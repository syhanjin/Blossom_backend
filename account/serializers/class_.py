# -*- coding: utf-8 -*-
from rest_framework import serializers

from account.conf import settings
from account.models.class_ import Class, ClassStudent, ClassTeacher


class ClassPublicSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = Class.PUBLIC_SIMPLE_FIELDS

    teacher_count = serializers.IntegerField(read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    headteacher = settings.serializers.user_private_simple(source="headteacher.user", is_teacher=True)


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


class ClassAllSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = Class.ALL_FIELDS

    teacher_count = serializers.IntegerField(read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    headteacher = settings.serializers.user_private_simple(source="headteacher.user", is_teacher=True)
    students = serializers.SerializerMethodField()
    teachers = serializers.SerializerMethodField()
    get_students = _get_members('students',
                                settings.serializers.user_private_simple,
                                settings.serializers.class_student_simple)
    get_teachers = _get_members('teachers',
                                settings.serializers.user_private_simple,
                                settings.serializers.class_teacher_simple, is_teacher=True)
    photo_preview = serializers.ImageField()
