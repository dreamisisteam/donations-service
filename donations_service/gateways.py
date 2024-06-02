import json
from typing import Literal

from web3.types import ENS

from web3 import Web3
from web3.eth import Contract

from django.conf import settings
from django.core.cache import cache

w3 = Web3(Web3.HTTPProvider(settings.CONTRACT_URL))

NeedsInfoKeys = Literal['name', 'total']
NeedsInfoType = dict[NeedsInfoKeys, int]  # {"name": "guitar", "total": 100}
ListNeedsInfoType = list[NeedsInfoType]

if not w3.is_connected():
    raise ValueError('No connection established!')


def prepare_address(func):
    """ Decorator to make address ChecksumAddress """

    def _transform_address_arg(*args, **kwargs):
        address = kwargs.pop('address', None)

        if not address:
            args = list(args)
            address = args.pop(1)

        address = Web3.to_checksum_address(address)
        kwargs['address'] = address

        return func(*args, **kwargs)

    return _transform_address_arg


class DonationContractsGateway:
    """ Gateway to access Donation Blockchain """
    exchanger: Contract
    token: Contract

    owner: str

    def __init__(self):
        self.exchanger = _load_contract(settings.EXCHANGER_CONTRACT_PATH, settings.CONTRACT_ADDRESS)

        self.owner = self.exchanger.functions.owner().call().lower()

        token_address = self.exchanger.functions.token().call()
        self.token = _load_contract(settings.TOKEN_CONTRACT_PATH, token_address)

    @property
    def members(self) -> list[str]:
        """ Returns all donation program members """
        if cached_members := cache.get('donation_members'):
            return cached_members

        members_registry = [
            address.lower()
            for address in self.token.functions.getMembersRegistry().call()
        ]

        cache.set('donation_members', members_registry, settings.CONTRACT_VIEWS_DATA_CACHE)
        return members_registry

    def _get_member_needs_names(self, address: str) -> list[str]:
        """
        Returns all names of donation program members needs

        :param address: address of needy
        :return: list of needs
        """
        return self.token.functions.donateNeedsNames(address).call()

    def _get_member_need_total(self, address: str, name: str) -> int:
        """
        Returns total sum of donation need of member

        :param address: address of needy
        :param name: need name
        :return: total sum of need
        """
        need_total_in_wei = self.token.functions.donateNeed(address, name).call()
        return need_total_in_wei

    def _get_member_charges_balance(self, address: str) -> int:
        """
        Returns all charges balance of donation program member

        :param address: address of needy
        :return: charges balance
        """
        charges_total_in_wei = self.token.functions.donateBalance(address).call()
        return charges_total_in_wei // 1000000000

    @prepare_address
    def get_member_needs_state(self, address: str) -> tuple[ListNeedsInfoType, int]:
        """
        Returns member needs state

        :param address: address of member
        :return: [{"name": "guitar", "total": 100}, {"name": "course", "total": 30], 100
        """
        member_need_array: ListNeedsInfoType = []

        # get needs costs
        for need_name in self._get_member_needs_names(address):
            member_need_array.append({
                'name': need_name,
                'total': self._get_member_need_total(address, need_name),
            })

        # get collected balance
        charges = self._get_member_charges_balance(address)

        return member_need_array, charges


def _load_contract(path: str, contract_address: ENS):
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


contracts_gateway = DonationContractsGateway()
