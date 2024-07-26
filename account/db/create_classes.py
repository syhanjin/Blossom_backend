# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from account.models.class_ import Class
from account.models.choices import ClassTypeChoice

"""
shell 
from account.db.create_classes import *

"""
User = get_user_model()


def create_class(name, created,
                 type=ClassTypeChoice.ADMINISTRATIVE,
                 nickname=None,
                 headteacher: User | None = None,
                 teachers: QuerySet | None = None,
                 students: QuerySet | None = None):
    class_obj = Class.objects.create(
        name=name,
        created=created,
        nickname=nickname or name,
        type=type,
        headteacher=headteacher.role_teacher,
    )
    if teachers is not None:
        class_obj.teachers.set(
            teachers.values_list("role_teacher", flat=True),
            through_defaults={}
        )
    if teachers is None or not teachers.filter(pk=headteacher.pk).exists():
        class_obj.teachers.add(
            headteacher.role_teacher,
            through_defaults={}
        )
    if students is not None:
        class_obj.students.set(
            students.values_list("role_student", flat=True),
            through_defaults={}
        )
    class_obj.save()
    return class_obj
