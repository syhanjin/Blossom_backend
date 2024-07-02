# -*- coding: utf-8 -*-

from .prod import *

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = "django-insecure-@431=vl-czdyz-4a6)q8k&4oikpds^9x&#to%1&0&t-g_m0l5*"

DEBUG = True

ALLOWED_HOSTS = [
    '192.168.0.104',
    '192.168.100.4',
    '127.0.0.1'
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'blossom',
        'USER': 'blossom',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '3306'
    }
}

# 以下内容用于解决跨域问题，正式部署不需要
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = "*"
# ====================================

# EMAIL_HOST_PASSWORD = "QKQRJDXNOKBQDYBA"
#
# APP_ID = 'kNs4SARVsB97qGaYrWW6U5'
# APP_KEY = '7SbUiedeug5a3Rmi7NeKe2'
# APP_SECRET = 'WkdQz8VcQG64EGkBx0XR36'
# MASTER_SECRET = '16UBUvXYyd9smExhM6Yis4'
