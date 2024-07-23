# -*- coding: utf-8 -*-
from django.contrib.auth.backends import ModelBackend

from account.models import User


class UserBackend(ModelBackend):

    def authenticate(self, request, name=None, username=None, password=None):
        # print(request, name, username, password)
        try:
            _name = name or username
            # 优先匹配id
            user = User.objects.filter(id=_name)
            if user.exists():
                user = user.first()
                if user.check_password(password):
                    return user
            # 再匹配昵称
            user = User.objects.get(nickname=_name)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
            return user
        except User.DoesNotExist:
            return None
