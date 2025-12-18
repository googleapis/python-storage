import google_crc32c

from google.api_core import exceptions

def raise_if_no_fast_crc32c():
    """Check if the C-accelerated version of google-crc32c is available.

    If not, raise an error to prevent silent performance degradation.
    
    raises google.api_core.exceptions.NotFound: If the C extension is not available.
    returns: True if the C extension is available.
    rtype: bool
    
    """
    if google_crc32c.implementation != "c":
        raise exceptions.NotFound(
            "The google-crc32c package is not installed with C support. "
            "Bidi reads require the C extension for data integrity checks."
            "For more information, see https://github.com/googleapis/python-crc32c."
        )
