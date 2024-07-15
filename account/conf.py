# -*- coding: utf-8 -*-
from conf import ObjDict, create_lazy_settings

SETTINGS_NAMESPACE = "account"


def serializer(name):
    return f"account.serializers.{name}"


def model(name):
    return f"account.models.{name}"


def permission(name):
    return f"account.permissions.{name}"


default_settings = {
    "permissions": ObjDict(
        {}
    ),
    "models": ObjDict(
        {
            "user_role": model("user.Role"),
            "user_role_student": model("user.RoleStudent"),
            "user_role_teacher": model("user.RoleTeacher"),
            "class_": model("class_.Class"),
            "class_student": model("class_.ClassStudent"),
            "class_teacher": model("class_.ClassTeacher"),
            "class_officer": model("class_.ClassOfficer"),
        }
    ),
    "serializers": ObjDict(
        {
            # 用户数据序列化器
            "user_public_simple": serializer("user_simple.UserPublicSimpleSerializer"),
            "user_private_simple": serializer("user_simple.UserPrivateSimpleSerializer"),
            "user_public": serializer("user.UserPublicSerializer"),
            "user_private": serializer("user.UserPrivateSerializer"),
            "user_all": serializer("user.UserAllSerializer"),
            "user_set": serializer("user.UserSetSerializer"),
            # 用户身份数据序列化器
            "role_student_public": serializer("user.RoleStudentPublicSerializer"),
            "role_teacher_public": serializer("user.RoleTeacherPublicSerializer"),
            # 班级序列化器
            "class_public_simple": serializer("class_.ClassPublicSimpleSerializer"),
            "class_all": serializer("class_.ClassAllSerializer"),
            # 班级-用户中间件序列化
            "class_student_simple": serializer("class_user_through.ClassStudentSimpleSerializer"),
            "class_teacher_simple": serializer("class_user_through.ClassTeacherSimpleSerializer"),
            # 班级职位
            "class_officer": serializer("class_user_through.ClassOfficerTypeSerializer"),
        }
    ),
    "choices": ObjDict(
        {
            "user_role": model("user.UserRoleChoice"),
            "class_type": model("class_.ClassTypeChoice"),
        }
    )
}

settings = create_lazy_settings(default_settings, SETTINGS_NAMESPACE, [])
