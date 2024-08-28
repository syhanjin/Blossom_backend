# -*- coding: utf-8 -*-
from rest_framework import serializers

from account.models.class_ import ClassOfficer, ClassStudent, ClassTeacher


class ClassStudentSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassStudent
        fields = ClassStudent.SIMPLE_FIELDS


class ClassStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassStudent
        fields = ClassStudent.ALL_FIELDS + [
            "id", "name"
        ]

    id = serializers.CharField(source="user_role.user.id")
    name = serializers.CharField(source="user_role.user.name")


class ClassStudentSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassStudent
        fields = ClassStudent.EDITABLE_FIELDS

    position = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ClassOfficer.objects.all(),
        allow_empty=True
    )


class ClassTeacherSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassTeacher
        fields = ClassTeacher.SIMPLE_FIELDS


class ClassTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassTeacher
        fields = ClassTeacher.ALL_FIELDS + [
            "id", "name", "subject"
        ]

    id = serializers.CharField(source="user_role.user.id")
    name = serializers.CharField(source="user_role.user.name")
    subject = serializers.CharField(source="user_role.subject")


class ClassTeacherSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassTeacher
        fields = ClassTeacher.EDITABLE_FIELDS


class ClassOfficerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassOfficer
        fields = ["name", "order"]
