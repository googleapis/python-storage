# python-storage benchmarking

**This is not an officially supported Google product**

This benchmarking script is used by Storage client library maintainers to benchmark various workloads and collect metrics in order to improve performance of the library.
Currently the benchmarking runs a Write-1-Read-3 workload and measures the usual two QoS performance attributes, latency and throughput.

## Run example:
This runs 10K iterations of Write-1-Read-3 on 5KiB to 2GiB files, and generates output to a default csv file `benchmarking<TIMESTAMP>.csv`:
```bash
$ cd storage
$ pip install -e . # install google.cloud.storage locally
$ cd tests/perf
$ python3 benchmarking.py --max_samples 10000 --max_size 2147483648
```

## CLI parameters

| Parameter | Description | Possible values | Default |
| --------- | ----------- | --------------- |:-------:|
| --min_size | minimum object size in bytes | any positive integer | `5120` |
| --max_size | maximum object size in bytes | any positive integer | `16384` |
| --num_samples | number of W1R3 iterations | any positive integer | `1000` |
| --p | number of processes (multiprocessing enabled) | any positive integer | `10` |
| --r | bucket region for benchmarks | any GCS region | `US` |
| --o | file to output results to | any file path | `benchmarking<TIMESTAMP>.csv` |


## Workload definition and CSV headers

For each invocation of the benchmark, write a new object of random size between `min_size` and `max_size` . After the successful write, download the object in full three times. For each of the 4 operations record the following fields:

| Field | Description |
| ----- | ----------- |
| Op | the name of the operations (WRITE, READ[{0,1,2}]) |
| ObjectSize | the number of bytes of the object |
| LibBufferSize | LibBufferSize is configured to use the library default of 100 MiB |
| Crc32cEnabled | whether crc32c was computed for the operation |
| MD5Enabled | whether MD5 was computed for the operation |
| ApiName | default to JSON|
| ElapsedTimeUs | the elapsed time in microseconds the operation took |
| Status | completion state of the operation [OK, FAIL] |
| AppBufferSize | N/A |
| CpuTimeUs | N/A |