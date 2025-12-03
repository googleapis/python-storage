import secrets

def generate_random_64bit_int():
  """Generates a secure 64-bit random integer."""
  # 8 bytes * 8 bits/byte = 64 bits
  random_bytes = secrets.token_bytes(8)
  # Convert bytes to an integer
  return int.from_bytes(random_bytes, "big")

# Generate 1000 unique IDs
# A set is the easiest way to guarantee uniqueness in the batch.
request_ids = set()
while len(request_ids) < 1000:
  request_ids.add(generate_random_64bit_int())

# You can convert it to a list if needed
id_list = list(request_ids)

print(f"Generated {len(id_list)} unique 64-bit IDs.")
print("First 5 IDs:", id_list[:5])
