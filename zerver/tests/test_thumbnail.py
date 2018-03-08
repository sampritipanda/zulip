# -*- coding: utf-8 -*-
from django.conf import settings

from zerver.lib.test_classes import ZulipTestCase, UploadSerializeMixin
from zerver.lib.test_helpers import use_s3_backend, override_settings

from io import StringIO
from boto.s3.connection import S3Connection
import ujson
import urllib

class ThumbnailTest(ZulipTestCase):

    @use_s3_backend
    @override_settings(THUMBOR_HOST='127.0.0.1:9995')
    def test_s3_source_type(self) -> None:
        def get_file_path_urlpart(uri: str, size: str='') -> str:
            base = '/user_uploads/'
            url_in_result = 'smart/%s/source_type/s3'
            if size:
                url_in_result = '/%s/%s' % (size, url_in_result)
            upload_file_path = urllib.parse.quote(uri[len(base):])
            return url_in_result % (upload_file_path)

        conn = S3Connection(settings.S3_KEY, settings.S3_SECRET_KEY)
        conn.create_bucket(settings.S3_AUTH_UPLOADS_BUCKET)

        self.login(self.example_email("hamlet"))
        fp = StringIO("zulip!")
        fp.name = "zulip.jpeg"

        result = self.client_post("/json/user_uploads", {'file': fp})
        self.assert_json_success(result)
        json = ujson.loads(result.content)
        self.assertIn("uri", json)
        uri = json["uri"]
        base = '/user_uploads/'
        self.assertEqual(base, uri[:len(base)])

        # Test original image size.
        result = self.client_get("/thumbnail%s?size=original" % (uri))
        self.assertEqual(result.status_code, 302, result)
        expected_part_url = get_file_path_urlpart(uri)
        self.assertIn(expected_part_url, result.url)

        # Test thumbnail size.
        result = self.client_get("/thumbnail%s?size=thumbnail" % (uri))
        self.assertEqual(result.status_code, 302, result)
        expected_part_url = get_file_path_urlpart(uri, '0x100')
        self.assertIn(expected_part_url, result.url)

        # Test with another user trying to access image using thumbor.
        self.logout()
        self.login(self.example_email("iago"))
        result = self.client_get("/thumbnail%s?size=original" % (uri))
        self.assertEqual(result.status_code, 403, result)
        self.assert_in_response("You are not authorized to view this file.", result)

    @override_settings(THUMBOR_HOST='127.0.0.1:9995')
    def test_external_source_type(self) -> None:
        def run_test_with_image_url(image_url: str) -> None:
            # Test original image size.
            result = self.client_get("/thumbnail/%s?size=original" % (image_url))
            self.assertEqual(result.status_code, 302, result)
            expected_part_url = '/smart/images.foobar.com/12345/source_type/external'
            self.assertIn(expected_part_url, result.url)

            # Test thumbnail size.
            result = self.client_get("/thumbnail/%s?size=thumbnail" % (image_url))
            self.assertEqual(result.status_code, 302, result)
            expected_part_url = '/0x100/smart/images.foobar.com/12345/source_type/external'
            self.assertIn(expected_part_url, result.url)

            # Test with another user trying to access image using thumbor.
            # File should be always accessible to user in case of external source
            self.logout()
            self.login(self.example_email("iago"))
            result = self.client_get("/thumbnail/%s?size=original" % (image_url))
            self.assertEqual(result.status_code, 302, result)
            expected_part_url = '/smart/images.foobar.com/12345/source_type/external'
            self.assertIn(expected_part_url, result.url)

        self.login(self.example_email("hamlet"))

        # We are using different urls with only difference in host protocol
        # with the difference of double forward slash because nginx has doesn't
        # work great with 'http' mentioned in path of a url. So we make sure we
        # handle things here fine.
        image_url = 'https://images.foobar.com/12345'
        run_test_with_image_url(image_url)

        image_url = 'http://images.foobar.com/12345'
        run_test_with_image_url(image_url)

        image_url = 'https:/images.foobar.com/12345'
        run_test_with_image_url(image_url)

        image_url = 'http:/images.foobar.com/12345'
        run_test_with_image_url(image_url)

    @override_settings(THUMBOR_HOST='127.0.0.1:9995')
    def test_local_file_type(self) -> None:
        def get_file_path_urlpart(uri: str, size: str='') -> str:
            base = '/user_uploads/'
            url_in_result = 'smart/%s/source_type/local_file'
            if size:
                url_in_result = '/%s/%s' % (size, url_in_result)
            upload_file_path = urllib.parse.quote(uri[len(base):])
            return url_in_result % (upload_file_path)

        self.login(self.example_email("hamlet"))
        fp = StringIO("zulip!")
        fp.name = "zulip.jpeg"

        result = self.client_post("/json/user_uploads", {'file': fp})
        self.assert_json_success(result)
        json = ujson.loads(result.content)
        self.assertIn("uri", json)
        uri = json["uri"]
        base = '/user_uploads/'
        self.assertEqual(base, uri[:len(base)])

        # Test original image size.
        result = self.client_get("/thumbnail%s?size=original" % (uri))
        self.assertEqual(result.status_code, 302, result)
        expected_part_url = get_file_path_urlpart(uri)
        self.assertIn(expected_part_url, result.url)

        # Test thumbnail size.
        result = self.client_get("/thumbnail%s?size=thumbnail" % (uri))
        self.assertEqual(result.status_code, 302, result)
        expected_part_url = get_file_path_urlpart(uri, '0x100')
        self.assertIn(expected_part_url, result.url)

        # Test with a unicode filename.
        fp = StringIO("zulip!")
        fp.name = "μένει.jpg"

        result = self.client_post("/json/user_uploads", {'file': fp})
        self.assert_json_success(result)
        json = ujson.loads(result.content)
        self.assertIn("uri", json)
        uri = json["uri"]
        result = self.client_get("/thumbnail%s?size=original" % (uri))
        self.assertEqual(result.status_code, 302, result)
        expected_part_url = get_file_path_urlpart(uri)
        self.assertIn(expected_part_url, result.url)

        # Test with another user trying to access image using thumbor.
        self.logout()
        self.login(self.example_email("iago"))
        result = self.client_get("/thumbnail%s?size=original" % (uri))
        self.assertEqual(result.status_code, 403, result)
        self.assert_in_response("You are not authorized to view this file.", result)

    @override_settings(THUMBOR_HOST='127.0.0.1:9995')
    def test_with_static_files(self) -> None:
        self.login(self.example_email("hamlet"))
        uri = '/static/images/cute/turtle.png'
        result = self.client_get("/thumbnail%s?size=original" % (uri))
        self.assertEqual(result.status_code, 302, result)
        self.assertEqual(uri, result.url)

    def test_with_thumbor_disabled(self) -> None:
        self.login(self.example_email("hamlet"))
        fp = StringIO("zulip!")
        fp.name = "zulip.jpeg"

        result = self.client_post("/json/user_uploads", {'file': fp})
        self.assert_json_success(result)
        json = ujson.loads(result.content)
        self.assertIn("uri", json)
        uri = json["uri"]
        base = '/user_uploads/'
        self.assertEqual(base, uri[:len(base)])

        with self.settings(THUMBOR_HOST=''):
            result = self.client_get("/thumbnail%s?size=original" % (uri))
        self.assertEqual(result.status_code, 302, result)
        self.assertEqual(uri, result.url)

        uri = 'https://www.google.com/images/srpr/logo4w.png'
        with self.settings(THUMBOR_HOST=''):
            result = self.client_get("/thumbnail/%s?size=original" % (uri))
        self.assertEqual(result.status_code, 302, result)
        self.assertEqual(uri, result.url)

        uri = 'http://www.google.com/images/srpr/logo4w.png'
        with self.settings(THUMBOR_HOST=''):
            result = self.client_get("/thumbnail/%s?size=original" % (uri))
        self.assertEqual(result.status_code, 302, result)
        base = 'https://external-content.zulipcdn.net/7b6552b60c635e41e8f6daeb36d88afc4eabde79/687474703a2f2f7777772e676f6f676c652e636f6d2f696d616765732f737270722f6c6f676f34772e706e67'
        self.assertEqual(base, result.url)

    def test_with_different_thumbor_host(self) -> None:
        self.login(self.example_email("hamlet"))
        fp = StringIO("zulip!")
        fp.name = "zulip.jpeg"

        result = self.client_post("/json/user_uploads", {'file': fp})
        self.assert_json_success(result)
        json = ujson.loads(result.content)
        self.assertIn("uri", json)
        uri = json["uri"]
        base = '/user_uploads/'
        self.assertEqual(base, uri[:len(base)])

        with self.settings(THUMBOR_HOST='http://test-thumborhost.com'):
            result = self.client_get("/thumbnail%s?size=original" % (uri))
        self.assertEqual(result.status_code, 302, result)
        base = 'http://test-thumborhost.com/thumbor/'
        self.assertEqual(base, result.url[:len(base)])

    @override_settings(THUMBOR_HOST='127.0.0.1:9995')
    def test_with_different_sizes(self) -> None:
        def get_file_path_urlpart(uri: str, size: str='') -> str:
            base = '/user_uploads/'
            url_in_result = 'smart/%s/source_type/local_file'
            if size:
                url_in_result = '/%s/%s' % (size, url_in_result)
            upload_file_path = urllib.parse.quote(uri[len(base):])
            return url_in_result % (upload_file_path)

        self.login(self.example_email("hamlet"))
        fp = StringIO("zulip!")
        fp.name = "zulip.jpeg"

        result = self.client_post("/json/user_uploads", {'file': fp})
        self.assert_json_success(result)
        json = ujson.loads(result.content)
        self.assertIn("uri", json)
        uri = json["uri"]
        base = '/user_uploads/'
        self.assertEqual(base, uri[:len(base)])

        # Test with size supplied as a query parameter.
        # size=thumbnail should return a 0x100 sized image.
        # size=original should return the original resolution image.
        result = self.client_get("/thumbnail%s?size=thumbnail" % (uri))
        self.assertEqual(result.status_code, 302, result)
        expected_part_url = get_file_path_urlpart(uri, '0x100')
        self.assertIn(expected_part_url, result.url)

        result = self.client_get("/thumbnail%s?size=original" % (uri))
        self.assertEqual(result.status_code, 302, result)
        expected_part_url = get_file_path_urlpart(uri)
        self.assertIn(expected_part_url, result.url)

        # Test with size supplied as a query parameter where size is anything
        # else than original or thumbnail. Result should be an error message.
        result = self.client_get("/thumbnail%s?size=480x360" % (uri))
        self.assertEqual(result.status_code, 403, result)
        self.assert_in_response("Invalid size.", result)

        # Test with no size param supplied. In this case as well we show an
        # error message.
        result = self.client_get("/thumbnail" + uri)
        self.assertEqual(result.status_code, 403, result)
        self.assert_in_response("Invalid size.", result)
