"""
CACHES
https://docs.djangoproject.com/en/5.0/topics/cache/
"""

from envparse import env

REDIS_HOST = env.str('REDIS_HOST')
REDIS_PORT = env.int('REDIS_PORT', default=0)
REDIS_USER = env.str('REDIS_USER', default='')
REDIS_PASSWORD = env.str('REDIS_PASSWORD', default='')
REDIS_DB = env.int('REDIS_DB', default=0)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}",
    }
}
