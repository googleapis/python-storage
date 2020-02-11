# Copyright 2014 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Manipulate access control lists that Cloud Storage provides.

:class:`google.cloud.storage.bucket.Bucket` has a getting method that creates
an ACL object under the hood, and you can interact with that using
:func:`google.cloud.storage.bucket.Bucket.acl`:

.. literalinclude:: snippets.py
    :start-after: [START client_bucket_acl]
    :end-before: [END client_bucket_acl]


Adding and removing permissions can be done with the following methods
(in increasing order of granularity):

- :func:`ACL.all`
  corresponds to access for all users.
- :func:`ACL.all_authenticated` corresponds
  to access for all users that are signed into a Google account.
- :func:`ACL.domain` corresponds to access on a
  per Google Apps domain (ie, ``example.com``).
- :func:`ACL.group` corresponds to access on a
  per group basis (either by ID or e-mail address).
- :func:`ACL.user` corresponds to access on a
  per user basis (either by ID or e-mail address).

And you are able to ``grant`` and ``revoke`` the following roles:

- **Reading**:
  :func:`_ACLEntity.grant_read` and :func:`_ACLEntity.revoke_read`
- **Writing**:
  :func:`_ACLEntity.grant_write` and :func:`_ACLEntity.revoke_write`
- **Owning**:
  :func:`_ACLEntity.grant_owner` and :func:`_ACLEntity.revoke_owner`

You can use any of these like any other factory method (these happen to
be :class:`_ACLEntity` factories):

.. literalinclude:: snippets.py
   :start-after: [START acl_user_settings]
   :end-before: [END acl_user_settings]

After that, you can save any changes you make with the
:func:`google.cloud.storage.acl.ACL.save` method:

.. literalinclude:: snippets.py
   :start-after: [START acl_save]
   :end-before: [END acl_save]

You can alternatively save any existing :class:`google.cloud.storage.acl.ACL`
object (whether it was created by a factory method or not) from a
:class:`google.cloud.storage.bucket.Bucket`:

.. literalinclude:: snippets.py
   :start-after: [START acl_save_bucket]
   :end-before: [END acl_save_bucket]

To get the list of ``entity`` and ``role`` for each unique pair, the
:class:`ACL` class is iterable:

.. literalinclude:: snippets.py
   :start-after: [START acl_print]
   :end-before: [END acl_print]

