# -*- coding: utf-8 -*-
import pandas as pd

from destination.models import City, School


def load_cities(fp="cities.csv"):
    cities = pd.read_csv(fp)
    for index, row in cities.iterrows():
        City.objects.update_or_create(
            name=row["name"],
            defaults={
                "adcode": row["adcode"],
            },
            create_defaults={
                "name": row["name"],
                "adcode": row["adcode"]
            }
        )


def load_schools(fp="schools.csv"):
    schools = pd.read_csv(fp)
    for index, row in schools.iterrows():
        print(row["学校名称"], row["所在地"])
        city = City.objects.get(name=row["所在地"])
        School.objects.update_or_create(
            id=row["学校标识码"],
            defaults={
                "name": row["学校名称"],
                "city": city
            },
            create_defaults={
                "id": row["学校标识码"],
                "name": row["学校名称"],
                "city": city
            }
        )
