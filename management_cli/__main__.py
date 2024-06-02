import logging
import json
import argparse

from dotenv import load_dotenv
from envparse import env

from web3 import Web3

load_dotenv()

logging.basicConfig(format="[%(asctime)s] %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel("INFO")

CONTRACT_URL = env.str('CONTRACT_URL')
CONTRACT_ADDRESS = env.str('CONTRACT_ADDRESS')
EXCHANGER_CONTRACT_PATH = env.str('EXCHANGER_CONTRACT_PATH')
TOKEN_CONTRACT_PATH = env.str('TOKEN_CONTRACT_PATH')


def _establish_connection() -> Web3:
    w3 = Web3(Web3.HTTPProvider(CONTRACT_URL))

    if w3.is_connected():
        logger.info("Web3 connected")
    else:
        raise ValueError('no connection established')

    return w3


def _load_contract(w3, path: str, contract_address: str):
    with open(path, 'r') as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']

    contract = w3.eth.contract(
        abi=contract_abi,
        address=contract_address,
    )

    if not list(contract.functions):
        raise ValueError('Contract has no functions!')

    return contract


def _send_signed_contract_transaction(w3, contract_method, private_key):
    address = w3.eth.account.from_key(private_key).address
    address = w3.to_checksum_address(address)
    nonce = w3.eth.get_transaction_count(address)

    transaction = contract_method.build_transaction(
        {'nonce': nonce, 'from': address})
    signed_transaction = w3.eth.account.sign_transaction(
        transaction, private_key=private_key)

    return w3.eth.send_raw_transaction(signed_transaction.rawTransaction)


def register_member(w3, token_contract, moderator_private_key,  # internals
                    account_address):
    """ DonationToken.registerMember (from owner) """
    _send_signed_contract_transaction(
        w3,
        token_contract.functions.registerMember(account_address),
        moderator_private_key,
    )


def disable_member(w3, token_contract, moderator_private_key,  # internals
                   account_address):
    """ DonationToken.disableMember (from owner) """
    _send_signed_contract_transaction(
        w3,
        token_contract.functions.disableMember(account_address),
        moderator_private_key,
    )


def register_donate_need(w3, token_contract,  # internals
                         account_private_key, need_name, total):
    """ DonationToken.registerDonateNeeds (from member) """
    _send_signed_contract_transaction(
        w3,
        token_contract.functions.registerDonateNeeds(need_name, total),
        account_private_key,
    )


def delete_donate_need(w3, token_contract,  # internals
                       account_private_key, need_name):
    """ DonationToken.deleteDonateNeeds (from member) """
    _send_signed_contract_transaction(
        w3,
        token_contract.functions.deleteDonateNeeds(need_name),
        account_private_key,
    )


def transfer(w3, token_contract,  # internals
             account_private_key, receiver_address, value):
    """ DonationToken.transfer (from any) """
    _send_signed_contract_transaction(
        w3,
        token_contract.functions.transfer(receiver_address, value),
        account_private_key,
    )


def donate(w3, token_contract,  # internals
           account_private_key, value):
    """ DonationToken.donate (from any) """
    _send_signed_contract_transaction(
        w3,
        token_contract.functions.donate(value),
        account_private_key,
    )


def donate_all(w3, token_contract,  # internals
               account_private_key, value):
    """ DonationToken.donateAll (from any) """
    _send_signed_contract_transaction(
        w3,
        token_contract.functions.donateAll(value),
        account_private_key,
    )


def buy(w3, contract_address,  # internals
        sender_address, sender_private_key, value):
    """ DonationExchanger.receive (from any) """
    w3.eth.send_transaction({
        'from': sender_address,
        'to': contract_address,
        'value': w3.to_wei(value, 'gwei'),
    })


_actions_mapping = {
    'register_member': register_member,
    'disable_member': disable_member,
    'register_donate_need': register_donate_need,
    'delete_donate_need': delete_donate_need,
    'transfer': transfer,
    'donate': donate,
    'donate_all': donate_all,
    'buy': buy,
}


arg_parser = argparse.ArgumentParser(
    description="Donation Tokens CLI",
    formatter_class=argparse.RawTextHelpFormatter,
)

arg_parser.add_argument(
    "action",
    help=(
        "Specifies action of module\n"
        "Options: {_actions_mapping.keys()}"
    )
)
arg_parser.add_argument(
    "-f",
    "--accounts-file",
    dest="file",
    default='local.json',
    help=(
        "Specifies accounts file\nType: str\n"
        "Default: local.json"
    ),
)
arg_parser.add_argument(
    "-s",
    "--sender",
    dest="sender",
    default=0,
    type=int,
    help=(
        "Specifies sender index of operation\nType: int\n"
        "Default: 0"
    )
)
arg_parser.add_argument(
    "-r",
    "--receiver",
    dest="receiver",
    default=None,
    type=int,
    help=(
        "Specifies receiver index of operation\nType: int\n"
        "Default: None"
    )
)
arg_parser.add_argument(
    "-v",
    "--value",
    default=None,
    help=(
        "Specifies value for operation\n"
        "Default: None"
    )
)


def _get_required_receiver(args):
    if not (receiver := args.receiver):
        raise ValueError('Select receiver in args!')
    return receiver


def _get_required_value(args):
    if not (value := args.value):
        raise ValueError('Select value in args!')
    return value


def main():
    args = arg_parser.parse_args()

    with open(args.file, 'r') as file:
        accounts_mapping = json.load(file)['private_keys']
        private_keys = list(accounts_mapping.values())

    w3 = _establish_connection()

    exchanger_contract = _load_contract(w3, EXCHANGER_CONTRACT_PATH, CONTRACT_ADDRESS)
    token_address = exchanger_contract.functions.token().call()

    token_contract = _load_contract(w3, TOKEN_CONTRACT_PATH, token_address)

    addresses = w3.eth.accounts
    print(
        'Initial balance: ', token_contract.functions.balanceOf(
            addresses[args.sender]).call()
    )

    match args.action:
        case "register_member" | "disable_member":
            if (sender := args.sender) != 0:
                raise ValueError('Incorrect sender for operation!')

            receiver = _get_required_receiver(args)

            private_key = private_keys[sender]
            address = addresses[receiver]

            _actions_mapping[args.action](w3, token_contract, private_key, address)
        case "register_donate_need":
            values = args.value.split(',')

            if not len(values) == 2:
                raise ValueError('Should be 2 args in values, use "," as separator')

            private_key = private_keys[args.sender]
            register_donate_need(w3, token_contract, private_key, values[0], int(values[1]))
        case "delete_donate_need":
            value = _get_required_value(args)

            private_key = private_keys[args.sender]
            delete_donate_need(w3, token_contract, private_key, value)
        case "transfer":
            receiver = _get_required_receiver(args)
            value = _get_required_value(args)

            private_key = private_keys[args.sender]
            address = addresses[receiver]
            transfer(w3, token_contract, private_key, address, w3.to_wei(int(value), 'gwei'))
        case "donate" | "donate_all":
            value = _get_required_value(args)

            private_key = private_keys[args.sender]
            _actions_mapping[args.action](w3, token_contract, private_key, w3.to_wei(int(value), 'gwei'))
        case "buy":
            value = _get_required_value(args)
            sender_address = addresses[args.sender]
            sender_private_key = private_keys[args.sender]
            buy(w3, exchanger_contract.address, sender_address, sender_private_key, value)
        case _:
            raise ValueError('action')

    print(
        'Result balance: ', token_contract.functions.balanceOf(
            addresses[args.sender]).call()
    )


if __name__ == '__main__':
    main()
