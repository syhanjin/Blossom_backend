# -*- coding: utf-8 -*-
from rest_framework import serializers

from destination.models import City, School


class SchoolSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ["name", "city", "id"]


class CitySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["name", "adcode"]
