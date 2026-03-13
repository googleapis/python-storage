import google.auth as ga
import os

from google.auth.compute_engine import _mtls

should_use_mtls = _mtls.should_use_mds_mtls()

mode_str = os.environ.get("GCE_METADATA_MTLS_MODE", "default")

print("Google auth version", ga.__version__)
print("env var  GCE_METADATA_MTLS_MODE", mode_str)
print("does cert files exits", _mtls._certs_exist(_mtls.MdsMtlsConfig()))
print("should_use_mds_mtls", should_use_mtls)
