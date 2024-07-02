# -*- coding: utf-8 -*-
import warnings

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import QuerySet
from imagekit.models import ProcessedImageField
from phonenumber_field.modelfields import PhoneNumberField
from pilkit.processors import ResizeToFill

from utils import create_uuid
from account.conf import settings as account_settings


class UserManager(BaseUserManager):
    # 定义用户管理器方法
    def create_user(self, nickname, password=None):
        """
        创建用户
        """
        if not nickname:
            raise ValueError('用户必须拥有用户名')

        user = self.model(nickname=nickname, )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, nickname, password, admin=1):
        """
        创建并保存超级用户
        """
        user = self.create_user(
            password=password,
            nickname=nickname,
        )
        user.admin = admin
        user.save(using=self._db)
        return user


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


class User(AbstractBaseUser, PermissionsMixin, models.Model):
    class Meta:
        # db_table = "account"
        indexes = [
            models.Index(fields=['id', 'name', '-created']),
        ]

    # 删除一些父类中的字段
    # is_active = None
    is_superuser = None

    id = models.CharField("用户id", primary_key=True, default=create_uuid, editable=False, max_length=8)
    created = models.DateTimeField("创建时间", auto_now_add=True, editable=False)
    admin = models.PositiveSmallIntegerField("管理员级别", choices=AdminChoice.choices, default=AdminChoice.USER)

    nickname = models.CharField("昵称", unique=True, max_length=64)
    avatar = ProcessedImageField(
        verbose_name="头像", default='avatar/default.jpg', upload_to='avatar',
        processors=[ResizeToFill(72, 72)], format='JPEG',
        options={'quality': 80}
    )

    # 身份信息
    name = models.CharField("名字", max_length=16)
    gender = models.CharField("性别", max_length=6, choices=GenderChoices.choices)
    birthday = models.DateField("生日", null=True)
    photo = ProcessedImageField(
        verbose_name="个人照", default='photo/default.jpg', upload_to='photo',
        processors=[ResizeToFill(768, 1024)], format='JPEG',
        options={'quality': 100}
    )
    # TODO: 保护媒体文件

    # 身份信息，student: role_student, teacher: role_teacher
    # 允许此处设为null 因为给用户绑定身份的操作与创建用户不放入一个模块
    role = models.CharField("身份", null=True, choices=UserRoleChoice.choices, max_length=7)

    # 联系方式
    phone = PhoneNumberField(verbose_name="手机号码", region="CN", null=True)
    email = models.EmailField(verbose_name="邮箱", null=True)
    QQ = models.CharField("QQ", max_length=14, null=True)
    WeChat = models.CharField("微信", max_length=64, null=True)

    # TODO: 去向统计

    # 班级关联信息，从班级关联用户

    objects = UserManager()

    REQUIRED_FIELDS = []
    PUBLIC_SIMPLE_FIELDS = [
        "id", "nickname", "role", "avatar",
    ]
    PUBLIC_FIELDS = PUBLIC_SIMPLE_FIELDS + [
        "created",
    ]
    PRIVATE_SIMPLE_FIELDS = [
        "id", "name", "nickname", "gender", "role", "avatar", "photo"
    ]
    PRIVATE_FIELDS = PRIVATE_SIMPLE_FIELDS + [
        "created",
    ]
    ALL_FIELDS = PUBLIC_FIELDS + [
        "name", "gender", "birthday", "photo",  # 身份信息
        "phone", "email", "QQ", "WeChat",  # 联系方式
    ]
    USERNAME_FIELD = "nickname"

    def get_avatar_url(self) -> str:
        return settings.MEDIA_URL + str(self.avatar)

    def get_administrative_classes(self) -> QuerySet:
        return self.classes.filter(type=account_settings.choices.class_type.ADMINISTRATIVE)

    def get_walking_classes(self) -> QuerySet:
        return self.classes.filter(type=account_settings.choices.class_type.WALKING)

    def get_classmates(self) -> QuerySet:
        # querysets = self.classes.prefetch_related("students__user").values_list('user', flat=True).all()
        # print(querysets)
        # print(querysets[0])
        # if isinstance(querysets, QuerySet):
        #     return querysets
        # return QuerySet(User).union(*querysets)
        # classmates = QuerySet(User)
        # for class_obj in self.classes:
        #     students = class_obj.students.all()
        return User.objects.filter(id__in=self.classes.values_list("students", flat=True).all())

    def get_teachers(self):
        return User.objects.filter(id__in=self.classes.values_list("teachers", flat=True).all())

    @property
    def classes(self) -> QuerySet:
        warnings.warn("怕忽略此问题所以留下警告："
                      "创建老师数据时班主任也要加入任课老师内，"
                      "因为暂时没有将班主任合并进classes里，会漏", Warning)
        if self.role == UserRoleChoice.STUDENT:
            return self.role_student.classes.all()
        elif self.role == UserRoleChoice.TEACHER:
            return self.role_teacher.classes.all()

    @property
    def role_obj(self) -> 'RoleStudent | RoleTeacher | None':
        if self.role == UserRoleChoice.STUDENT:
            return self.role_student
        elif self.role == UserRoleChoice.TEACHER:
            return self.role_teacher
        else:
            return None


class Role(models.Model):
    """
    用于储存用户的身份信息，此处预留学生与老师信息的公共部分，班级信息绑定到了Role上（分开）
    """

    class Meta:
        abstract = True


# 暂时不能确定 Role 会不会额外建表
class RoleStudent(Role):
    """
    用于储存用户的身份信息
    """
    user = models.OneToOneField(User, related_name="role_student", on_delete=models.CASCADE, primary_key=True)

    PUBLIC_FIELDS = ["classes"]
    ALL_FIELDS = PUBLIC_FIELDS + []


class RoleTeacher(Role):
    user = models.OneToOneField(User, related_name="role_teacher", on_delete=models.CASCADE, primary_key=True)
    subject = models.CharField("科目", max_length=64)

    PUBLIC_FIELDS = ["classes", "managed_classes", "subject"]
    ALL_FIELDS = PUBLIC_FIELDS + []
