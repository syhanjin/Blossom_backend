# -*- coding: utf-8 -*-
from django.conf import settings as django_settings

from conf import create_lazy_settings

default_settings = {
    "KEY": "a2be9334d27020adf8e8f6962be84102",
    "CLASS_MAPJSON_ROOT": django_settings.MEDIA_ROOT / "class_map"
}

settings = create_lazy_settings(default_settings, "destination")
