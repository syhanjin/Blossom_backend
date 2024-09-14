# -*- coding: utf-8 -*-
__doc__ = """
20240912 重构权限系统

----------
通用权限
IsAuthenticated 需要登录账号
AllowAny        不进行权限检验
----------
权限                            检验对象                      说明
CurrentUser                     User/Role/ClassMembership   被访问的对象是访问者本身
IsStudent                       /   
IsTeacher                       /   
OnSameClass                     User/Role/ClassMembership   被访问的对象与当前用户在同一个班       
OnSameAdministrativeClass       User/Role/ClassMembership   被访问的对象与当前用户在同一个行政班    注意，此三项权限不用区分老师和学生
OnSameWalkingClass              User/Role/ClassMembership   被访问的对象与当前用户在同一个走班班级   
AccessToDestination             User/Role/ClassMembership   用户是否拥有权查看被访问的对象的去向

OnCurrentClass                  Class                       用户在当前班级内
IsHeadteacher                   Class                       是否为班级班主任
CanEditClass                    Class                       是否有编辑权限 含班主任
IsMapActive                     Class                       班级地图功能是否开启

CurrentMember                   ClassMemberShip

----------
管理权限
_Admin
Admin           普通管理员   1
AdminSuper      超级管理员   5
AdminDeveloper  我         10

""".strip()

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from rest_framework.permissions import IsAuthenticated

from account.models import Class, ClassStudent, ClassTeacher, RoleStudent, RoleTeacher
from account.models.choices import AdminChoice, ClassTypeChoice, UserRoleChoice

User = get_user_model()


# - - - - - - 管理员权限 - - - - - -
class _Admin(IsAuthenticated):
    def _has_permission(self, admin, request, view):
        return super().has_permission(request, view) and request.user.admin >= admin


class Admin(_Admin):
    def has_permission(self, request, view):
        return super()._has_permission(AdminChoice.NORMAL, request, view)


class AdminSuper(_Admin):
    def has_permission(self, request, view):
        return super()._has_permission(AdminChoice.SUPER, request, view)


class AdminDeveloper(_Admin):
    def has_permission(self, request, view):
        return super()._has_permission(AdminChoice.DEVELOPER, request, view)


# - - - - - - 用户权限 - - - - - -
class CurrentUser(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, User):
            return obj.pk == request.user.pk
        elif isinstance(obj, (RoleStudent, RoleTeacher)):
            return request.user.id == obj.user_id
        elif isinstance(obj, (ClassStudent, ClassTeacher)):
            return request.user.id == obj.user_role_id
        else:
            raise TypeError("object类型不匹配(CurrentUser)")


CurrentUserOrAdmin = Admin | CurrentUser


class Student(IsAuthenticated):
    def has_permission(self, request, view):
        return bool(
            super().has_permission(request, view) and
            request.user.role == UserRoleChoice.STUDENT
        )


StudentOrAdmin = Admin | Student


class Teacher(IsAuthenticated):
    def has_permission(self, request, view):
        return bool(
            super().has_permission(request, view) and
            request.user.role == UserRoleChoice.TEACHER
        )


TeacherOrAdmin = Admin | Teacher


class OnSameClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not super().has_permission(request, view):
            return False
        if isinstance(obj, User):
            return (obj.classes & request.user.classes).exists()
        elif isinstance(obj, RoleStudent):
            return (obj.classes.all() & request.user.classes).exists()
        elif isinstance(obj, RoleTeacher):
            return ((obj.classes.all() | obj.managed_classes.all()) & request.user.classes).exists()
        elif isinstance(obj, ClassStudent):
            return (obj.user_role.classes.all() & request.user.classes).exists()
        elif isinstance(obj, ClassTeacher):
            return ((obj.user_role.classes.all() | obj.user_role.managed_classes.all()) & request.user.classes).exists()
        else:
            raise TypeError("object类型不匹配(OnSameClass)")


OnSameClassOrAdmin = Admin | OnSameClass


def administrative(qs: QuerySet[Class]) -> QuerySet[Class]:
    return qs.filter(type=ClassTypeChoice.ADMINISTRATIVE)


class OnSameAdministrativeClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not super().has_permission(request, view):
            return False
        if isinstance(obj, User):
            return administrative(obj.classes & request.user.classes).exists()
        elif isinstance(obj, RoleStudent):
            return administrative(obj.classes.all() & request.user.classes).exists()
        elif isinstance(obj, RoleTeacher):
            return administrative((obj.classes.all() | obj.managed_classes.all()) & request.user.classes).exists()
        elif isinstance(obj, ClassStudent):
            return administrative(obj.user_role.classes.all() & request.user.classes).exists()
        elif isinstance(obj, ClassTeacher):
            return administrative(
                (obj.user_role.classes.all() | obj.user_role.managed_classes.all()) & request.user.classes).exists()
        else:
            raise TypeError("object类型不匹配(OnSameAdministrativeClass)")


OnSameAdministrativeClassOrAdmin = Admin | OnSameAdministrativeClass


class AccessToDestination(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not super().has_permission(request, view):
            return False
        if isinstance(obj, User):
            return (request.user.pk == obj.pk or
                    (request.user.role == UserRoleChoice.TEACHER and
                     request.user.classes.all().filter(students__pk=obj.id).exists()) or
                    (request.user.role == UserRoleChoice.STUDENT and
                     request.user.classes.all().filter(map_activated=True, students__pk=obj.id).exists())
                    )
        elif isinstance(obj, RoleStudent):
            return (
                    request.user.pk == obj.user_id or
                    request.user.classes.all().filter(map_activated=True, students__pk=obj.pk).exists()
            )
        elif isinstance(obj, (RoleTeacher, ClassTeacher)):
            return False
        elif isinstance(obj, ClassStudent):
            return (
                    request.user.pk == obj.user_role_id or
                    request.user.classes.all().filter(map_activated=True, students__pk=obj.user_role_id).exists()
            )
        else:
            raise TypeError("object类型不匹配(AccessToDestination)")


# - - - - - - 班级权限 - - - - - -

class OnCurrentClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Class):
            raise TypeError("object类型不匹配(OnCurrentClass)")

        if not super().has_permission(request, view):
            return False
        if request.user.role_obj is None:
            return False
        return request.user.classes.filter(pk=obj.pk).exists()


OnCurrentClassOrAdmin = Admin | OnCurrentClass


class IsHeadteacher(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Class):
            raise TypeError("object类型不匹配(IsHeadteacher)")

        if not super().has_permission(request, view):
            return False
        if request.user.role_obj is None or request.user.role != UserRoleChoice.TEACHER:
            return False
        return request.user.id == obj.headteacher_id  # 单对单关系所以id是一样的


class IsEditor(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Class):
            raise TypeError("object类型不匹配(CanEditClass)")

        if not super().has_permission(request, view):
            return False
        return obj.editors.filter(pk=request.user.pk).exists()


IsHeadteacherOrEditorOrAdmin = Admin | IsHeadteacher | IsEditor


class IsMapActive(OnCurrentClass):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Class):
            raise TypeError("object类型不匹配(IsMapActive)")
        if not super().has_object_permission(request, view, obj):
            return False
        return obj.map_activated
