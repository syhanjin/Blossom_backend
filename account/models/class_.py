# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import QuerySet
from imagekit.models import ImageSpecField, ProcessedImageField
from pilkit.processors import ResizeToFill

from account.models import RoleStudent
from account.models.choices import ClassTypeChoice
from account.serializers.user_map import UserMapSerializer
from destination.utils.geo import district_to_feature, get_district
from utils import create_uuid, file_path_getter

User = get_user_model()


def class_photo_path(instance, filename):
    return file_path_getter('class_photo/', instance, filename)


def map_path(instance, filename):
    return file_path_getter('map/', instance, filename)


class ClassManager(models.Manager):
    def get_queryset(self):
        """
        将统计老师和学生数的过程加到这里（暂定）
        *bug*
        这里的统计会发生错误 经过一大坨调试发现 原本生成的Sql语句
        ------------------------
        SELECT `account_class`.`id`,
               `account_class`.`name`,
               `account_class`.`nickname`,
               `account_class`.`created`,
               `account_class`.`type`,
               `account_class`.`description`,
               `account_class`.`headteacher_id`,
               `account_class`.`photo`,
               `account_class`.`photo_desc`,
               COUNT(`account_classteacher`.`user_role_id`) AS `teacher_count`,
               COUNT(`account_classstudent`.`user_role_id`) AS `student_count`
        FROM `account_class`
                 LEFT OUTER JOIN `account_classteacher` ON (`account_class`.`id` = `account_classteacher`.`classes_id`)
                 LEFT OUTER JOIN `account_classstudent` ON (`account_class`.`id` = `account_classstudent`.`classes_id`)
                 INNER JOIN `account_classstudent` T6 ON (`account_class`.`id` = T6.`classes_id`)
        WHERE T6.`user_role_id` = 72591729
        GROUP BY `account_class`.`id`
        ORDER BY NULL
        ------------------------
        会导致 teacher_count 和 student_count 统计错误
        需要加上 distinct 具体原因未知（）
        设置 distinct=True 后统计正常，sql语句中
        ------------------------
        COUNT(`account_classteacher`.`user_role_id`) AS `teacher_count`,
        COUNT(`account_classstudent`.`user_role_id`) AS `student_count`
        ------------------------
        变为
        ------------------------
        COUNT(DISTINCT `account_classteacher`.`user_role_id`) AS `teacher_count`,
        COUNT(DISTINCT `account_classstudent`.`user_role_id`) AS `student_count`
        ------------------------
        问题解决
        """
        return super().get_queryset().annotate(
            teacher_count=models.Count('teachers', distinct=True),
            student_count=models.Count('students', distinct=True),
        )


