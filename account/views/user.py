# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from account.conf import settings
from account.permissions import CurrentUserOrAdmin

User = get_user_model()


class UserViewSet(BaseUserViewSet):
    """
    直接继承djoser的UserViewSet，改动部分功能和添加特定功能
    """

    def permission_denied(self, request, **kwargs):
        # if (
        #     settings.HIDE_USERS
        #     and request.user.is_authenticated
        #     and self.action in ["update", "partial_update", "list", "retrieve"]
        # ):
        #     raise NotFound()
        super(BaseUserViewSet, self).permission_denied(request, **kwargs)

    def get_queryset(self):
        user = self.request.user
        queryset = super(BaseUserViewSet, self).get_queryset()
        # warnings.warn("此处同班级获取用户的功能未实现", Warning)
        if user.admin == 0:
            # 理论上会在list操作上加权限设置
            # 如果不是管理员，则只能获取自己的同学或者老师
            queryset = self.request.user.get_classmates() | self.request.user.get_teachers()
        return queryset

    def get_permissions(self):
        # if self.action == 'list':
        #     self.permission_classes = settings.
        # if self.action == 'me':
        #     self.permission_classes = [CurrentUserOrAdmin]
        if self.action == 'set':
            self.permission_classes = [CurrentUserOrAdmin]

        return super(BaseUserViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return settings.serializers.user_public_simple
        elif self.action == "me":
            return settings.serializers.user_all
        elif self.action == "retrieve":
            obj = self.get_object()
            if self.request.user.pk == obj.pk:
                return settings.serializers.user_all
            return settings.serializers.user_private
        elif self.action == "set":
            return settings.serializers.user_set
        raise NotImplementedError(f"Action {self.action} 未实现！")

    @action(detail=False, methods=["get"])
    def has_nickname(self, request, *args, **kwargs):
        nickname = request.query_params.get("nickname", None)
        if not nickname:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "未提供nickname"})
        has_nickname = User.objects.filter(nickname=nickname).exists()
        return Response(data={"has_nickname": has_nickname})

    @action(methods=["post"], detail=True)
    def set(self, request, *args, **kwargs):
        data = request.data
        nickname = data.pop("nickname", None)
        # get_object已经被覆写了
        obj = super(BaseUserViewSet, self).get_object()
        if obj.nickname != nickname:
            if User.objects.filter(nickname=nickname).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"nickname": ["昵称已被使用"]})
            data['nickname'] = nickname
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.update(
            instance=self.get_object(),
            validated_data=serializer.validated_data
        )
        return Response(data=serializer.data)
