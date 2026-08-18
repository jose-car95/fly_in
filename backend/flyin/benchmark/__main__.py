"""Entry point: print the benchmark table for the official maps."""

from flyin.benchmark.suite import BenchmarkSuite


def main() -> None:
    """Print the benchmark report to stdout."""
    print(BenchmarkSuite().report())


if __name__ == "__main__":
    main()
