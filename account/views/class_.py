# -*- coding: utf-8 -*-
import warnings

from rest_framework import viewsets
from rest_framework.response import Response

from account.conf import settings
from account.models.class_ import Class
from account.permissions import OnCurrentClassOrAdmin
from account.serializers.class_ import ClassPublicSimpleSerializer


class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = ClassPublicSimpleSerializer
    queryset = Class.objects.all()
    permission_classes = [OnCurrentClassOrAdmin]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.admin == 0:
            # 如果不是管理员，则只能获取自己所在的班级
            warnings.warn("暂时禁止列出自己不在的班级", Warning)
            queryset = user.classes
        return queryset

    def get_permissions(self):
        # if self.action == 'list':
        #     self.permission_classes = settings.
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return settings.serializers.class_public_simple
        elif self.action == "retrieve":
            return settings.serializers.class_all
        raise NotImplementedError(f"Action {self.action} 未实现！")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
