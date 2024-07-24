# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from account.conf import settings
from account.models.user import UserRoleChoice
from account.permissions import AdminSuper, CurrentUserOrAdmin

User = get_user_model()


class UserViewSet(BaseUserViewSet):
    """
    直接继承djoser的UserViewSet，改动部分功能和添加特定功能
    """

    # 非常危险！！！！ 可能通过update修改方法！
    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

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
        if self.action in ["partial_update", "images", "me_images"]:
            self.permission_classes = [CurrentUserOrAdmin]
        elif self.action == ["role"]:
            self.permission_classes = [AdminSuper]

        return super(BaseUserViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return settings.serializers.user_public_simple
        elif self.action == "create":
            return settings.serializers.user_create
        elif self.action == "me":
            return settings.serializers.user_all
        elif self.action == "retrieve":
            obj = self.get_object()
            if self.request.user.pk == obj.pk:
                return settings.serializers.user_all
            return settings.serializers.user_private
        elif self.action == "partial_update":
            return settings.serializers.user_set
        elif self.action in ["images", "me_images"]:
            return settings.serializers.user_set_images
        elif self.action == "role":
            role = self.request.data.get("role")
            if role is None:
                raise ValidationError("`role` is required")
            elif role == UserRoleChoice.STUDENT:
                return settings.serializers.user_role_student_create
            elif role == UserRoleChoice.TEACHER:
                return settings.serializers.user_role_teacher_create
            else:
                raise ValidationError(f"{role=} 不在可选范围内")
        raise NotImplementedError(f"Action {self.action} 未实现！")

    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        # 覆写掉这个，因为下面这行太诡异了。猜测：每次访问都会重新创建view实例？
        # self.get_object = self.get_instance
        # return self.retrieve(request, *args, **kwargs)
        # 但是无妨，因为这个本来就要特别对待，在使用retrieve获取数据的时候不会带上中间件
        user = request.user
        data = self.get_serializer(user).data
        if data.get('role'):
            for i, v in enumerate(data["role"]["classes"]):
                if user.role == settings.choices.user_role.STUDENT:
                    data["role"]["classes"][i].update(settings.serializers.class_student_simple(
                        settings.models.class_student.objects.get(user_role__pk=user.role_student.pk,
                                                                  classes__pk=v["id"]),
                        context=self.get_serializer_context()
                    ).data)
                elif user.role == settings.choices.user_role.TEACHER:
                    data["role"]["classes"][i].update(settings.serializers.class_teacher_simple(
                        settings.models.class_teacher.objects.get(user_role__pk=user.role_teacher.pk,
                                                                  classes__pk=v["id"]),
                        context=self.get_serializer_context()
                    ).data)

        return Response(data=data)

    @action(detail=False, methods=["get"])
    def has_nickname(self, request, *args, **kwargs):
        nickname = request.query_params.get("nickname", None)
        if not nickname:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "未提供nickname"})
        has_nickname = User.objects.filter(nickname=nickname).exists()
        return Response(data={"has_nickname": has_nickname})

    # @action(detail=True, methods=["post"])
    def partial_update(self, request, *args, **kwargs):
        data = request.data.copy()
        nickname = data.pop("nickname", None)
        obj = self.get_object()
        if nickname is not None and obj.nickname != nickname:
            if User.objects.filter(nickname=nickname).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"nickname": ["昵称已被使用"]})
            data['nickname'] = nickname
        serializer = self.get_serializer(instance=self.get_object(), data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data)

    def _set_images(self, request, detail):
        if detail:
            instance = self.get_object()
        else:
            instance = request.user
        serializer = self.get_serializer(instance=instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data)

    @action(detail=False, methods=["patch"], url_path="me/images")
    def me_images(self, request, *args, **kwargs):
        # 这个要在下面那个之前，不然匹配不到
        return self._set_images(request, False)

    @action(detail=True, methods=["patch"])
    def images(self, request, *args, **kwargs):
        return self._set_images(request, True)

    @action(detail=True, methods=["post"])
    def role(self, request, *args, **kwargs):
        data = request.data.copy()
        role = data.pop("role")
        obj = self.get_object()
        data["user"] = obj.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        obj.role = role[0]
        # print(role)
        obj.save()
        serializer.save()
        return Response(data=serializer.data)
