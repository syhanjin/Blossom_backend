# -*- coding: utf-8 -*-
"""
从djoser里面扒拉出来的

"""
from django.conf import settings as django_settings
from django.core.signals import setting_changed
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string


class ObjDict(dict):
    def __getattribute__(self, item):
        try:
            val = self[item]
            if isinstance(val, str):
                val = import_string(val)
            elif isinstance(val, (list, tuple)):
                val = [import_string(v) if isinstance(v, str) else v for v in val]
            self[item] = val
        except KeyError:
            val = super(ObjDict, self).__getattribute__(item)

        return val


def create_lazy_settings(DEFAULT_SETTINGS, SETTINGS_NAMESPACE, SETTINGS_TO_IMPORT=[]):
    class Settings:
        def __init__(self, default_settings, explicit_overriden_settings: dict = None):
            if explicit_overriden_settings is None:
                explicit_overriden_settings = {}

            overriden_settings = (
                    getattr(django_settings, SETTINGS_NAMESPACE, {})
                    or explicit_overriden_settings
            )

            self._load_default_settings()
            self._override_settings(overriden_settings)
            self._init_settings_to_import()

        def _load_default_settings(self):
            for setting_name, setting_value in DEFAULT_SETTINGS.items():
                # if setting_name.isupper():
                setattr(self, setting_name, setting_value)

        def _override_settings(self, overriden_settings: dict):
            for setting_name, setting_value in overriden_settings.items():
                value = setting_value
                if isinstance(setting_value, dict):
                    value = getattr(self, setting_name, {})
                    value.update(ObjDict(setting_value))
                setattr(self, setting_name, value)

        def _init_settings_to_import(self):
            for setting_name in SETTINGS_TO_IMPORT:
                value = getattr(self, setting_name)
                if isinstance(value, str):
                    setattr(self, setting_name, import_string(value))

    class LazySettings(LazyObject):
        def _setup(self, explicit_overriden_settings=None):
            self._wrapped = Settings(DEFAULT_SETTINGS, explicit_overriden_settings)

    settings = LazySettings()

    def reload_settings(*args, **kwargs):
        setting, value = kwargs["setting"], kwargs["value"]
        if setting == SETTINGS_NAMESPACE:
            settings._setup(explicit_overriden_settings=value)

    setting_changed.connect(reload_settings)
    return settings


"""

from django.core.signals import setting_changed
from conf import LazySettings, ObjDict

SETTINGS_NAMESPACE = ""

DEFAULT_SETTINGS = {}

settings = LazySettings(DEFAULT_SETTINGS, SETTINGS_NAMESPACE, [])


def reload_settings(*args, **kwargs):
    global settings
    setting, value = kwargs["setting"], kwargs["value"]
    if setting == SETTINGS_NAMESPACE:
        settings._setup(explicit_overriden_settings=value)


setting_changed.connect(reload_settings)
"""
