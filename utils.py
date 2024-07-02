# -*- coding: utf-8 -*-
import shortuuid


def create_uuid(): return shortuuid.ShortUUID(alphabet="0123456789").random(8)
