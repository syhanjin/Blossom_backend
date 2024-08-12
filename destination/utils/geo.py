# -*- coding: utf-8 -*-
import json

import httpx
from django.conf import settings as django_settings

from destination.conf import settings

API_BASE_URL = 'https://restapi.amap.com/v3/config/district'

DISTRICTS_DIR = django_settings.BASE_DIR / "destination" / "districts"
# GEOJSON_DIR = django_settings.BASE_DIR / "destination" / "geojson"

# GEOJSON_DIR.mkdir(mode=0o644, exist_ok=True, parents=True)
DISTRICTS_DIR.mkdir(mode=0o644, exist_ok=True, parents=True)


def get_district(adcode, subdistrict=1, extensions="all"):
    """
    获取行政区信息 https://lbs.amap.com/api/webservice/guide/api/district
    :param adcode: 行政图adcode
    :param subdistrict: 设置显示下级行政区级数（行政区级别包括：国家、省/直辖市、市、区/县、乡镇/街道多级数据）
    :param extensions: base:不返回行政区边界坐标点；all:只返回当前查询 district 的边界值
    :return: 行政区的json
    """
    fp = DISTRICTS_DIR / f"{adcode}_{subdistrict}_{extensions}.json"
    if fp.exists():
        return json.loads(fp.read_text())
    resp = httpx.get(API_BASE_URL, params={
        "key": settings.KEY,
        "keywords": adcode,
        "subdistrict": subdistrict,
        "extensions": extensions
    })
    if resp.status_code != 200:
        raise ValueError(resp)
    data = resp.json()
    if data["status"] == 0:
        raise ValueError(data)
    district = data["districts"][0]
    fp.write_text(json.dumps(district))
    return district


def string_to_point(s: str):
    """

    :param s: lon,lat
    :return: [float,float]
    """
    p = s.split(",")
    return float(p[0]), float(p[1])


def polyline_to_multipolygon(polyline: str):
    ret = {
        "type": "MultiPolygon",
        "coordinates": []
    }
    polygons = polyline.split("|")
    for polygon in polygons:
        points = polygon.split(";")
        ret["coordinates"].append([[string_to_point(x) for x in points]])
    return ret


def district_to_feature(district):
    if 'polyline' in district:
        # 如果有边界信息则标记为边界
        geometry = polyline_to_multipolygon(district["polyline"])
    else:
        geometry = {
            "type": "Point",
            "coordinates": string_to_point(district["center"])
        }
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "adcode": district["adcode"],
            "level": district["level"],
            "name": district["name"],
        }
    }


def district_to_feature_collection(district, children=False):
    """
    将高德的district转化为geojson
    :param district: 高德district
    :param children: 是否包含下属地区
    :return: FeatureCollection
    """
    ret = {
        "type": "FeatureCollection",
        "features": []
    }
    # 向FeatureCollection中加入父节点
    ret["features"].append(district_to_feature(district))
    if children:
        for child in district["districts"]:
            ret["features"].append(district_to_feature(child))

    return ret
