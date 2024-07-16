# -*- coding: utf-8 -*-
import warnings

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from account.conf import settings
from account.models.class_ import Class
from account.permissions import ManageCurrentClassOrAdmin, OnCurrentClassOrAdmin
from account.serializers.class_ import ClassPublicSimpleSerializer


class ClassViewSet(
    # mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    # mixins.UpdateModelMixin,
    # mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
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
            queryset = user.classes.all() | user.edited_classes.all()
        return queryset

    def get_permissions(self):
        # if self.action == 'list':
        #     self.permission_classes = settings.
        if self.action.startswith("set"):
            self.permission_classes = [ManageCurrentClassOrAdmin]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return settings.serializers.class_public_simple
        elif self.action == "retrieve":
            return settings.serializers.class_all
        elif self.action == "set_photo":
            return settings.serializers.class_set_photo
        raise NotImplementedError(f"Action {self.action} 未实现！")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def officer_type_list(self, request, *args, **kwargs):
        class_type = request.query_params.get("type")
        if not class_type:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"errors": ["必须提供type"]})
        if class_type == settings.choices.class_type.ADMINISTRATIVE:
            objects = settings.models.class_officer.objects.filter(administrative=True)
        elif class_type == settings.choices.class_type.WALKING:
            objects = settings.models.class_officer.objects.filter(walking=True)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"errors": [f"Type {class_type} 不在可选范围内"]})
        return Response(data=settings.serializers.class_officer(objects, many=True).data)

    @action(detail=True, methods=["post"])
    def set_photo(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.photo = serializer.validated_data["photo"]
        instance.save()

        return Response(data={"photo": request.build_absolute_uri(instance.photo.url)})
