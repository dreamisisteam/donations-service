"""
DATABASES
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
"""

from envparse import env

DB_HOST = env.str('DB_HOST')
DB_PORT = env.int('DB_PORT', default=5672)
POSTGRES_DB = env.str('POSTGRES_DB')
POSTGRES_USER = env.str('POSTGRES_USER')
POSTGRES_PASSWORD = env.str('POSTGRES_PASSWORD')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': POSTGRES_DB,
        'USER': POSTGRES_USER,
        'PASSWORD': POSTGRES_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}

DB_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}'