class Class(models.Model):
    class Meta:
        # 因为 administrative 刚好就在 walking 前捏
        ordering = ("type", "-created", "id")

    """
    注1：所有班级信息统一与Role关联，因为需要区分老师和学生
    """
    id = models.CharField("班级id", primary_key=True, default=create_uuid, editable=False, max_length=8)
    name = models.CharField("班级名称", max_length=6)  # 例如：K2111
    """
    注2：关于数据如何获得，只能是由班上的同学自己填写，那么班级数据如何填写？
    一个思路是采用一次性权限代码，管理员给一个代码，用户输入就可以获得暂时的修改权限，这个有点难办哈
    目前还是使用设置管理员的形式，但是反向关系要与班主任的区分一下
    """
    editors = models.ManyToManyField(User, related_name="edited_classes")

    nickname = models.CharField("班级昵称", max_length=64, blank=True, null=True)  # 可以自己设置
    created = models.PositiveSmallIntegerField("建班年份")
    graduated = models.PositiveSmallIntegerField("毕业年份", null=True)

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
        "account.RoleTeacher", on_delete=models.SET_NULL, null=True, related_name="managed_classes",
        verbose_name="班主任"
    )
    # 储存照片
    photo = ProcessedImageField(
        verbose_name="班级合照", default=None, null=True, upload_to=class_photo_path,
        format='JPEG', options={'quality': 100}
    )
    photo_preview = ImageSpecField(
        source='photo', processors=[ResizeToFill(1800, 1200)], format='JPEG', options={'quality': 100}
    )

    photo_desc = models.TextField("班级合照人员说明", blank=True, null=True, default=None)

    # 去向统计地图名字
    map = models.FileField(verbose_name="地图json数据", upload_to=map_path, null=True, default=None)

    EDITABLE_FIELDS = [
        "name", "nickname", "created", "graduated", "description", "photo_desc"
    ]
    REQUIRED_FIELDS = [
        "name", "created", "type", "headteacher"
    ]

    PUBLIC_SIMPLE_FIELDS = [
        "id", "name", "nickname", "type",
        "created", "graduated", "headteacher",
        "teacher_count", "student_count"
    ]
    PUBLIC_FIELDS = PUBLIC_SIMPLE_FIELDS + [
        "description"
    ]
    ALL_FIELDS = PUBLIC_FIELDS + [
        "students", "teachers",
        "photo", "photo_preview", "photo_desc",
    ]

    objects = ClassManager()

    # 去向统计部分
    def get_map_geojson(self):
        """

        :return:
        """

        def get_students(city_name) -> QuerySet[RoleStudent]:
            _students = self.students.filter(city__name=city_name)
            return _students

        # 四个直辖市和两个特别行政区
        special_adcodes = [
            "310000",  # 上海市
            "500000",  # 重庆市
            "810000",  # 香港特别行政区
            "820000",  # 澳门特别行政区
            "110000",  # 北京市
        ]
        _map, points = ({"type": "FeatureCollection", "features": []},
                        {"type": "FeatureCollection", "features": []})
        # 获取中国边界信息
        country = get_district(100000)
        # feature_collection["features"].append(district_to_feature(country))
        # print("country")
        for district in country["districts"]:
            # print("province", district["name"])
            # 省级行政单位
            if district["adcode"] in special_adcodes:
                # 如果是特别行政区
                students = get_students(district["name"])
                if students.count() > 0:
                    # 首先获得中心点Feature
                    center_feature = district_to_feature(district)
                    center_feature["properties"]["province"] = district["name"]
                    center_feature["properties"]["students"] = UserMapSerializer(students, many=True).data
                    center_feature["properties"]["count"] = students.count()
                    points["features"].append(center_feature)
                # 获得轮廓
                all_district = get_district(district["adcode"], 0)
                feature = district_to_feature(all_district)
                feature["properties"]["count"] = students.count()
                _map["features"].append(feature)
            else:
                # 如果是普通省
                province = get_district(district["adcode"])
                count = 0
                for city in province["districts"]:
                    students = get_students(city["name"])
                    if len(students) > 0:
                        count += len(students)
                        feature = district_to_feature(city)
                        feature["properties"]["count"] = students.count()
                        feature["properties"]["students"] = UserMapSerializer(students, many=True).data
                        feature["properties"]["province"] = district["name"]
                        points["features"].append(feature)
                province_feature = district_to_feature(province)
                province_feature["properties"]["count"] = count
                _map["features"].append(province_feature)

        # echarts点必须单独拿出来，所以我这里修改一下分开搞
        return {
            "map": _map,
            "points": points,
        }


class ClassMembership(models.Model):
    class Meta:
        abstract = True

    # 命名不规范，将就一下
    classes = models.ForeignKey(Class, on_delete=models.CASCADE)
    aka = models.TextField("外号", max_length=128, blank=True)  # also known as

    joined = models.DateField("加入时间", null=True, default=None)
    exited = models.DateField("离开时间", null=True, default=None)


class ClassStudent(ClassMembership):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['classes', 'user_role'], name='class_membership_student')
        ]

    user_role = models.ForeignKey("account.RoleStudent", on_delete=models.CASCADE)
    rank = models.CharField("在班级内的“地位”", max_length=1024, blank=True)
    # 班级内的职位
    """
    说明：
    区分走班和行政班，职位的选项不同，ClassOfficer的administrative和walking两个健用于区分
    """
    position = models.ManyToManyField('account.ClassOfficer', verbose_name="职位")
    number = models.PositiveSmallIntegerField("学号", null=True)

    SIMPLE_FIELDS = [
        "number", "rank", "position", "aka"
    ]
    ALL_FIELDS = SIMPLE_FIELDS + [
        "joined", "exited",
    ]
    EDITABLE_FIELDS = [
        "aka", "joined", "exited", "position", "number", "rank"
    ]


class ClassTeacher(ClassMembership):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['classes', 'user_role'], name='class_membership_teacher')
        ]

    user_role = models.ForeignKey("account.RoleTeacher", on_delete=models.CASCADE)
    SIMPLE_FIELDS = ["aka"]

    ALL_FIELDS = SIMPLE_FIELDS + [
        "joined", "exited",
    ]
    EDITABLE_FIELDS = [
        "aka", "joined", "exited",
    ]


class ClassOfficer(models.Model):
    """
    记录班级职务名称，用户通过外键关联职务
    """

    class Meta:
        ordering = ["order"]

    name = models.CharField(max_length=64, primary_key=True)
    administrative = models.BooleanField()
    walking = models.BooleanField()
    # 名字暂定，标记优先顺序
    order = models.PositiveSmallIntegerField(default=50000)
