# -*- coding: utf-8 -*-
"""
说明：该模块是为了解决循环引用问题构建的
该模块包括不需要使用到班级序列化的用户数据序列化器。
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserPublicSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = User.PUBLIC_SIMPLE_FIELDS


class UserPrivateSimpleSerializer(serializers.ModelSerializer):
    """
    是老师的时候科目一项需要给出
    """

    class Meta:
        model = User
        fields = User.PRIVATE_SIMPLE_FIELDS + ['subject']

    subject = serializers.CharField(source='role_teacher.subject')

    def __init__(self, *args, **kwargs):
        is_teacher = kwargs.pop('is_teacher', False)
        super(UserPrivateSimpleSerializer, self).__init__(*args, **kwargs)
        if not is_teacher:
            self.fields.pop("subject")
