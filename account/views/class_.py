# -*- coding: utf-8 -*-
import warnings

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_nested.viewsets import NestedViewSetMixin
from django.conf import settings as django_settings
from django.core.cache import cache

from account.models.class_ import Class, ClassOfficer, ClassStudent, ClassTeacher
from account.models.choices import ClassTypeChoice, UserRoleChoice
from account.permissions import AdminSuper, CurrentMemberOrAdmin, IsMapActive, ManageCurrentClassOrAdmin, \
    OnCurrentClassOrAdmin, OnSameClassWithClassMembershipOrAdmin
from account.serializers.class_ import ClassCreateSerializer, ClassPhotoSetSerializer, \
    ClassSerializer, ClassSetSerializer, ClassSimpleSerializer, ClassStudentAddSerializer, ClassTeacherAddSerializer
from account.serializers.class_user_through import ClassOfficerTypeSerializer, ClassStudentSerializer, \
    ClassStudentSetSerializer, ClassTeacherSerializer, ClassTeacherSetSerializer


class ClassViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    # mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = ClassSimpleSerializer
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
        if self.action in ["photo", "partial_update", "update"]:
            self.permission_classes = [ManageCurrentClassOrAdmin]
        elif self.action in ["create", "members"]:
            self.permission_classes = [AdminSuper]
        elif self.action == "map":
            self.permission_classes = [IsMapActive]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return ClassSimpleSerializer
        elif self.action == "create":
            return ClassCreateSerializer
        elif self.action == "retrieve":
            return ClassSerializer
        elif self.action == "photo":
            return ClassPhotoSetSerializer
        elif self.action in ["partial_update", "update"]:
            return ClassSetSerializer
        elif self.action == "members":
            role = self.request.data.get("role")
            if not role:
                raise ValidationError("`role` is required")
            elif role == UserRoleChoice.STUDENT:
                return ClassStudentAddSerializer
            elif role == UserRoleChoice.TEACHER:
                return ClassTeacherAddSerializer
            else:
                raise ValidationError(f"{role=} 不在可选范围内")
        raise NotImplementedError(f"Action {self.action} 未实现！")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # 告诉前端用户是否可以编辑该班级信息
        data = serializer.data
        data["can_edit"] = ManageCurrentClassOrAdmin().has_object_permission(request, self, instance)
        return Response(data)

    def update(self, request, *args, **kwargs):
        if kwargs.get("partial", False) or request.query_params.get("partial", "false").lower() == "true":
            # 因为默认的partial_update方法是调用update方法实现的
            kwargs["partial"] = True
            return super().update(request, *args, **kwargs)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=["get"])
    def officer_type_list(self, request, *args, **kwargs):
        class_type = request.query_params.get("type")
        if not class_type:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"errors": ["必须提供type"]})
        if class_type == ClassTypeChoice.ADMINISTRATIVE:
            objects = ClassOfficer.objects.filter(administrative=True)
        elif class_type == ClassTypeChoice.WALKING:
            objects = ClassOfficer.objects.filter(walking=True)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"errors": [f"Type {class_type} 不在可选范围内"]})
        return Response(data=ClassOfficerTypeSerializer(objects, many=True).data)

    @action(detail=True, methods=["put"])
    def photo(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.get_object()
        instance.photo = serializer.validated_data["photo"]
        instance.save()
        return Response(data={"photo": request.build_absolute_uri(instance.photo.url)})

    @action(detail=True, methods=["patch", "put"])
    def members(self, request, *args, **kwargs):
        if request.method.upper() == "PUT" and not request.query_params.get("partial", "false").lower() == "true":
            # 由于uni-app没有patch方法，所以使用partial=True通过put方法实现patch
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        data = request.data.copy()
        role = data.pop("role")
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        obj = self.get_object()
        if role == UserRoleChoice.STUDENT:
            obj.students.add(*serializer.validated_data["students"])
        elif role == UserRoleChoice.TEACHER:
            obj.teachers.add(*serializer.validated_data["teachers"])
        obj.save()
        return Response(data={"teacher_count": obj.teachers.count(), "student_count": obj.students.count()})

    @action(detail=True, methods=["get"])
    def map(self, request, *args, **kwargs):
        class_obj = self.get_object()
        """这里考虑到一个问题：如果另一个用户访问时正在创建文件，缓存状态为generating，此时我再次创建
        可能导致：1. 文件被占用报错 2. 资源使用过多 3. 缓存状态卡在generating"""
        if not class_obj.map or not cache.get(class_obj.map_cache_key) == 'generated':
            class_obj.create_map_file()
        else:
            fp = django_settings.MEDIA_ROOT / class_obj.map.name
            if not fp.exists():
                class_obj.create_map_file()
        return Response(data={
            "map": request.build_absolute_uri(class_obj.map.url),
        })


class ClassStudentViewSet(NestedViewSetMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          viewsets.GenericViewSet):
    parent_lookup_kwargs = {"class_id": "classes__id"}
    lookup_field = 'user_role__user__id'
    queryset = ClassStudent.objects.all()
    permission_classes = [OnCurrentClassOrAdmin]

    def get_serializer_class(self):
        if self.action == "list":
            return ClassStudentSerializer
        elif self.action == "retrieve":
            return ClassStudentSerializer
        elif self.action in ["update", "partial_update"]:
            return ClassStudentSetSerializer

        raise NotImplementedError(f"{self.action=} 未实现")

    def get_permissions(self):
        if self.action == "retrieve":
            self.permission_classes = [OnCurrentClassOrAdmin, OnSameClassWithClassMembershipOrAdmin]
        elif self.action in ["update", "partial_update"]:
            self.permission_classes = [CurrentMemberOrAdmin]

        return super().get_permissions()

    def update(self, request, *args, **kwargs):
        if request.query_params.get("partial", "false").lower() == "true":
            kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class ClassTeacherViewSet(NestedViewSetMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          viewsets.GenericViewSet):
    parent_lookup_kwargs = {"class_id": "classes__id"}
    lookup_field = 'user_role__user__id'
    queryset = ClassTeacher.objects.all()
    permission_classes = [OnCurrentClassOrAdmin]

    def get_serializer_class(self):
        if self.action == "list":
            return ClassTeacherSerializer
        elif self.action == "retrieve":
            return ClassTeacherSerializer
        elif self.action in ["update", "partial_update"]:
            return ClassTeacherSetSerializer

        raise NotImplementedError(f"{self.action=} 未实现")

    def get_permissions(self):
        if self.action == "retrieve":
            self.permission_classes = [OnCurrentClassOrAdmin, OnSameClassWithClassMembershipOrAdmin]
        elif self.action in ["update", "partial_update"]:
            self.permission_classes = [CurrentMemberOrAdmin]

        return super().get_permissions()

    def update(self, request, *args, **kwargs):
        if request.query_params.get("partial", "false").lower() == "true":
            kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
