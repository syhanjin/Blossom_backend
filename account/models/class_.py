# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.db import models

from account.conf import settings
from utils import create_uuid

User = get_user_model()


class ClassTypeChoice(models.TextChoices):
    ADMINISTRATIVE = "administrative", "行政班级"
    WALKING = "walking", "走班班级"


class ClassManager(models.Manager):
    def get_queryset(self):
        """
        将统计老师和学生数的过程加到这里（暂定）
        """
        return super().get_queryset().annotate(
            teacher_count=models.Count('teachers'),
            student_count=models.Count('students'),
        )


class Class(models.Model):
    """
    注1：所有班级信息统一与Role关联，因为需要区分老师和学生
    """
    id = models.CharField("班级id", primary_key=True, default=create_uuid, editable=False, max_length=8)
    name = models.CharField("班级名称", max_length=6)  # 例如：K2111

    nickname = models.CharField("班级昵称", max_length=64)  # 可以自己设置
    created = models.PositiveSmallIntegerField("建班年份")
    type = models.CharField("班级类型", choices=ClassTypeChoice.choices, max_length=15)
    description = models.TextField("班级描述", null=True, blank=True)
    # 班级人员信息
    students = models.ManyToManyField(
        "account.RoleStudent", related_name="classes", related_query_name="classes", through="ClassStudent"
    )
    teachers = models.ManyToManyField(
        "account.RoleTeacher", related_name="classes", related_query_name="classes", through="ClassTeacher"
    )
    headteacher = models.ForeignKey(
        settings.models.user_role_teacher, on_delete=models.SET_NULL, null=True, related_name="managed_classes",
        verbose_name="班主任"
    )
    # officers = models.ManyToManyField(
    #
    # )

    PUBLIC_SIMPLE_FIELDS = [
        "id", "name", "nickname", "type",
        "created", "headteacher",
        "teacher_count", "student_count"
    ]
    PUBLIC_FIELDS = PUBLIC_SIMPLE_FIELDS + [
        "description"
    ]
    ALL_FIELDS = PUBLIC_FIELDS + [
        "students", "teachers"
    ]

    objects = ClassManager()


class ClassMembership(models.Model):
    class Meta:
        abstract = True

    # 命名不规范，将就一下
    classes = models.ForeignKey(Class, on_delete=models.CASCADE)
    nickname = models.TextField("外号", max_length=1024, null=True)

    joined = models.DateTimeField("加入时间", null=True, default=None)
    exited = models.DateTimeField("离开时间", null=True, default=None)


class ClassStudent(ClassMembership):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['classes', 'user_role'], name='class_membership_student')
        ]

    user_role = models.ForeignKey("account.RoleStudent", on_delete=models.CASCADE)
    rank = models.CharField("在班级内的“地位”", max_length=128, null=True)
    # 班级内的职位
    """
    说明：
    区分走班和行政班，职位的选项不同，ClassOfficer的administrative和walking两个健用于区分
    """
    position = models.ForeignKey('account.ClassOfficer', verbose_name="职位", on_delete=models.SET_NULL, null=True)
    number = models.PositiveSmallIntegerField("学号", null=True)

    SIMPLE_FIELDS = [
        "number", "rank", "position", "nickname"
    ]


class ClassTeacher(ClassMembership):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['classes', 'user_role'], name='class_membership_teacher')
        ]

    user_role = models.ForeignKey("account.RoleTeacher", on_delete=models.CASCADE)
    SIMPLE_FIELDS = ["nickname"]


class ClassOfficer(models.Model):
    """
    记录班级职务名称，用户通过外键关联职务
    """
    name = models.CharField(max_length=64, primary_key=True)
    administrative = models.BooleanField()
    walking = models.BooleanField()
