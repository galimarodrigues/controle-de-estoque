from .settings import *


# O manifesto do WhiteNoise e gerado somente no deploy. Nos testes, os
# templates devem referenciar os estaticos sem exigir collectstatic.
del STATICFILES_STORAGE
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE
    if middleware != 'whitenoise.middleware.WhiteNoiseMiddleware'
]
