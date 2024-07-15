# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated

from account.conf import settings
from account.models.user import AdminChoice

User = get_user_model()


class _Admin(IsAuthenticated):
    def _has_permission(self, admin, request, view):
        return super().has_permission(request, view) and request.user.admin > admin


class Admin(_Admin):
    def has_permission(self, request, view):
        return super()._has_permission(AdminChoice.NORMAL, request, view)


class AdminDeveloper(_Admin):
    def has_permission(self, request, view):
        return super()._has_permission(AdminChoice.DEVELOPER, request, view)


class CurrentUser(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return obj.pk == user.pk


class Student(IsAuthenticated):
    def has_permission(self, request, view):
        return (
                super(Student, self).has_permission(request, view)
                and request.user.role.role == settings.choices.user_role.STUDENT
        )


class Teacher(IsAuthenticated):
    def has_permission(self, request, view):
        return (
                super(Teacher, self).has_permission(request, view)
                and request.user.role.role == settings.choices.user_role.TEACHER
        )


class OnSameAdministrativeClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return (
                super(OnSameAdministrativeClass, self).has_object_permission(request, view, obj)
                and isinstance(obj, User)
                and (obj.get_administrative_class() & request.user.get_administrative_classes()).exists()
        )


class OnSameClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return (  # 有额外的数据库请求！
                super(OnSameClass, self).has_object_permission(request, view, obj)
                # and isinstance(obj, User) 开发的时候注意一点就好了
                and (obj.classes & request.user.classes).exists()
        )


class CanEditCurrentClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return (
                super(CanEditCurrentClass, self).has_object_permission(request, view, obj)
                and obj.editors.filter(pk=request.user.pk).exists()
        )


class OnCurrentClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return (
                super(OnCurrentClass, self).has_object_permission(request, view, obj)
                and (
                        obj.students.filter(pk=request.user.role_obj.pk).exists()
                        or obj.headteacher.pk == request.user.role_obj.pk
                        or obj.teachers.filter(pk=request.user.role_obj.pk).exists()
                )
        )


class ManageCurrentClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return (
                super(ManageCurrentClass, self).has_object_permission(request, view, obj)
                and request.user.managed_classes.filter(pk=obj.pk).exists()
        )


CurrentUserOrAdmin = CurrentUser | Admin

StudentOrAdmin = Student | Admin
TeacherOrAdmin = Teacher | Admin

# 把编辑权限算作管理员权限
OnSameClassOrAdmin = OnSameClass | Admin | CanEditCurrentClass
OnCurrentClassOrAdmin = OnCurrentClass | Admin | CanEditCurrentClass
ManageCurrentClassOrAdmin = ManageCurrentClass | Admin | CanEditCurrentClass
