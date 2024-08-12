# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from rest_framework import serializers

from account.models import RoleStudent

User = get_user_model()


class UserMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleStudent
        fields = [
            "id", "name",
            "school", "campus",
            # "phone", "email", "QQ", "WeChat"
        ]

    id = serializers.CharField(source="user.id")
    name = serializers.CharField(source="user.name")
    school = serializers.CharField(source='school.name', default=None)
