"""Climate Insights: download and analyze historical weather data.

Example:
    >>> from climate_insights import ClimateAnalyzer, WeatherFetcher, find_city
    >>> city = find_city("Dortmund")
    >>> data = WeatherFetcher().fetch(city, years=30)
    >>> analyzer = ClimateAnalyzer(city, data)
    >>> analyzer.warming_trend()  # °C per decade
"""

from climate_insights.analysis import ClimateAnalyzer, PeriodComparison
from climate_insights.fetcher import WeatherFetcher
from climate_insights.geocoding import City, CityNotFoundError, find_city
from climate_insights.plotting import (
    create_all_plots,
    plot_extreme_heat_days,
    plot_monthly_climate,
    plot_seasonal_trends,
    plot_warming_stripes,
    plot_yearly_temperature,
)
from climate_insights.report import format_comparison, format_report

__all__ = [
    "City",
    "CityNotFoundError",
    "ClimateAnalyzer",
    "PeriodComparison",
    "WeatherFetcher",
    "create_all_plots",
    "find_city",
    "format_comparison",
    "format_report",
    "plot_extreme_heat_days",
    "plot_monthly_climate",
    "plot_seasonal_trends",
    "plot_warming_stripes",
    "plot_yearly_temperature",
]
