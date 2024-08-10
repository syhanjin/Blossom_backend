# -*- coding: utf-8 -*-
from rest_framework import serializers

from apps.models import App, AppVersion


class AppCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = App
        fields = ('name', 'verbose_name', 'description', 'id')
        read_only_fields = ('id',)


class AppVersionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = AppVersion.REQUIRED_FIELDS + ['app_id']

    app_id = serializers.UUIDField()
    installer = serializers.FileField()

    def validate(self, attrs):
        if not App.objects.filter(id=attrs["app_id"]).exists():
            raise serializers.ValidationError("app不存在")
        app = App.objects.get(id=attrs["app_id"])
        if app.versions.filter(version_name=attrs['version_name']).exists():
            raise serializers.ValidationError("版本名已存在")
        if app.versions.filter(version_code=attrs['version_code']).exists():
            raise serializers.ValidationError("版本号已存在")
        return attrs


class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = '__all__'

    # apk = serializers.FileField(source="installer")


class AppSerializer(serializers.ModelSerializer):
    versions = AppVersionSerializer(many=True)

    class Meta:
        model = App
        fields = '__all__'
