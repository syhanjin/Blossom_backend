# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated

from account.models import Class, ClassMembership, ClassStudent, ClassTeacher
from account.models.choices import AdminChoice, UserRoleChoice

User = get_user_model()


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


class CurrentUser(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return obj.pk == user.pk


class Student(IsAuthenticated):
    def has_permission(self, request, view):
        return (
                super(Student, self).has_permission(request, view)
                and request.user.role.role == UserRoleChoice.STUDENT
        )


class Teacher(IsAuthenticated):
    def has_permission(self, request, view):
        return (
                super(Teacher, self).has_permission(request, view)
                and request.user.role.role == UserRoleChoice.TEACHER
        )


class CurrentMember(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, (ClassStudent, ClassTeacher)):
            return True
        return (
                super(CurrentMember, self).has_permission(request, view)
                and request.user.pk == obj.user_role.user.pk
        )


class OnSameAdministrativeClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, User):
            return True
        return (
                super(OnSameAdministrativeClass, self).has_permission(request, view)
                and (obj.get_administrative_class() & request.user.get_administrative_classes()).exists()
        )


class OnSameClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, User):
            return True
        return (  # 有额外的数据库请求！
                super(OnSameClass, self).has_permission(request, view)
                and (obj.classes & request.user.classes).exists()
        )


class OnSameClassWithClassMemberShip(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, ClassMembership):
            return True
        return (
                super(OnSameClassWithClassMemberShip, self).has_permission(request, view)
                and request.user.classes.filter(pk=obj.classes.pk).exists()
        )


class CanEditCurrentClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Class):
            return True
        return (
                super(CanEditCurrentClass, self).has_permission(request, view)
                and isinstance(obj, Class)
                and obj.editors.filter(pk=request.user.pk).exists()
        )


class OnCurrentClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Class):
            return True
        return (
                super(OnCurrentClass, self).has_permission(request, view)
                and request.user.role_obj is not None
                and (
                        obj.students.filter(pk=request.user.role_obj.pk).exists()
                        or obj.headteacher.pk == request.user.role_obj.pk
                        or obj.teachers.filter(pk=request.user.role_obj.pk).exists()
                )
        )


class IsMapActive(OnCurrentClass):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Class):
            return True
        return (
                super(IsMapActive, self).has_object_permission(request, view, obj)
                and obj.map_activated
        )


class AccessToDestination(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, User):
            return True
        return (
                super().has_permission(request, view)
                and obj.role == UserRoleChoice.STUDENT
                and (
                        request.user.pk == obj.pk or
                        (  # 老师可以看到学生的去向，不需要这个班级的地图功能开启
                                request.user.role == UserRoleChoice.TEACHER
                                and request.user.classes.all().filter(students__pk=obj.id).exists()
                        ) or (
                                request.user.role == UserRoleChoice.STUDENT
                                and request.user.classes.all().filter(map_activated=True, students__pk=obj.id).exists()
                        )
                )
        )


class ManageCurrentClass(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Class):
            return True
        return (
                super(ManageCurrentClass, self).has_permission(request, view)
                and request.user.role == UserRoleChoice.TEACHER
                and request.user.role_teacher.managed_classes.filter(pk=obj.pk).exists()
        )


CurrentUserOrAdmin = CurrentUser | Admin

StudentOrAdmin = Student | Admin
TeacherOrAdmin = Teacher | Admin

# 把编辑权限算作管理员权限
OnSameClassOrAdmin = OnSameClass | Admin
OnSameClassWithClassMembershipOrAdmin = OnSameClassWithClassMemberShip | Admin
OnCurrentClassOrAdmin = OnCurrentClass | Admin | CanEditCurrentClass
CurrentMemberOrAdmin = CurrentMember | Admin

# 管理班级===具有编辑权限
ManageCurrentClassOrAdmin = ManageCurrentClass | Admin | CanEditCurrentClass
