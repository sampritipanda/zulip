# -*- coding: utf-8 -*-
import os
import sys
import urllib
from django.conf import settings
from libthumbor import CryptoURL

ZULIP_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath('__file__'))))
sys.path.append(ZULIP_PATH)

from zthumbor.loaders.helpers import (
    THUMBOR_S3_TYPE, THUMBOR_LOCAL_FILE_TYPE, THUMBOR_EXTERNAL_TYPE
)
from zerver.lib.camo import get_camo_url

def is_thumbor_enabled() -> bool:
    return settings.THUMBOR_HOST != ''

def get_source_type(url: str) -> str:
    if not url.startswith('user_uploads/'):
        return THUMBOR_EXTERNAL_TYPE

    local_uploads_dir = settings.LOCAL_UPLOADS_DIR
    if local_uploads_dir:
        return THUMBOR_LOCAL_FILE_TYPE
    return THUMBOR_S3_TYPE

def generate_thumbnail_url(path: str, size: str='0x0') -> str:
    if not is_thumbor_enabled():
        if path.startswith('https'):
            return path
        if path.startswith('http'):
            return get_camo_url(path)
        return '/' + path

    # Ignore thumbnailing for static resources.
    if path.startswith('static/'):
        return '/' + path

    source_type = get_source_type(path)
    if source_type == THUMBOR_EXTERNAL_TYPE:
        url = path
    else:
        url = path[len('user_uploads/'):]

    # Hack to get by weird issue with http in path and nginx.
    # We drop url scheme in order to by pass the issue.
    parsed_url = urllib.parse.urlparse(url)
    url = parsed_url.netloc + parsed_url.path
    if url.startswith('/'):
        url = url[1:]

    safe_url = urllib.parse.quote(url)
    image_url = '%s/source_type/%s' % (safe_url, source_type)
    width, height = map(int, size.split('x'))
    crypto = CryptoURL(key=settings.THUMBOR_KEY)
    encrypted_url = crypto.generate(
        width=width,
        height=height,
        smart=True,
        filters=['no_upscale()'],
        image_url=image_url
    )

    thumbnail_url = '/thumbor' + encrypted_url
    if settings.THUMBOR_HOST != '127.0.0.1:9995':
        thumbnail_url = urllib.parse.urljoin(settings.THUMBOR_HOST, thumbnail_url)
    return thumbnail_url
