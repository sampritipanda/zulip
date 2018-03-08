from __future__ import absolute_import

from six.moves import urllib
from tornado.concurrent import return_future
from thumbor.loaders import LoaderResult, file_loader, https_loader
from tc_aws.loaders import s3_loader
from thumbor.context import Context
from .helpers import (
    separate_url_and_source_type, change_url_scheme_to_http,
    THUMBOR_S3_TYPE, THUMBOR_LOCAL_FILE_TYPE, THUMBOR_EXTERNAL_TYPE
)

from typing import Any, Callable

def get_not_found_result():
    # type: () -> LoaderResult
    result = LoaderResult()
    result.error = LoaderResult.ERROR_NOT_FOUND
    result.successful = False
    return result

@return_future
def load(context, url, callback):
    # type: (Context, str, Callable[..., Any]) -> None
    url = urllib.parse.unquote(url)
    source_type, actual_url = separate_url_and_source_type(url)
    if source_type not in (THUMBOR_S3_TYPE, THUMBOR_LOCAL_FILE_TYPE,
                           THUMBOR_EXTERNAL_TYPE):
        callback(get_not_found_result())
        return

    def maybe_perform_pre_callback_actions(result):
        # type: (LoaderResult) -> None
        if result.successful:
            callback(result)
        elif source_type == THUMBOR_EXTERNAL_TYPE:
            http_url = change_url_scheme_to_http(actual_url)
            https_loader.load(context, http_url, callback)
        else:
            callback(result)

    if source_type == THUMBOR_S3_TYPE:
        s3_loader.load(context, actual_url, callback)
    elif source_type == THUMBOR_LOCAL_FILE_TYPE:
        patched_local_url = 'files/' + actual_url
        file_loader.load(context, patched_local_url, callback)
    elif source_type == THUMBOR_EXTERNAL_TYPE:
        https_loader.load(context, actual_url, maybe_perform_pre_callback_actions)
