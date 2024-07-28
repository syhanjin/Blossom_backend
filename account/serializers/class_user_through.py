# -*- coding: utf-8 -*-
from rest_framework import serializers

from account.conf import settings
from account.models.class_ import ClassOfficer


class ClassStudentSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.models.class_student
        fields = settings.models.class_student.SIMPLE_FIELDS


class ClassStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.models.class_student
        fields = settings.models.class_student.ALL_FIELDS + [
            "id", "name"
        ]

    id = serializers.CharField(source="user_role.user.id")
    name = serializers.CharField(source="user_role.user.name")


class ClassStudentSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.models.class_student
        fields = settings.models.class_student.EDITABLE_FIELDS

    position = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ClassOfficer.objects.all(),
        allow_empty=True
    )


class ClassTeacherSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.models.class_teacher
        fields = settings.models.class_teacher.SIMPLE_FIELDS


class ClassTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.models.class_teacher
        fields = settings.models.class_teacher.ALL_FIELDS + [
            "id", "name", "subject"
        ]

    id = serializers.CharField(source="user_role.user.id")
    name = serializers.CharField(source="user_role.user.name")
    subject = serializers.CharField(source="user_role.subject")


class ClassOfficerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.models.class_officer
        fields = ["name", "order"]
