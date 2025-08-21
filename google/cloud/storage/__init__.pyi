# Stubs for google.cloud.storage package
# Generated minimal PEP 561 stub to improve Pylance/Pyright experience.
from __future__ import annotations

from typing import Any, Optional, MutableMapping, Sequence, Tuple

__all__ = ["__version__", "Batch", "Blob", "Bucket", "Client"]

__version__: str

class Batch:
    def __init__(self, client: "Client", raise_exception: bool = True) -> None: ...

    def finish(self, raise_exception: bool = True) -> Sequence[Tuple[Any, Any]]: ...


class Blob:
    STORAGE_CLASSES: Sequence[str]

    def __init__(
        self,
        name: str,
        bucket: "Bucket",
        chunk_size: Optional[int] = None,
        encryption_key: Optional[bytes] = None,
        kms_key_name: Optional[str] = None,
        generation: Optional[int] = None,
    ) -> None: ...

    name: str
    bucket: "Bucket"
    generation: Optional[int]

    @property
    def public_url(self) -> str: ...

    @property
    def client(self) -> "Client": ...

    def from_uri(self, uri: str) -> "Blob": ...

    def download_as_bytes(self, timeout: Optional[float] = ...) -> bytes: ...

    def upload_from_file(self, file_obj: Any, timeout: Optional[float] = ...) -> None: ...


class Bucket:
    STORAGE_CLASSES: Sequence[str]

    def __init__(
        self,
        client: "Client",
        name: str,
        user_project: Optional[str] = None,
        generation: Optional[int] = None,
    ) -> None: ...

    name: str
    client: "Client"
    user_project: Optional[str]

    def blob(self, blob_name: str, chunk_size: Optional[int] = None) -> Blob: ...

    def get_blob(self, blob_name: str, timeout: Optional[float] = ...) -> Optional[Blob]: ...

    def create(self, timeout: Optional[float] = ...) -> None: ...

    @classmethod
    def from_string(cls, uri: str, client: Optional["Client"] = ...) -> "Bucket": ...


class Client:
    SCOPE: Sequence[str]

    def __init__(
        self,
        project: Optional[str] = ...,
        credentials: Optional[Any] = ...,
        _http: Optional[Any] = ...,
        client_info: Optional[Any] = ...,
        client_options: Optional[Any] = ...,
        use_auth_w_custom_endpoint: bool = True,
        extra_headers: Optional[MutableMapping[str, str]] = ..., *, api_key: Optional[str] = ...,
    ) -> None: ...

    project: Optional[str]

    @classmethod
    def create_anonymous_client(cls) -> "Client": ...

    @property
    def universe_domain(self) -> str: ...

    @property
    def api_endpoint(self) -> str: ...

    @property
    def current_batch(self) -> Optional[Batch]: ...

    def bucket(self, bucket_name: str, user_project: Optional[str] = None, generation: Optional[int] = None) -> Bucket: ...

    def batch(self, raise_exception: bool = True) -> Batch: ...

    def get_service_account_email(self, project: Optional[str] = None, timeout: Optional[float] = ..., retry: Optional[Any] = ...) -> str: ...
