import google_crc32c
import base64
import sys

# The file to check
# file_path = 'part_data.bin'
# file_path = "/usr/local/google/home/chandrasiri/checksum/dec8/chunk3"  # Example file path, replace with your actual file
file_path = sys.argv[1]
#   # Example file path, replace with your actual file

try:
    crc32c_int = 0
    # data = b"<html>" + (b"A" * 256 * 1024) + b"</html>"
    # crc32c_int = google_crc32c.extend(crc32c_int, data)
    with open(file_path, "rb") as f:
        # Calculate the CRC32C checksum as an integer
        crc32c_int = 0
        while True:
            chunk = f.read(1024 * 1024 * 1024)  # Read in 64KiB chunks
            if not chunk:
                break
            crc32c_int = google_crc32c.extend(crc32c_int, chunk)

    # --- Format the checksum in all three ways ---
    # 1. Hexadecimal format (32-bit, zero-padded)
    crc32c_hex = f"{crc32c_int:08x}"

    # 2. Base64 format (from big-endian bytes)
    crc32c_bytes = crc32c_int.to_bytes(4, "big")
    base64_encoded = base64.b64encode(crc32c_bytes)
    print("this is the crc32c in base64_encoded (in bytes) ", base64_encoded)
    crc32c_base64 = base64_encoded.decode("utf-8")

    # --- Print the results ---
    print(f"✅ Checksum results for '{file_path}':")
    print(f"  - Integer:   {crc32c_int}")
    print(f"  - Hex:       {crc32c_hex}")
    print(f"  - Base64 (after decoding ):    {crc32c_base64}")

except FileNotFoundError:
    print(f"❌ Error: The file '{file_path}' was not found.")
except Exception as e:
    print(f"An error occurred: {e}")
