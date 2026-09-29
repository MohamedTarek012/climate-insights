"""Create climate plots and save them as PNG files.

The plots use matplotlib's Figure class directly instead of pyplot, so no
plot window is opened. Every function saves its figure and returns the path.
"""

from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from climate_insights.analysis import ClimateAnalyzer

DEFAULT_OUTPUT_DIR = Path("outputs")
MONTH_LABELS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
LABEL_SIZE = 12


def plot_yearly_temperature(
    analyzers: list[ClimateAnalyzer], output_dir: str | Path = DEFAULT_OUTPUT_DIR
) -> Path:
    """Plot the yearly mean temperature with a linear trend line per city."""
    fig = Figure(figsize=(10, 5), layout="constrained")
    ax = fig.subplots()

    for a in analyzers:
        yearly = a.yearly_summary()["temp_mean"]
        (line,) = ax.plot(
            yearly.index, yearly, marker="o", markersize=3, label=a.city.name
        )
        trend = a.yearly_trend_line()
        ax.plot(
            trend.index,
            trend,
            linestyle="--",
            color=line.get_color(),
            label=f"Trend: {a.warming_trend():+.2f} °C/decade",
        )

    ax.set_xlabel("Year", fontsize=LABEL_SIZE)
    ax.set_ylabel("Mean temperature (°C)", fontsize=LABEL_SIZE)
    ax.set_title("Yearly mean temperature", fontsize=LABEL_SIZE + 2)
    ax.grid(alpha=0.3)
    ax.legend()
    return _save(fig, output_dir, f"{_slug(analyzers)}_yearly_temperature.png")


def plot_warming_stripes(
    analyzer: ClimateAnalyzer, output_dir: str | Path = DEFAULT_OUTPUT_DIR
) -> Path:
    """Draw "warming stripes": one colored stripe per year.

    Blue stripes are colder than the average of the whole period, red
    stripes are warmer.
    """
    anomalies = analyzer.temperature_anomalies()
    limit = float(np.abs(anomalies).max())

    fig = Figure(figsize=(10, 2.8), layout="constrained")
    ax = fig.subplots()
    image = ax.imshow(
        anomalies.to_numpy()[np.newaxis, :],
        cmap="RdBu_r",
        aspect="auto",
        vmin=-limit,
        vmax=limit,
        extent=(analyzer.start_year - 0.5, analyzer.end_year + 0.5, 0, 1),
    )
    ax.set_yticks([])
    ax.set_xlabel("Year", fontsize=LABEL_SIZE)
    ax.set_title(
        f"Warming stripes: {analyzer.city} ({analyzer.start_year}-{analyzer.end_year})",
        fontsize=LABEL_SIZE + 2,
    )
    fig.colorbar(image, ax=ax, label="Difference from average (°C)")
    return _save(fig, output_dir, f"{_slug([analyzer])}_warming_stripes.png")


def plot_monthly_climate(
    analyzers: list[ClimateAnalyzer], output_dir: str | Path = DEFAULT_OUTPUT_DIR
) -> Path:
    """Plot average temperature and precipitation for each month."""
    fig = Figure(figsize=(10, 7), layout="constrained")
    ax_temp, ax_rain = fig.subplots(2, 1, sharex=True)
    width = 0.8 / len(analyzers)

    for i, a in enumerate(analyzers):
        climate = a.monthly_climate()
        ax_temp.plot(climate.index, climate["temp_mean"], marker="o", label=a.city.name)
        offset = (i - (len(analyzers) - 1) / 2) * width
        ax_rain.bar(
            climate.index + offset,
            climate["precipitation"],
            width=width,
            label=a.city.name,
        )

    ax_temp.set_ylabel("Mean temperature (°C)", fontsize=LABEL_SIZE)
    ax_temp.set_title("Average climate by month", fontsize=LABEL_SIZE + 2)
    ax_temp.grid(alpha=0.3)
    ax_temp.legend()
    ax_rain.set_ylabel("Precipitation (mm)", fontsize=LABEL_SIZE)
    ax_rain.set_xticks(range(1, 13), MONTH_LABELS)
    ax_rain.grid(alpha=0.3, axis="y")
    ax_rain.legend()
    return _save(fig, output_dir, f"{_slug(analyzers)}_monthly_climate.png")


def plot_extreme_heat_days(
    analyzers: list[ClimateAnalyzer], output_dir: str | Path = DEFAULT_OUTPUT_DIR
) -> Path:
    """Plot the number of extreme heat days per year, one panel per city."""
    fig = Figure(figsize=(10, 3.5 * len(analyzers)), layout="constrained")
    axes = fig.subplots(len(analyzers), 1, sharex=True, squeeze=False)[:, 0]

    for ax, a in zip(axes, analyzers):
        heat_days = a.extreme_heat_days()
        ax.bar(
            heat_days.index,
            heat_days,
            color="tab:red",
            alpha=0.6,
            label="Extreme heat days",
        )
        rolling = heat_days.rolling(5, center=True).mean()
        ax.plot(
            rolling.index, rolling, color="darkred", linewidth=2, label="5-year average"
        )
        ax.set_ylabel("Days per year", fontsize=LABEL_SIZE)
        ax.set_title(f"Extreme heat days: {a.city}", fontsize=LABEL_SIZE + 2)
        ax.grid(alpha=0.3, axis="y")
        ax.legend(loc="upper left")

    axes[-1].set_xlabel("Year", fontsize=LABEL_SIZE)
    return _save(fig, output_dir, f"{_slug(analyzers)}_extreme_heat_days.png")


def plot_seasonal_trends(
    analyzers: list[ClimateAnalyzer], output_dir: str | Path = DEFAULT_OUTPUT_DIR
) -> Path:
    """Compare the warming trend of each season as a grouped bar chart."""
    fig = Figure(figsize=(9, 5), layout="constrained")
    ax = fig.subplots()
    width = 0.8 / len(analyzers)
    positions = np.arange(4)

    for i, a in enumerate(analyzers):
        seasons = a.seasonal_summary()
        offset = (i - (len(analyzers) - 1) / 2) * width
        ax.bar(
            positions + offset,
            seasons["trend_per_decade"],
            width=width,
            label=a.city.name,
        )

    ax.set_xticks(positions, seasons.index)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Trend (°C per decade)", fontsize=LABEL_SIZE)
    ax.set_title("Warming trend by season", fontsize=LABEL_SIZE + 2)
    ax.grid(alpha=0.3, axis="y")
    ax.legend()
    return _save(fig, output_dir, f"{_slug(analyzers)}_seasonal_trends.png")


def create_all_plots(
    analyzers: list[ClimateAnalyzer], output_dir: str | Path = DEFAULT_OUTPUT_DIR
) -> list[Path]:
    """Create every available plot and return the paths of the saved files."""
    paths = [
        plot_yearly_temperature(analyzers, output_dir),
        plot_monthly_climate(analyzers, output_dir),
        plot_extreme_heat_days(analyzers, output_dir),
        plot_seasonal_trends(analyzers, output_dir),
    ]
    paths += [plot_warming_stripes(a, output_dir) for a in analyzers]
    return paths


def _slug(analyzers: list[ClimateAnalyzer]) -> str:
    """Build a file name prefix from the city names, e.g. "dortmund_cairo"."""
    return "_".join(a.city.name.lower().replace(" ", "-") for a in analyzers)


def _save(fig: Figure, output_dir: str | Path, filename: str) -> Path:
    """Save a figure as PNG in the output directory and return its path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.savefig(path, dpi=150)
    return path
