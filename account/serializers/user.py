# -*- coding: utf-8 -*-
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers

from account.conf import settings
from account.models import RoleStudent, RoleTeacher
from destination.models import City, School

User = get_user_model()


# TODO: 重构序列化器
#  由于设计上不打算支持查看别的班级学生，所以区分序列化内容的Public和Private便没有必要
#  只需要区分Simple和All来应对list模式和retrieve模式


class RoleStudentPublicSerializer(serializers.ModelSerializer):
    """
    用户身份序列化器-学生-公开数据，此序列化器序列化公开的内容
    """

    class Meta:
        model = settings.models.user_role_student
        fields = settings.models.user_role_student.PUBLIC_FIELDS

    classes = settings.serializers.class_public_simple(many=True)


class RoleStudentPrivateSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.models.user_role_student
        fields = settings.models.user_role_student.PRIVATE_FIELDS

    school = serializers.CharField(source="school.name", default=None)


class RoleStudentAllSerializer(serializers.ModelSerializer):
    """
    用户身份序列化器-学生-公开数据，此序列化器序列化公开的内容
    """

    class Meta:
        model = settings.models.user_role_student
        fields = settings.models.user_role_student.ALL_FIELDS

    school = serializers.CharField(source="school.name", default=None)
    classes = settings.serializers.class_public_simple(many=True)


class RoleTeacherPublicSerializer(serializers.ModelSerializer):
    """
    用户身份序列化器-老师-公开数据，此序列化器序列化公开的内容
    """

    class Meta:
        model = settings.models.user_role_teacher
        fields = settings.models.user_role_teacher.PUBLIC_FIELDS

    classes = settings.serializers.class_public_simple(many=True)
    managed_classes = settings.serializers.class_public_simple(many=True)


class RoleTeacherAllSerializer(serializers.ModelSerializer):
    """
    用户身份序列化器-老师-公开数据，此序列化器序列化公开的内容
    """

    class Meta:
        model = settings.models.user_role_teacher
        fields = settings.models.user_role_teacher.ALL_FIELDS

    classes = settings.serializers.class_public_simple(many=True)
    managed_classes = settings.serializers.class_public_simple(many=True)


def _get_role(
        self,
        obj: settings.models.user_role,
        student_model: Any = RoleStudentPublicSerializer,
        teacher_model: Any = RoleTeacherPublicSerializer,
):
    """
    将Role作为字段时，使用SerializerMethodField的数据获取函数
    理论上有更优解，此处暂用该方案
    """
    # print(RoleStudentPublicSerializer(obj.role).data)
    # print(hasattr(obj, 'role'), RoleStudentPublicSerializer(obj.role).data)
    if not hasattr(obj, 'role_student') and not hasattr(obj, 'role_teacher'):
        return None
    if obj.role == settings.choices.user_role.STUDENT:
        role_data = student_model(obj.role_student, context=self.context).data
    elif obj.role == settings.choices.user_role.TEACHER:
        role_data = teacher_model(obj.role_teacher, context=self.context).data
    else:
        raise ValueError(f"{obj.role=} 数据异常！")
    # 将身份类型和其他信息结合到一起，保证输出一致
    role_data['role'] = obj.role
    return role_data


class RoleMixin(serializers.Serializer):
    role = serializers.SerializerMethodField()

    def get_role(self, obj):
        return _get_role(self, obj)


class UserPublicSerializer(serializers.ModelSerializer, RoleMixin):
    """
    用户描述序列化器，此序列化器序列化用户的公开数据
    """

    class Meta:
        model = User
        fields = User.PUBLIC_FIELDS


class UserPrivateSerializer(serializers.ModelSerializer, RoleMixin):
    class Meta:
        model = User
        fields = User.PRIVATE_FIELDS

    def get_role(self, obj):
        return _get_role(
            self,
            obj,
            RoleStudentPrivateSerializer,
            RoleTeacherPublicSerializer,
        )


class UserAllSerializer(serializers.ModelSerializer, RoleMixin):
    """
    用户序列化器，此序列化器序列化用户的全部字段（不包括敏感字段）
    """

    class Meta:
        model = User
        fields = User.ALL_FIELDS

    def get_role(self, obj):
        return _get_role(
            self,
            obj,
            RoleStudentAllSerializer,
            RoleTeacherAllSerializer,
        )


class UserStudentSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = User.EDITABLE_FIELDS + ["school", "campus", "city"]

    school = serializers.CharField(source="role_student.school", allow_null=True)
    campus = serializers.CharField(source="role_student.campus", allow_blank=True, allow_null=True)
    city = serializers.CharField(source="role_student.city", allow_null=True)

    def validate_school(self, value):
        if value is None:
            return None
        school = School.objects.filter(name=value)
        if not school.exists():
            raise serializers.ValidationError(f"学校{value}不存在")
        return school.first()

    def validate_city(self, value):
        if value is None:
            return None
        city = City.objects.filter(name=value)
        if not city.exists():
            raise serializers.ValidationError(f"城市{value}不存在")
        return city.first()

    def update(self, instance, validated_data):
        # 不能有多对多关系
        role_student = validated_data.pop("role_student", None)
        if role_student is not None:
            for attr, value in role_student.items():
                setattr(instance.role_student, attr, value)
            instance.role_student.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserTeacherSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = User.EDITABLE_FIELDS


class UserImagesSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["avatar", "photo"]


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta:
        model = User
        fields = User.REQUIRED_FIELDS + [
            User.USERNAME_FIELD, "password", "id"
        ]

    id = serializers.CharField(required=False, max_length=8)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserRoleStudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleStudent
        fields = ["user"]


class UserRoleTeacherCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleTeacher
        fields = ["user", "subject"]


# 由于djoser的用户密码重置策略是发送重置邮件，我只能手搓一个别的了
class PasswordResetSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, style={"input_type": "password"})
    new_password = serializers.CharField(required=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = getattr(self, "user", None) or self.context["request"].user
        # why assert? There are ValidationError / fail everywhere
        assert user is not None
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"old_password": ["原密码错误"]})

        try:
            validate_password(attrs["new_password"], user)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        return super().validate(attrs)
