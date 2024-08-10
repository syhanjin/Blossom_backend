import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class App(models.Model):
    id = models.UUIDField(verbose_name="UUID", primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(verbose_name="应用名称", max_length=64, unique=True)
    verbose_name = models.CharField(verbose_name="应用展示名称", max_length=64)
    description = models.TextField(verbose_name="介绍")


class AppUpdateMode(models.TextChoices):
    # 默认更新，即用户可以选择跳过更新
    default = "default", "默认更新"
    # 强制更新模式，适用于后端api路径发生变更的情况
    force = "force", "强制更新"


class AppVersion(models.Model):
    class Meta:
        ordering = ["-released"]
        constraints = [
            models.UniqueConstraint(fields=['app', 'version_name'], name='app_version_name'),
            models.UniqueConstraint(fields=['app', 'version_code'], name='app_version_code'),
        ]

    id = models.UUIDField(verbose_name="UUID", primary_key=True, default=uuid.uuid4, editable=False)
    app = models.ForeignKey(to=App, related_name='versions', on_delete=models.CASCADE)

    version_name = models.CharField(max_length=64, verbose_name="版本名称")
    version_code = models.PositiveIntegerField(verbose_name="版本号")
    updates = models.TextField(verbose_name="更新内容")
    author = models.ForeignKey(User, verbose_name='发布者', null=True, on_delete=models.SET_NULL)
    released = models.DateTimeField(verbose_name="发布时间", auto_now_add=True, editable=False)
    installer = models.FileField(verbose_name="apk", upload_to="apps/")

    mode = models.CharField(max_length=16, choices=AppUpdateMode.choices, default=AppUpdateMode.default)

    REQUIRED_FIELDS = [
        "id",
        "version_name", "version_code",
        "updates", "mode",
        "installer",
    ]

    def __unicode__(self):
        return self.app.name + " " + self.version_name


class AppWgtVersion(models.Model):
    # wgt更新模式
    pass
