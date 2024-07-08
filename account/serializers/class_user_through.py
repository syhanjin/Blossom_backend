# -*- coding: utf-8 -*-
from rest_framework import serializers

from account.conf import settings


class ClassStudentSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.models.class_student
        fields = settings.models.class_student.SIMPLE_FIELDS


class ClassTeacherSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.models.class_teacher
        fields = settings.models.class_teacher.SIMPLE_FIELDS


class ClassOfficerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.models.class_officer
        fields = ["name", "order"]
