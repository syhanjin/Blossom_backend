# -*- coding: utf-8 -*-
"""
序列化器说明（重置版）
* 取消公开和私有的区分，所有有访问权限的用户均能看到你的联系方式，但是去向需要处理，限制为毕业班可以看（map_activated=True）
共有三类用户序列化器
 - 简单序列化，用于list操作时使用
  - 学生
  - 老师
  - 混合 同时包括学生和老师的字段，用于UserViewSet的list
 - 对外序列化，用于其他用户retrieve
  - 学生 （注意，需要依据毕业班关系决定是否包括去向信息）
  - 老师
 - 自身序列化，用于me
"""

from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers

from account.models import RoleStudent, RoleTeacher
from account.models.choices import UserRoleChoice
from account.serializers.class_ import ClassSimpleSerializer
from destination.models import City, School

User = get_user_model()


# TODO: 重构序列化器
#  由于设计上不打算支持查看别的班级学生，所以区分序列化内容的Public和Private便没有必要
#  只需要区分Simple和All来应对list模式和retrieve模式

# --- BEGIN 序列化器重构 ---

# Role信息序列化
class RoleStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleStudent
        fields = [
            "classes",
            "city", "school", "campus"
        ]

    classes = ClassSimpleSerializer(many=True)
    school = serializers.CharField(source="school.name", default=None)

    def __init__(self, *args, **kwargs):
        show_destination = kwargs.pop('show_destination', False)
        super().__init__(*args, **kwargs)
        if not show_destination:
            self.fields.pop('school')
            self.fields.pop('campus')
            self.fields.pop('city')


class RoleTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleTeacher
        fields = [
            "classes", "managed_classes",
            "subject"
        ]

    classes = ClassSimpleSerializer(many=True)
    managed_classes = ClassSimpleSerializer(many=True)


# 没文化，重构版的就用Current后缀表示是当前用户
class RoleStudentCurrentSerializer(RoleStudentSerializer):
    def __init__(self, *args, **kwargs):
        super(RoleStudentSerializer, self).__init__(*args, **kwargs)


class RoleTeacherCurrentSerializer(RoleTeacherSerializer):
    pass


# 用户信息序列化
def _get_role(self, obj: User,
              student_model: Type[serializers.ModelSerializer],
              teacher_model: Type[serializers.ModelSerializer]):
    """
    将Role作为字段时，使用SerializerMethodField的数据获取函数
    理论上有更优解，此处暂用该方案
    """
    # print(RoleStudentPublicSerializer(obj.role).data)
    # print(hasattr(obj, 'role'), RoleStudentPublicSerializer(obj.role).data)
    if not hasattr(obj, 'role_student') and not hasattr(obj, 'role_teacher'):
        return None
    if obj.role == UserRoleChoice.STUDENT:
        role_data = student_model(obj.role_student, context=self.context).data
    elif obj.role == UserRoleChoice.TEACHER:
        role_data = teacher_model(obj.role_teacher, context=self.context).data
    else:
        raise ValueError(f"{obj.role=} 数据异常！")
    # 将身份类型和其他信息结合到一起，保证输出一致
    role_data['role'] = obj.role
    return role_data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = User.FIELDS

    role = serializers.SerializerMethodField()

    def get_role(self, obj: User):
        return _get_role(self, obj, RoleStudentSerializer, RoleTeacherSerializer)


class UserCurrentSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = User.FIELDS_CURRENT

    role = serializers.SerializerMethodField()

    def get_role(self, obj: User):
        return _get_role(self, obj, RoleStudentCurrentSerializer, RoleTeacherCurrentSerializer)


# 用于创建和修改用户信息的序列化器

class UserStudentSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = User.EDITABLE_FIELDS + [
            "school", "campus", "city"
        ]

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

# --- END ---
