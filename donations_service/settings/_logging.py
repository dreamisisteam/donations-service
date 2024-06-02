import logging

from envparse import env


DEBUG = env.bool('DEBUG', default=False)
LOG_LEVEL = 'DEBUG' if DEBUG else 'INFO'

logging.basicConfig(level=LOG_LEVEL)
