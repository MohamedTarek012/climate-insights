"""Command-line interface of Climate Insights.

Usage:
    uv run -m climate_insights --city Dortmund
    uv run -m climate_insights --city Dortmund --compare Cairo London
"""

import argparse
import sys
from pathlib import Path

import requests

from climate_insights.analysis import ClimateAnalyzer
from climate_insights.fetcher import DEFAULT_CACHE_DIR, WeatherFetcher
from climate_insights.geocoding import CityNotFoundError, find_city
from climate_insights.plotting import DEFAULT_OUTPUT_DIR, create_all_plots
from climate_insights.report import format_comparison, format_report

MIN_YEARS = 2
# The Open-Meteo archive starts in 1940.
MAX_YEARS = 80


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command-line arguments.

    Args:
        argv: The arguments to parse. Defaults to sys.argv[1:].
    """
    parser = argparse.ArgumentParser(
        prog="climate_insights",
        description="Download and analyze historical weather data for any city.",
        epilog="Example: uv run -m climate_insights --city Dortmund --compare Cairo",
    )
    parser.add_argument("--city", required=True, help="the city to analyze")
    parser.add_argument(
        "--compare",
        nargs="+",
        default=[],
        metavar="CITY",
        help="one or more cities to compare with",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=30,
        help=f"number of complete years to analyze ({MIN_YEARS}-{MAX_YEARS}, "
        "default: 30)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"folder for the saved plots (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help=f"folder for downloaded data (default: {DEFAULT_CACHE_DIR})",
    )
    parser.add_argument(
        "--no-plots", action="store_true", help="only print the text report"
    )

    args = parser.parse_args(argv)
    if not MIN_YEARS <= args.years <= MAX_YEARS:
        parser.error(f"--years must be between {MIN_YEARS} and {MAX_YEARS}.")
    return args


def main(argv: list[str] | None = None) -> int:
    """Run the command-line program and return the exit code."""
    args = parse_args(argv)
    fetcher = WeatherFetcher(cache_dir=args.data_dir)

    analyzers = []
    try:
        for name in [args.city, *args.compare]:
            city = find_city(name)
            data = fetcher.fetch(city, years=args.years)
            analyzers.append(ClimateAnalyzer(city, data))
    except CityNotFoundError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except requests.RequestException as error:
        print(
            f"Error: could not download data ({error}). "
            "Please check your internet connection.",
            file=sys.stderr,
        )
        return 1

    for analyzer in analyzers:
        print()
        print(format_report(analyzer))

    if len(analyzers) > 1:
        print()
        print(format_comparison(analyzers))

    if not args.no_plots:
        paths = create_all_plots(analyzers, args.output_dir)
        print()
        print(f"Saved {len(paths)} plots:")
        for path in paths:
            print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
