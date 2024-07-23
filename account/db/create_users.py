# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model

from account.conf import settings
from account.models import RoleStudent, RoleTeacher
from account.models.user import UserRoleChoice

"""
shell 
from account.db.create_users import *
u = create_developer_user(nickname="hanjin",password="123456")
set_role(u, "student")
t1 = create_teacher_user("张", "数学", "123456")
t2 = create_teacher_user("李", "数学", "123456")
t3 = create_teacher_user("赵", "数学", "123456")
"""
User = get_user_model()


def create_developer_user(nickname, password=None):
    return User.objects.create_superuser(
        nickname=nickname,
        admin=10,
        password=password
    )


def set_role(user, role, **kwargs):
    if role == settings.choices.user_role.STUDENT:
        _role = RoleStudent.objects.create(user=user, **kwargs)
    elif role == settings.choices.user_role.TEACHER:
        _role = RoleTeacher.objects.create(user=user, **kwargs)
    else:
        raise ValueError(f'Unknown role: {role}')
    user.role = role
    user.save()
    _role.save()


def create_student_user(nickname, password=None):
    user = User.objects.create_user(nickname=nickname, password=password)
    set_role(user, settings.choices.user_role.STUDENT)
    return user


def create_teacher_user(nickname, subject, password=None):
    user = User.objects.create_user(nickname=nickname, password=password)
    set_role(user, UserRoleChoice.TEACHER, subject=subject)
    return user
