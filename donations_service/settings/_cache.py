"""
CACHES
https://docs.djangoproject.com/en/5.0/topics/cache/
"""

from donations_service.settings._redis import REDIS_CONNECTION_STRING

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_CONNECTION_STRING,
    }
}
