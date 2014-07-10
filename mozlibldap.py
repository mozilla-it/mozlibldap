#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
# Author: gdestuynder@mozilla.com

import ldap

class MozLDAP(object):
	debug = False

	def __init__(self, url, bind_dn, bind_passwd):
		self.conn = ldap.initialize(url)
		self.conn.simple_bind_s(bind_dn, bind_passwd)
		#might want to restrict to o=com,net,org in some cases
		self.base = "dc=mozilla"

	def _fixdn(self, dn):
		# Auto-fix dn if an email is passed. This is not unique, unlike the dn. In doubt please always use a dn.
		if not dn.startswith("mail="):
			dn = "mail="+dn
		if dn.find(",") != -1:
			raise Exception('InvalidDnFormat', 'Use mail=user, not a fully qualified DN')
		return dn

	def query(self, filterstr, attrlist=None, base=None):
		"""
		desc: wrapper to search_s

		return: ldap resource
		"""
		if base == None:
			base = self.base
		return self.conn.search_s(base, ldap.SCOPE_SUBTREE, filterstr, attrlist)

	def get_user_dn_by_uid(self, uid):
		"""
		desc: search for a user's DN
		res format: [('mail=gdestuynder@mozilla.com,o=com,dc=mozilla', {'uid': ['gdestuynder']})]

		@uid: integer posix uid ex: 1663
		return: str ex: "gdestuynder"
		"""
		res = self.query("uidNumber="+str(uid), ['uid'])
		return res[0][0]


	def get_user_posix_username(self, dn):
		return self.get_user_posix_uid(dn)

	def get_user_posix_uid(self, dn):
		"""
		desc: search for a user's POSIX UID and POSIX username

		@dn str ex: "mail=user" (not fully qualified).
		return: str,int ex: ('gdestuynder', 1663)
		"""
		dn = self._fixdn(dn)
		res = self.query("(&("+dn+")(uidNumber=*))", ['uidNumber', 'uid'])
		return (res[0][1]['uid'][0], int(res[0][1]['uidNumber'][0]))

	def get_user_email(self, dn):
		"""
		desc: search for a user's email

		@dn str ex: "mail=user" (not fully qualified) 
		return: [str] ex: ["gdestuynder@mozilla.com"] (there can be more than one, first entry is the default)
		"""
		dn = self._fixdn(dn)
		res = self.query("("+dn+")", ['mail'])
		return res[0][1]['mail']

	def get_user_attribute(self, dn, attr):
		"""
		desc: generic function to search for a specific user attribute, granted you know the attribute name. Use
		specific functions when available as there's safety filters to ensure you get the result you're looking for, and
		proper typing.

		@dn str ex: "mail=user" (not fully qualified) 
		return: [attr] type unknown
		"""
		dn = self._fixdn(dn)
		res = self.query("("+dn+")", [attr])
		return res[0][1][attr]

	def get_user_attributes(self, dn):
		"""
		desc: search for all user attributes - more resource intensive than dedicated functions! This will return mail,
		uid, ssh keys, picture, shirt size, phone, etc.

		@dn str ex: "mail=user" (not fully qualified) 
		return: {'attr': value, ...}
		"""
		dn = self._fixdn(dn)
		res = self.query("("+dn+")")
		return res[0][1]

	def get_all_enabled_users_attr(self, attr):
		"""
		desc: search for all non-disabled users and return one of their attribute

		@attr str ex: 'sshPublicKey'
		return: ['dn': {'attr': ['attr..']}, ...] (may also return ['dn', {}] if no attr found or empty)
		"""
		res = self.query("(&(!(employeeType=DISABLED))(mail=*))", [attr])
		return res

	def get_all_enabled_users(self):
		"""
		desc: search for all non-disabled users and return the DN.

		return: ['mail=gdestuynder@mozilla.com,o=com,dc=mozilla', 'mail=gdestuynder2@mozilla.com,o=com,dc=mozilla' ...]"""
		res = self.query("(&(!(employeeType=DISABLED))(mail=*))", ['dn'])
		return [x[0] for x in res]

	def get_all_disabled_users(self):
		"""
		desc: like get_all_enabled_users but only return disabled users (inverse function)

		return: ['mail=gdestuynder@mozilla.com,o=com,dc=mozilla', 'mail=gdestuynder2@mozilla.com,o=com,dc=mozilla' ...]"""
		res = self.query("(&(employeeType=DISABLED)(mail=*))", ['dn'])
		return [x[0] for x in res]

	def get_all_groups(self):
		"""
		desc: search for all groups.

		return: ['cn=groupname,ou=groups,dc=mozilla', ...]
		"""
		res = self.query("(cn=*)", ['cn'], base="ou=groups,"+self.base)
		return [x[0] for x in res]
