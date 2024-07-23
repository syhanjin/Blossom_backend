# -*- coding: utf-8 -*-
import os
import uuid

import shortuuid


def create_uuid(): return shortuuid.ShortUUID(alphabet="0123456789").random(8)


def file_path_getter(upload_to, instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join(upload_to, filename)
