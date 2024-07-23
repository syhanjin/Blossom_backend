# -*- coding: utf-8 -*-
from account.models.class_ import ClassOfficer

__doc__ = """
构建班级职位列表
""".strip()

__OFFICER_LIST = [
    # (名字, 是否应用于行政班, 是否应用于走班)
    # 班干部
    ("班长", 1, 1, 10000),
    ("副班长", 1, 1, 10001),
    ("学习委员", 1, 0, 10003),
    ("团支书", 1, 0, 10002),
    ("电教委员", 1, 0, 10005),
    ("体育委员", 1, 0, 10004),
    # 课代表
    ("语文课代表", 1, 0, 30001),
    ("数学课代表", 1, 0, 30002),
    ("英语课代表", 1, 0, 30003),
    ("物理课代表", 1, 0, 30004),
    ("化学课代表", 1, 0, 30006),
    ("生物课代表", 1, 0, 30007),
    ("地理课代表", 1, 0, 30009),
    ("政治课代表", 1, 0, 30008),
    ("历史课代表", 1, 0, 30005),
    ("课代表", 0, 1, 30000),
]


def create_officer_list():
    total = 0
    for row in __OFFICER_LIST:
        total += 1
        ClassOfficer.objects.update_or_create(
            name=row[0],
            defaults={"administrative": row[1], "walking": row[2], "order": row[3]},
            create_defaults={"name": row[0], "administrative": row[1], "walking": row[2], "order": row[3]},
        )
    print(f"创建完毕！共{total}条！")
