# -*- coding: utf-8 -*-
from __future__ import absolute_import

from zerver.lib.test_classes import ZulipTestCase
from zerver.models import get_realm, get_realm_by_email_domain, \
    GetRealmByDomainException, RealmAlias
import ujson


class RealmAliasTest(ZulipTestCase):

    def test_list(self):
        # type: () -> None
        self.login("iago@zulip.com")
        realm = get_realm('zulip')
        alias = RealmAlias(realm=realm, domain='zulip.org')
        alias.save()
        result = self.client_get("/json/realm/domains")
        self.assert_json_success(result)
        self.assertEqual(200, result.status_code)
        content = ujson.loads(result.content)
        self.assertEqual(len(content['domains']), 2)

    def test_not_realm_admin(self):
        # type: () -> None
        self.login("hamlet@zulip.com")
        result = self.client_post("/json/realm/domains")
        self.assert_json_error(result, 'Must be a realm administrator')
        result = self.client_delete("/json/realm/domains/15")
        self.assert_json_error(result, 'Must be a realm administrator')

    def test_create(self):
        # type: () -> None
        self.login("iago@zulip.com")
        data = {"domain": ""}
        result = self.client_post("/json/realm/domains", info=data)
        self.assert_json_error(result, 'Domain can\'t be empty.')

        data['domain'] = 'zulip.org'
        result = self.client_post("/json/realm/domains", info=data)
        self.assert_json_success(result)

        result = self.client_post("/json/realm/domains", info=data)
        self.assert_json_error(result, 'A Realm for this domain already exists.')

    def test_delete(self):
        # type: () -> None
        self.login("iago@zulip.com")
        realm = get_realm('zulip')
        alias_id = RealmAlias.objects.create(realm=realm, domain='zulip.org').id
        aliases_count = RealmAlias.objects.count()
        result = self.client_delete("/json/realm/domains/{0}".format(alias_id + 1))
        self.assert_json_error(result, 'No such entry found.')

        result = self.client_delete("/json/realm/domains/{0}".format(alias_id))
        self.assert_json_success(result)
        self.assertEqual(RealmAlias.objects.count(), aliases_count - 1)

    def test_get_realm_by_email_domain(self):
        # type: () -> None
        self.assertEqual(get_realm_by_email_domain('user@zulip.com').string_id, 'zulip')
        self.assertEqual(get_realm_by_email_domain('user@fakedomain.com'), None)
        with self.settings(REALMS_HAVE_SUBDOMAINS = True), (
             self.assertRaises(GetRealmByDomainException)):
            get_realm_by_email_domain('user@zulip.com')
