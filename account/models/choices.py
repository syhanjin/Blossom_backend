# -*- coding: utf-8 -*-
from django.db import models


class ClassTypeChoice(models.TextChoices):
    ADMINISTRATIVE = "administrative", "行政班级"
    WALKING = "walking", "走班班级"


class AdminChoice(models.IntegerChoices):
    USER = 0, "普通用户"
    NORMAL = 1, "管理员"

    SUPER = 5, "超级管理员"
    DEVELOPER = 10, "开发者"


class UserRoleChoice(models.TextChoices):
    STUDENT = "student", "学生"
    TEACHER = "teacher", "老师"
    PARENT = "PARENT", "家长"


class GenderChoices(models.TextChoices):
    male = "male", "男"
    female = "female", "女"