This list of tuples can be used as the ``entity`` and ``role`` fields
when sending metadata for ACLs to the API.
"""

from google.cloud.storage.constants import _DEFAULT_TIMEOUT


class _ACLEntity(object):
    """Class representing a set of roles for an entity.

    This is a helper class that you likely won't ever construct
    outside of using the factor methods on the :class:`ACL` object.

    :type entity_type: str
    :param entity_type: The type of entity (ie, 'group' or 'user').

    :type identifier: str
    :param identifier: The ID or e-mail of the entity. For the special
                       entity types (like 'allUsers') this is optional.
    """

    READER_ROLE = "READER"
    WRITER_ROLE = "WRITER"
    OWNER_ROLE = "OWNER"

    def __init__(self, entity_type, identifier=None):
        self.identifier = identifier
        self.roles = set([])
        self.type = entity_type

    def __str__(self):
        if not self.identifier:
            return str(self.type)
        else:
            return "{acl.type}-{acl.identifier}".format(acl=self)

    def __repr__(self):
        return "<ACL Entity: {acl} ({roles})>".format(
            acl=self, roles=", ".join(self.roles)
        )

    def get_roles(self):
        """Get the list of roles permitted by this entity.

        :rtype: list of strings
        :returns: The list of roles associated with this entity.
        """
        return self.roles

    def grant(self, role):
        """Add a role to the entity.

        :type role: str
        :param role: The role to add to the entity.
        """
        self.roles.add(role)

    def revoke(self, role):
        """Remove a role from the entity.

        :type role: str
        :param role: The role to remove from the entity.
        """
        if role in self.roles:
            self.roles.remove(role)

    def grant_read(self):
        """Grant read access to the current entity."""
        self.grant(_ACLEntity.READER_ROLE)

    def grant_write(self):
        """Grant write access to the current entity."""
        self.grant(_ACLEntity.WRITER_ROLE)

    def grant_owner(self):
        """Grant owner access to the current entity."""
        self.grant(_ACLEntity.OWNER_ROLE)

    def revoke_read(self):
        """Revoke read access from the current entity."""
        self.revoke(_ACLEntity.READER_ROLE)

    def revoke_write(self):
        """Revoke write access from the current entity."""
        self.revoke(_ACLEntity.WRITER_ROLE)

    def revoke_owner(self):
        """Revoke owner access from the current entity."""
        self.revoke(_ACLEntity.OWNER_ROLE)


class ACL(object):
    """Container class representing a list of access controls."""

    _URL_PATH_ELEM = "acl"
    _PREDEFINED_QUERY_PARAM = "predefinedAcl"

    PREDEFINED_XML_ACLS = {
        # XML API name -> JSON API name
        "project-private": "projectPrivate",
        "public-read": "publicRead",
        "public-read-write": "publicReadWrite",
        "authenticated-read": "authenticatedRead",
        "bucket-owner-read": "bucketOwnerRead",
        "bucket-owner-full-control": "bucketOwnerFullControl",
    }

    PREDEFINED_JSON_ACLS = frozenset(
        [
            "private",
            "projectPrivate",
            "publicRead",
            "publicReadWrite",
            "authenticatedRead",
            "bucketOwnerRead",
            "bucketOwnerFullControl",
        ]
    )
    """See
    https://cloud.google.com/storage/docs/access-control/lists#predefined-acl
    """

    loaded = False

    # Subclasses must override to provide these attributes (typically,
    # as properties).
    reload_path = None
    save_path = None
    user_project = None

    def __init__(self):
        self.entities = {}

    def _ensure_loaded(self, timeout=_DEFAULT_TIMEOUT):
        """Load if not already loaded.

        :type timeout: float or tuple
        :param timeout: (optional) The amount of time, in seconds, to wait
            for the server response.

            Can also be passed as a tuple (connect_timeout, read_timeout).
            See :meth:`requests.Session.request` documentation for details.
        """
        if not self.loaded:
            self.reload(timeout=timeout)

    @classmethod
    def validate_predefined(cls, predefined):
        """Ensures predefined is in list of predefined json values

        :type predefined: str
        :param predefined: name of a predefined acl

        :type predefined: str
        :param predefined: validated JSON name of predefined acl

        :raises: :exc: `ValueError`: If predefined is not a valid acl
        """
        predefined = cls.PREDEFINED_XML_ACLS.get(predefined, predefined)
        if predefined and predefined not in cls.PREDEFINED_JSON_ACLS:
            raise ValueError("Invalid predefined ACL: %s" % (predefined,))
        return predefined

    def reset(self):
        """Remove all entities from the ACL, and clear the ``loaded`` flag."""
        self.entities.clear()
        self.loaded = False

    def __iter__(self):
        self._ensure_loaded()

        for entity in self.entities.values():
            for role in entity.get_roles():
                if role:
                    yield {"entity": str(entity), "role": role}

    def entity_from_dict(self, entity_dict):
        """Build an _ACLEntity object from a dictionary of data.

        An entity is a mutable object that represents a list of roles
        belonging to either a user or group or the special types for all
        users and all authenticated users.

        :type entity_dict: dict
        :param entity_dict: Dictionary full of data from an ACL lookup.

        :rtype: :class:`_ACLEntity`
        :returns: An Entity constructed from the dictionary.
        """
        entity = entity_dict["entity"]
        role = entity_dict["role"]

        if entity == "allUsers":
            entity = self.all()

        elif entity == "allAuthenticatedUsers":
            entity = self.all_authenticated()

        elif "-" in entity:
            entity_type, identifier = entity.split("-", 1)
            entity = self.entity(entity_type=entity_type, identifier=identifier)

        if not isinstance(entity, _ACLEntity):
            raise ValueError("Invalid dictionary: %s" % entity_dict)

        entity.grant(role)
        return entity

    def has_entity(self, entity):
        """Returns whether or not this ACL has any entries for an entity.

        :type entity: :class:`_ACLEntity`
        :param entity: The entity to check for existence in this ACL.

        :rtype: bool
        :returns: True of the entity exists in the ACL.
        """
        self._ensure_loaded()
        return str(entity) in self.entities

    def get_entity(self, entity, default=None):
        """Gets an entity object from the ACL.

        :type entity: :class:`_ACLEntity` or string
        :param entity: The entity to get lookup in the ACL.

        :type default: anything
        :param default: This value will be returned if the entity
                        doesn't exist.

        :rtype: :class:`_ACLEntity`
        :returns: The corresponding entity or the value provided
                  to ``default``.
        """
        self._ensure_loaded()
        return self.entities.get(str(entity), default)

    def add_entity(self, entity):
        """Add an entity to the ACL.

        :type entity: :class:`_ACLEntity`
        :param entity: The entity to add to this ACL.
        """
        self._ensure_loaded()
        self.entities[str(entity)] = entity

    def entity(self, entity_type, identifier=None):
        """Factory method for creating an Entity.

        If an entity with the same type and identifier already exists,
        this will return a reference to that entity.  If not, it will
        create a new one and add it to the list of known entities for
        this ACL.

        :type entity_type: str
        :param entity_type: The type of entity to create
                            (ie, ``user``, ``group``, etc)

        :type identifier: str
        :param identifier: The ID of the entity (if applicable).
                           This can be either an ID or an e-mail address.

        :rtype: :class:`_ACLEntity`
        :returns: A new Entity or a reference to an existing identical entity.
        """
        entity = _ACLEntity(entity_type=entity_type, identifier=identifier)
        if self.has_entity(entity):
            entity = self.get_entity(entity)
        else:
            self.add_entity(entity)
        return entity

    def user(self, identifier):
        """Factory method for a user Entity.

        :type identifier: str
        :param identifier: An id or e-mail for this particular user.

        :rtype: :class:`_ACLEntity`
        :returns: An Entity corresponding to this user.
        """
        return self.entity("user", identifier=identifier)

    def group(self, identifier):
        """Factory method for a group Entity.

        :type identifier: str
        :param identifier: An id or e-mail for this particular group.

        :rtype: :class:`_ACLEntity`
        :returns: An Entity corresponding to this group.
        """
        return self.entity("group", identifier=identifier)

    def domain(self, domain):
        """Factory method for a domain Entity.

        :type domain: str
        :param domain: The domain for this entity.

        :rtype: :class:`_ACLEntity`
        :returns: An entity corresponding to this domain.
        """
        return self.entity("domain", identifier=domain)

    def all(self):
        """Factory method for an Entity representing all users.

        :rtype: :class:`_ACLEntity`
        :returns: An entity representing all users.
        """
        return self.entity("allUsers")

    def all_authenticated(self):
        """Factory method for an Entity representing all authenticated users.

        :rtype: :class:`_ACLEntity`
        :returns: An entity representing all authenticated users.
        """
        return self.entity("allAuthenticatedUsers")

    def get_entities(self):
        """Get a list of all Entity objects.

        :rtype: list of :class:`_ACLEntity` objects
        :returns: A list of all Entity objects.
        """
        self._ensure_loaded()
        return list(self.entities.values())

    @property
    def client(self):
        """Abstract getter for the object client."""
        raise NotImplementedError

    def _require_client(self, client):
        """Check client or verify over-ride.

        :type client: :class:`~google.cloud.storage.client.Client` or
                      ``NoneType``
        :param client: the client to use.  If not passed, falls back to the
                       ``client`` stored on the current ACL.

        :rtype: :class:`google.cloud.storage.client.Client`
        :returns: The client passed in or the currently bound client.
        """
        if client is None:
            client = self.client
        return client

    def reload(self, client=None, timeout=_DEFAULT_TIMEOUT):
        """Reload the ACL data from Cloud Storage.

        If :attr:`user_project` is set, bills the API request to that project.

        :type client: :class:`~google.cloud.storage.client.Client` or
                      ``NoneType``
        :param client: Optional. The client to use.  If not passed, falls back
                       to the ``client`` stored on the ACL's parent.
        :type timeout: float or tuple
        :param timeout: (optional) The amount of time, in seconds, to wait
            for the server response.

            Can also be passed as a tuple (connect_timeout, read_timeout).
            See :meth:`requests.Session.request` documentation for details.
        """
        path = self.reload_path
        client = self._require_client(client)
        query_params = {}

        if self.user_project is not None:
            query_params["userProject"] = self.user_project

        self.entities.clear()

        found = client._connection.api_request(
            method="GET", path=path, query_params=query_params, timeout=timeout
        )
        self.loaded = True
        for entry in found.get("items", ()):
            self.add_entity(self.entity_from_dict(entry))

    def _save(self, acl, predefined, client, timeout=_DEFAULT_TIMEOUT):
        """Helper for :meth:`save` and :meth:`save_predefined`.

        :type acl: :class:`google.cloud.storage.acl.ACL`, or a compatible list.
        :param acl: The ACL object to save.  If left blank, this will save
                    current entries.

        :type predefined: str
        :param predefined:
            (Optional) An identifier for a predefined ACL.  Must be one of the
            keys in :attr:`PREDEFINED_JSON_ACLS` If passed, `acl` must be None.

        :type client: :class:`~google.cloud.storage.client.Client` or
                      ``NoneType``
        :param client: Optional. The client to use.  If not passed, falls back
                       to the ``client`` stored on the ACL's parent.
        :type timeout: float or tuple
        :param timeout: (optional) The amount of time, in seconds, to wait
            for the server response.

            Can also be passed as a tuple (connect_timeout, read_timeout).
            See :meth:`requests.Session.request` documentation for details.
        """
        query_params = {"projection": "full"}
        if predefined is not None:
            acl = []
            query_params[self._PREDEFINED_QUERY_PARAM] = predefined

        if self.user_project is not None:
            query_params["userProject"] = self.user_project

        path = self.save_path
        client = self._require_client(client)

        result = client._connection.api_request(
            method="PATCH",
            path=path,
            data={self._URL_PATH_ELEM: list(acl)},
            query_params=query_params,
            timeout=timeout,
        )
        self.entities.clear()
        for entry in result.get(self._URL_PATH_ELEM, ()):
            self.add_entity(self.entity_from_dict(entry))
        self.loaded = True

    def save(self, acl=None, client=None, timeout=_DEFAULT_TIMEOUT):
        """Save this ACL for the current bucket.

        If :attr:`user_project` is set, bills the API request to that project.

        :type acl: :class:`google.cloud.storage.acl.ACL`, or a compatible list.
        :param acl: The ACL object to save.  If left blank, this will save
                    current entries.

        :type client: :class:`~google.cloud.storage.client.Client` or
                      ``NoneType``
        :param client: Optional. The client to use.  If not passed, falls back
                       to the ``client`` stored on the ACL's parent.
        :type timeout: float or tuple
        :param timeout: (optional) The amount of time, in seconds, to wait
            for the server response.

            Can also be passed as a tuple (connect_timeout, read_timeout).
            See :meth:`requests.Session.request` documentation for details.
        """
        if acl is None:
            acl = self
            save_to_backend = acl.loaded
        else:
            save_to_backend = True

        if save_to_backend:
            self._save(acl, None, client, timeout=timeout)

    def save_predefined(self, predefined, client=None, timeout=_DEFAULT_TIMEOUT):
        """Save this ACL for the current bucket using a predefined ACL.

        If :attr:`user_project` is set, bills the API request to that project.

        :type predefined: str
        :param predefined: An identifier for a predefined ACL.  Must be one
                           of the keys in :attr:`PREDEFINED_JSON_ACLS`
                           or :attr:`PREDEFINED_XML_ACLS` (which will be
                           aliased to the corresponding JSON name).
                           If passed, `acl` must be None.

        :type client: :class:`~google.cloud.storage.client.Client` or
                      ``NoneType``
        :param client: Optional. The client to use.  If not passed, falls back
                       to the ``client`` stored on the ACL's parent.
        :type timeout: float or tuple
        :param timeout: (optional) The amount of time, in seconds, to wait
            for the server response.

            Can also be passed as a tuple (connect_timeout, read_timeout).
            See :meth:`requests.Session.request` documentation for details.
        """
        predefined = self.validate_predefined(predefined)
        self._save(None, predefined, client, timeout=timeout)

    def clear(self, client=None, timeout=_DEFAULT_TIMEOUT):
        """Remove all ACL entries.

        If :attr:`user_project` is set, bills the API request to that project.

        Note that this won't actually remove *ALL* the rules, but it
        will remove all the non-default rules.  In short, you'll still
        have access to a bucket that you created even after you clear
        ACL rules with this method.

        :type client: :class:`~google.cloud.storage.client.Client` or
                      ``NoneType``
        :param client: Optional. The client to use.  If not passed, falls back
                       to the ``client`` stored on the ACL's parent.
        :type timeout: float or tuple
        :param timeout: (optional) The amount of time, in seconds, to wait
            for the server response.

            Can also be passed as a tuple (connect_timeout, read_timeout).
            See :meth:`requests.Session.request` documentation for details.
        """
        self.save([], client=client, timeout=timeout)


class BucketACL(ACL):
    """An ACL specifically for a bucket.

    :type bucket: :class:`google.cloud.storage.bucket.Bucket`
    :param bucket: The bucket to which this ACL relates.
    """

    def __init__(self, bucket):
        super(BucketACL, self).__init__()
        self.bucket = bucket

    @property
    def client(self):
        """The client bound to this ACL's bucket."""
        return self.bucket.client

    @property
    def reload_path(self):
        """Compute the path for GET API requests for this ACL."""
        return "%s/%s" % (self.bucket.path, self._URL_PATH_ELEM)

    @property
    def save_path(self):
        """Compute the path for PATCH API requests for this ACL."""
        return self.bucket.path

    @property
    def user_project(self):
        """Compute the user project charged for API requests for this ACL."""
        return self.bucket.user_project


class DefaultObjectACL(BucketACL):
    """A class representing the default object ACL for a bucket."""

    _URL_PATH_ELEM = "defaultObjectAcl"
    _PREDEFINED_QUERY_PARAM = "predefinedDefaultObjectAcl"


class ObjectACL(ACL):
    """An ACL specifically for a Cloud Storage object / blob.

    :type blob: :class:`google.cloud.storage.blob.Blob`
    :param blob: The blob that this ACL corresponds to.
    """

    def __init__(self, blob):
        super(ObjectACL, self).__init__()
        self.blob = blob

    @property
    def client(self):
        """The client bound to this ACL's blob."""
        return self.blob.client

    @property
    def reload_path(self):
        """Compute the path for GET API requests for this ACL."""
        return "%s/acl" % self.blob.path

    @property
    def save_path(self):
        """Compute the path for PATCH API requests for this ACL."""
        return self.blob.path

    @property
    def user_project(self):
        """Compute the user project charged for API requests for this ACL."""
        return self.blob.user_project
