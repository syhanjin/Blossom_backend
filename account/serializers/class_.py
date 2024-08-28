# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from rest_framework import serializers

from account.models.class_ import Class, ClassStudent, ClassTeacher
from account.models.choices import UserRoleChoice
from account.serializers.class_user_through import ClassStudentSimpleSerializer, ClassTeacherSimpleSerializer
from account.serializers.user_simple import UserSimpleSerializer

User = get_user_model()


class ClassSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = Class.SIMPLE_FIELDS

    teacher_count = serializers.IntegerField(read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    headteacher = UserSimpleSerializer(source="headteacher.user", is_teacher=True)


def _get_members(role, serializer, through_serializer, **kwargs):
    def func(self, obj):
        # TODO: 暂时采用该方案，中间件在序列化的时候获取
        # return serializer(getattr(obj, role).prefetch_related("user").values_list("user", flat=True), many=True).data
        members = getattr(obj, role)
        # return serializer([member.user for member in members.all()], many=True, **kwargs).data
        '''
        在此处我会实现中间件的获取，必要的话会在这里添加班干部和课代表信息吗。
        我会在序列化完成之后添加，获取中间件本来就有数据库请求，所以（理论上）这个方案不会带来额外的请求。
        中间件本来就需要自己获取！
        '''
        ret = []
        for member in members.all():
            # 修复bug，图片路径不是url：附带context
            data = serializer(member.user, **kwargs, context=self.context).data
            if role == 'students':
                through = ClassStudent.objects.get(user_role=member, classes=self.instance)
            elif role == 'teachers':
                through = ClassTeacher.objects.get(user_role=member, classes=self.instance)
            else:
                raise ValueError()
            through_data = through_serializer(through, context=self.context).data
            data.update(through_data)
            ret.append(data)
        return ret

    return func


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = Class.ALL_FIELDS

    teacher_count = serializers.IntegerField(read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    headteacher = UserSimpleSerializer(source="headteacher.user", is_teacher=True)
    students = serializers.SerializerMethodField()
    teachers = serializers.SerializerMethodField()
    get_students = _get_members('students',
                                UserSimpleSerializer,
                                ClassStudentSimpleSerializer)
    get_teachers = _get_members('teachers',
                                UserSimpleSerializer,
                                ClassTeacherSimpleSerializer, is_teacher=True)

    photo_preview = serializers.ImageField()


class ClassPhotoSetSerializer(serializers.Serializer):
    photo = serializers.ImageField()


class ClassSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = Class.EDITABLE_FIELDS


class ClassCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = Class.REQUIRED_FIELDS + ["id"]

    id = serializers.CharField(max_length=8, required=False)
    name = serializers.CharField(max_length=5)
    created = serializers.IntegerField(min_value=2017, max_value=2500)
    headteacher = serializers.CharField(min_length=8, max_length=8)

    def validate_name(self, value: str):
        value = value.upper()
        if not len(value) == 5:
            raise serializers.ValidationError(f"{value=} 的长度不是5")
        if not value[0] in ["C", "K"]:
            raise serializers.ValidationError(f"{value=} 不是以`C`或`K`开头")
        if not value[1:].isdigit():
            raise serializers.ValidationError(f"{value=} 的后四位不是数字")
        return value

    def validate_headteacher(self, value):
        headteacher = User.objects.filter(id=value)
        if not headteacher.exists():
            raise serializers.ValidationError("所设置的班主任不存在")
        headteacher = headteacher.first()
        if headteacher.role != UserRoleChoice.TEACHER:
            raise serializers.ValidationError("所设置的班主任不是老师")
        if not headteacher.role_teacher:
            raise ValueError
        return headteacher.role_teacher


def _validate_member(value, role, role_name):
    if len(value) == 0:
        raise serializers.ValidationError(f"请至少设置一名{role_name}")
    members = []
    err = []
    for _id in value:
        obj = User.objects.filter(id=_id)
        if not obj.exists():
            err.append(f"用户{_id}不存在")
            continue
        obj = obj.first()
        if obj.role != role:
            err.append(f"用户{_id}不是{role_name}")
        elif not obj.role_obj:
            raise ValueError
        else:
            members.append(obj.role_obj)
    if len(err) > 0:
        raise serializers.ValidationError(err)
    return members


class ClassStudentAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["students"]

    students = serializers.ListField(child=serializers.CharField(min_length=8, max_length=8))

    def validate_students(self, value):
        return _validate_member(value, UserRoleChoice.STUDENT, "学生")


class ClassTeacherAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["teachers"]

    teachers = serializers.ListField(child=serializers.CharField(min_length=8, max_length=8))

    def validate_teachers(self, value):
        return _validate_member(value, UserRoleChoice.TEACHER, "老师")
