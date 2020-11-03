#!/usr/bin/env python3
#
#  repo.py
"""
Modified Dulwich repository object.

.. versionadded:: 0.3.0
"""
#
#  Copyright © 2020 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#
#  get_user_identity and Repo based on https://github.com/dulwich/dulwich
#  Copyright (C) 2013 Jelmer Vernooij <jelmer@jelmer.uk>
#  |  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  |  not use this file except in compliance with the License. You may obtain
#  |  a copy of the License at
#  |
#  |	  http://www.apache.org/licenses/LICENSE-2.0
#  |
#  |  Unless required by applicable law or agreed to in writing, software
#  |  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  |  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  |  License for the specific language governing permissions and limitations
#  |  under the License.
#

# stdlib
import os
from typing import Any, Optional, Union

# 3rd party
from dulwich import repo
from dulwich.config import StackedConfig

__all__ = ["get_user_identity", "Repo"]


def get_user_identity(config: StackedConfig, kind: Optional[str] = None) -> bytes:
	"""
	Determine the identity to use for new commits.

	If kind is set, this first checks
	:envvar:`GIT_${KIND}_NAME` and :envvar:`GIT_${KIND}_EMAIL`.

	If those variables are not set, then it will fall back
	to reading the ``user.name`` and ``user.email`` settings from
	the specified configuration.

	If that also fails, then it will fall back to using
	the current users' identity as obtained from the host
	system (e.g. the gecos field, $EMAIL, $USER@$(hostname -f).

	:param config:
	:param kind: Optional kind to return identity for, usually either ``'AUTHOR'`` or ``'COMMITTER'``.

	:returns: A user identity
	"""

	user: Optional[bytes] = None
	email: Optional[bytes] = None

	if kind:
		user_uc = os.environ.get("GIT_" + kind + "_NAME")
		if user_uc is not None:
			user = user_uc.encode('utf-8')
		email_uc = os.environ.get("GIT_" + kind + "_EMAIL")
		if email_uc is not None:
			email = email_uc.encode('utf-8')

	if user is None:
		try:
			user = config.get(("user", ), "name")
		except KeyError:
			user = None

	if email is None:
		try:
			email = config.get(("user", ), "email")
		except KeyError:
			email = None

	if user is None or email is None:
		default_user, default_email = repo._get_default_identity()  # type: ignore

		if user is None:
			user = default_user.encode('utf-8')
		if email is None:
			email = default_email.encode('utf-8')

	if email.startswith(b'<') and email.endswith(b'>'):
		email = email[1:-1]

	return user + b" <" + email + b">"


class Repo(repo.Repo):
	"""
	Modified Dulwich repository object.

	A git repository backed by local disk.

	To open an existing repository, call the contructor with
	the path of the repository.

	To create a new repository, use the Repo.init class method.

	:param root:
	"""

	def do_commit(
			self,
			message: Optional[Union[str, bytes]] = None,
			committer: Optional[Union[str, bytes]] = None,
			author: Optional[Union[str, bytes]] = None,
			commit_timestamp: Optional[float] = None,
			commit_timezone: Optional[float] = None,
			author_timestamp: Optional[float] = None,
			author_timezone: Optional[float] = None,
			tree: Optional[Any] = None,
			encoding: Optional[Union[str, bytes]] = None,
			ref: bytes = b'HEAD',
			merge_heads: Optional[Any] = None
			) -> bytes:
		"""
		Create a new commit.

		If not specified, `committer` and `author` default to
		:func:`get_user_identity(..., 'COMMITTER') <.get_user_identity>`
		and :func:`get_user_identity(..., 'AUTHOR') <.get_user_identity>` respectively.

		:param message: Commit message
		:param committer: Committer fullname
		:param author: Author fullname
		:param commit_timestamp: Commit timestamp (defaults to now)
		:param commit_timezone: Commit timestamp timezone (defaults to GMT)
		:param author_timestamp: Author timestamp (defaults to commit timestamp)
		:param author_timezone: Author timestamp timezone (defaults to commit timestamp timezone)
		:param tree: SHA1 of the tree root to use (if not specified the current index will be committed).
		:param encoding: Encoding
		:param ref: Optional ref to commit to (defaults to current branch)
		:param merge_heads: Merge heads (defaults to .git/MERGE_HEADS)

		:returns: New commit SHA1
		"""

		config = self.get_config_stack()

		if committer is None:
			committer = get_user_identity(config, kind='COMMITTER')

		if author is None:
			author = get_user_identity(config, kind='AUTHOR')

		return super().do_commit(  # type: ignore
			message=message,
			committer=committer,
			author=author,
			commit_timestamp=commit_timestamp,
			commit_timezone=commit_timezone,
			author_timestamp=author_timestamp,
			author_timezone=author_timezone,
			tree=tree,
			encoding=encoding,
			ref=ref,
			merge_heads=merge_heads,
			)
