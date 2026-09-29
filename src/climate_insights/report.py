"""Turn analysis results into readable text reports."""

from climate_insights.analysis import ClimateAnalyzer

# Trends smaller than this (in °C per decade) are described as stable.
STABLE_TREND = 0.1


def format_report(analyzer: ClimateAnalyzer) -> str:
    """Create a text report with the key climate statistics of one city.

    Args:
        analyzer: The analyzer of the city to report on.

    Returns:
        A multi-line string ready to be printed.
    """
    a = analyzer
    trend = a.warming_trend()
    hot_year, hot_year_temp = a.hottest_year()
    cold_year, cold_year_temp = a.coldest_year()
    hot_day, hot_day_temp = a.hottest_day()
    cold_day, cold_day_temp = a.coldest_day()
    periods = a.period_comparison()
    seasons = a.seasonal_summary()
    early = f"{periods.first_period[0]}-{periods.first_period[1]}"
    recent = f"{periods.last_period[0]}-{periods.last_period[1]}"

    title = f"{a.city} ({a.start_year}-{a.end_year})"
    lines = [
        title,
        "=" * len(title),
        f"  Average temperature:     {a.mean_temperature():.1f} °C",
        f"  Warming trend:           {trend:+.2f} °C per decade",
        f"  Hottest year:            {hot_year} ({hot_year_temp:.1f} °C)",
        f"  Coldest year:            {cold_year} ({cold_year_temp:.1f} °C)",
        f"  Hottest day:             {hot_day:%d %b %Y} ({hot_day_temp:.1f} °C)",
        f"  Coldest day:             {cold_day:%d %b %Y} ({cold_day_temp:.1f} °C)",
        f"  Yearly precipitation:    {a.mean_yearly_precipitation():.0f} mm",
        "",
        f"  {early} vs {recent}:",
        f"    Mean temperature:      {periods.temp_change:+.2f} °C",
        (
            f"    Extreme heat days/yr:  {periods.heat_days_early:.1f} -> "
            f"{periods.heat_days_recent:.1f}"
        ),
        "",
        "  Seasons (mean, trend per decade):",
    ]
    for season, row in seasons.iterrows():
        lines.append(
            f"    {season}:  {row['temp_mean']:5.1f} °C   "
            f"{row['trend_per_decade']:+.2f} °C"
        )

    lines += ["", "  Insights:"]
    lines += [f"    - {insight}" for insight in _insights(a)]
    return "\n".join(lines)


def format_comparison(analyzers: list[ClimateAnalyzer]) -> str:
    """Create a table that compares several cities side by side.

    Args:
        analyzers: One analyzer per city, at least two.

    Returns:
        A multi-line string ready to be printed.
    """
    header = (
        f"{'City':<25} {'Mean °C':>8} {'Trend/decade':>13} "
        f"{'Hottest year':>13} {'Heat days/yr':>16}"
    )
    lines = ["City comparison", "=" * len(header), header, "-" * len(header)]
    for a in analyzers:
        periods = a.period_comparison()
        hot_year, _ = a.hottest_year()
        heat_days = f"{periods.heat_days_early:.1f} -> {periods.heat_days_recent:.1f}"
        lines.append(
            f"{a.city!s:<25} {a.mean_temperature():>8.1f} "
            f"{a.warming_trend():>+13.2f} {hot_year:>13} {heat_days:>16}"
        )

    fastest = max(analyzers, key=lambda a: a.warming_trend())
    lines += [
        "",
        (
            f"{fastest.city.name} is warming the fastest "
            f"({fastest.warming_trend():+.2f} °C per decade)."
        ),
    ]
    return "\n".join(lines)


def _insights(analyzer: ClimateAnalyzer) -> list[str]:
    """Generate plain-language conclusions from the statistics."""
    a = analyzer
    name = a.city.name
    trend = a.warming_trend()
    years = a.end_year - a.start_year + 1
    insights = []

    if trend > STABLE_TREND:
        total = trend * years / 10
        insights.append(
            f"{name} has warmed by about {total:.1f} °C over the last {years} years."
        )
    elif trend < -STABLE_TREND:
        insights.append(f"{name} has become cooler over the last {years} years.")
    else:
        insights.append(f"The temperature in {name} has stayed roughly stable.")

    seasons = a.seasonal_summary()
    fastest_season = seasons["trend_per_decade"].idxmax()
    fastest_trend = seasons.loc[fastest_season, "trend_per_decade"]
    if fastest_trend > STABLE_TREND:
        insights.append(
            f"The strongest warming happens in {fastest_season} "
            f"({fastest_trend:+.2f} °C per decade)."
        )

    periods = a.period_comparison()
    if periods.heat_days_early > 0:
        ratio = periods.heat_days_recent / periods.heat_days_early
        if ratio >= 1.2:
            insights.append(
                f"Extreme heat days are {ratio:.1f}x as common as "
                f"in {periods.first_period[0]}-{periods.first_period[1]}."
            )
        elif ratio <= 0.8:
            insights.append("Extreme heat days have become less common.")

    if years < 20:
        return insights
    recent_years = a.yearly_summary()["temp_mean"].nlargest(5).index
    recent_count = sum(year >= a.end_year - 9 for year in recent_years)
    if recent_count >= 3:
        insights.append(
            f"{recent_count} of the 5 hottest years were in the last ten years."
        )
    return insights
