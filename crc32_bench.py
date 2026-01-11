import timeit
import os
import google_crc32c
from google_crc32c import Checksum

def benchmark():
    # Setup: Create a 1MB random payload
    data = os.urandom(2 * 1024 * 1024)
    
    # Method 1: The old approach (Object instantiation + digest + conversion)
    def method_old():
        # Note: Checksum(data).digest() returns bytes, which we convert to int
        return int.from_bytes(Checksum(data).digest(), "big")

    # Method 2: The new approach (Direct C-extension call)
    def method_new():
        return google_crc32c.value(data)

    # Verify they produce the same result
    assert method_old() == method_new(), "Checksums do not match!"

    # Configuration for timeit
    iterations = 1000
    
    print(f"Benchmarking with {len(data)/1024:.0f}KB payload over {iterations} iterations...")

    # Measure Method 1
    time_old = timeit.timeit(method_old, number=iterations)
    print(f"Old method: {time_old:.4f} seconds total")

    # Measure Method 2
    time_new = timeit.timeit(method_new, number=iterations)
    print(f"New method: {time_new:.4f} seconds total")

    # Calculate difference
    if time_new > 0:
        speedup = time_old / time_new
        print(f"\nResult: The new method is {speedup:.2f}x faster")
        print(f"Difference per call: {(time_old - time_new) / iterations * 1000:.4f} ms")
    else:
        print("\nNew method was too fast to measure accurately.")

if __name__ == "__main__":
    try:
        benchmark()
    except ImportError:
        print("Error: google-crc32c is not installed. Run 'pip install google-crc32c'")
