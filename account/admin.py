from django.contrib import admin

from account.models import RoleStudent, RoleTeacher, User


class UserRoleStudentInline(admin.StackedInline):
    model = RoleStudent


class UserRoleTeacherInline(admin.StackedInline):
    model = RoleTeacher


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # inlines = [UserRoleTeacherInline, UserRoleStudentInline]
    list_display = ('id', "admin", 'nickname', "gender", "role")
    readonly_fields = ("id", "created", "admin", "role")
    fieldsets = (
        ("用户信息", {"fields": ("id", "created", "admin", "avatar")}),
        ("个人基本信息", {"fields": ("name", "gender", "birthday", "photo")}),
        ("联系方式", {"fields": ("phone", "email", "QQ", "WeChat")}),
        ("班级信息", {"fields": ("role",)})
    )
