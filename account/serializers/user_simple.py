# -*- coding: utf-8 -*-
"""
说明：该模块是为了解决循环引用问题构建的
该模块包括不需要使用到班级序列化的用户数据序列化器。
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = User.SIMPLE_FIELDS + [
            "school", "campus", "city",
            "subject"
        ]

    subject = serializers.CharField(source='role_teacher.subject', default=None)

    school = serializers.CharField(source='role_student.school.name', default=None)
    campus = serializers.CharField(source='role_student.campus', default=None)
    city = serializers.CharField(source='role_student.city.name', default=None)

    def __init__(self, *args, **kwargs):
        is_teacher = kwargs.pop('is_teacher', False)
        show_destination = kwargs.pop('show_destination', False)
        super().__init__(*args, **kwargs)
        if not show_destination or is_teacher:
            self.fields.pop('school')
            self.fields.pop('campus')
            self.fields.pop('city')

        if not is_teacher:
            self.fields.pop("subject")


class UserSimpleCompatibleSerializer(UserSimpleSerializer):
    def __init__(self, *args, **kwargs):
        super(UserSimpleSerializer, self).__init__(*args, **kwargs)
        self.fields.pop('school')
        self.fields.pop('campus')
        self.fields.pop('city')
