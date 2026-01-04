from typing import Any, List
import statistics


def publish_benchmark_extra_info(
    benchmark: Any,
    params: Any,
    benchmark_group: str = "read",
    true_times: List[float] = [],
) -> None:
    """
    Helper function to publish benchmark parameters to the extra_info property.
    """

    benchmark.extra_info["num_files"] = params.num_files
    benchmark.extra_info["file_size"] = params.file_size_bytes
    benchmark.extra_info["chunk_size"] = params.chunk_size_bytes
    if benchmark_group == "write":
        benchmark.extra_info["pattern"] = "seq"
    else:
        benchmark.extra_info["pattern"] = params.pattern
    benchmark.extra_info["coros"] = params.num_coros
    benchmark.extra_info["rounds"] = params.rounds
    benchmark.extra_info["bucket_name"] = params.bucket_name
    benchmark.extra_info["bucket_type"] = params.bucket_type
    benchmark.extra_info["processes"] = params.num_processes
    benchmark.group = benchmark_group

    object_size = params.file_size_bytes
    num_files = params.num_files
    min_throughput = (object_size / (1024 * 1024) * num_files) / benchmark.stats["max"]
    max_throughput = (object_size / (1024 * 1024) * num_files) / benchmark.stats["min"]
    mean_throughput = (object_size / (1024 * 1024) * num_files) / benchmark.stats["mean"]
    median_throughput = (
        object_size / (1024 * 1024) * num_files
    ) / benchmark.stats["median"]

    benchmark.extra_info["throughput_MiB_s_min"] = min_throughput
    benchmark.extra_info["throughput_MiB_s_max"] = max_throughput
    benchmark.extra_info["throughput_MiB_s_mean"] = mean_throughput
    benchmark.extra_info["throughput_MiB_s_median"] = median_throughput

    print(f"\nThroughput Statistics (MiB/s):")
    print(f"  Min:    {min_throughput:.2f} (from max time)")
    print(f"  Max:    {max_throughput:.2f} (from min time)")
    print(f"  Mean:   {mean_throughput:.2f} (approx, from mean time)")
    print(f"  Median: {median_throughput:.2f} (approx, from median time)")

    if true_times:
        throughputs = [(object_size / (1024 * 1024) * num_files) / t for t in true_times]
        true_min_throughput = min(throughputs)
        true_max_throughput = max(throughputs)
        true_mean_throughput = statistics.mean(throughputs)
        true_median_throughput = statistics.median(throughputs)

        benchmark.extra_info["true_throughput_MiB_s_min"] = true_min_throughput
        benchmark.extra_info["true_throughput_MiB_s_max"] = true_max_throughput
        benchmark.extra_info["true_throughput_MiB_s_mean"] = true_mean_throughput
        benchmark.extra_info["true_throughput_MiB_s_median"] = true_median_throughput

        print(f"\nThroughput Statistics from true_times (MiB/s):")
        print(f"  Min:    {true_min_throughput:.2f}")
        print(f"  Max:    {true_max_throughput:.2f}")
        print(f"  Mean:   {true_mean_throughput:.2f}")
        print(f"  Median: {true_median_throughput:.2f}")

    # Get benchmark name, rounds, and iterations
    name = benchmark.name
    rounds = benchmark.stats['rounds']
    iterations = benchmark.stats['iterations']

    # Header for throughput table
    header = "\n\n" + "-" * 125 + "\n"
    header += "Throughput Benchmark (MiB/s)\n"
    header += "-" * 125 + "\n"
    header += f"{'Name':<50} {'Min':>10} {'Max':>10} {'Mean':>10} {'StdDev':>10} {'Median':>10} {'Rounds':>8} {'Iterations':>12}\n"
    header += "-" * 125

    # Data row for throughput table
    # The table headers (Min, Max) refer to the throughput values.
    row = f"{name:<50} {min_throughput:>10.4f} {max_throughput:>10.4f} {mean_throughput:>10.4f} {'N/A':>10} {median_throughput:>10.4f} {rounds:>8} {iterations:>12}"

    print(header)
    print(row)
    print("-" * 125)
