"""Statistical analysis of daily weather data."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from climate_insights.geocoding import City

REQUIRED_COLUMNS = {"date", "temp_mean", "temp_max", "temp_min", "precipitation"}

# Meteorological seasons. They are labelled by month range instead of
# "winter"/"summer" so the labels are correct in both hemispheres.
SEASONS = {
    12: "Dec-Feb",
    1: "Dec-Feb",
    2: "Dec-Feb",
    3: "Mar-May",
    4: "Mar-May",
    5: "Mar-May",
    6: "Jun-Aug",
    7: "Jun-Aug",
    8: "Jun-Aug",
    9: "Sep-Nov",
    10: "Sep-Nov",
    11: "Sep-Nov",
}
SEASON_ORDER = ["Dec-Feb", "Mar-May", "Jun-Aug", "Sep-Nov"]


@dataclass(frozen=True)
class PeriodComparison:
    """Comparison between the first and the last years of a dataset.

    Attributes:
        first_period: First and last year of the early period.
        last_period: First and last year of the recent period.
        temp_change: Change in mean temperature in °C (recent - early).
        heat_days_early: Average extreme heat days per year, early period.
        heat_days_recent: Average extreme heat days per year, recent period.
    """

    first_period: tuple[int, int]
    last_period: tuple[int, int]
    temp_change: float
    heat_days_early: float
    heat_days_recent: float


class ClimateAnalyzer:
    """Compute climate statistics from daily weather data of one city.

    Args:
        city: The city the data belongs to.
        data: Daily data with the columns date, temp_mean, temp_max,
            temp_min and precipitation, as returned by WeatherFetcher.

    Raises:
        ValueError: If columns are missing or there are fewer than
            two years of data.
    """

    def __init__(self, city: City, data: pd.DataFrame):
        missing = REQUIRED_COLUMNS - set(data.columns)
        if missing:
            raise ValueError(f"Data is missing the columns {sorted(missing)}.")

        self.city = city
        self.data = data.copy()
        self.data["date"] = pd.to_datetime(self.data["date"])
        self.data["year"] = self.data["date"].dt.year
        self.data["month"] = self.data["date"].dt.month
        self.data["season"] = self.data["month"].map(SEASONS)

        if self.data["year"].nunique() < 2:
            raise ValueError("At least two years of data are needed.")

    @property
    def start_year(self) -> int:
        """The first year in the data."""
        return int(self.data["year"].min())

    @property
    def end_year(self) -> int:
        """The last year in the data."""
        return int(self.data["year"].max())

    def yearly_summary(self) -> pd.DataFrame:
        """Summarize each year.

        Returns:
            A DataFrame indexed by year with the mean temperature, the
            highest maximum, the lowest minimum and total precipitation.
        """
        return self.data.groupby("year").agg(
            temp_mean=("temp_mean", "mean"),
            temp_max=("temp_max", "max"),
            temp_min=("temp_min", "min"),
            precipitation=("precipitation", "sum"),
        )

    def mean_temperature(self) -> float:
        """Average temperature over the whole period in °C."""
        return float(self.yearly_summary()["temp_mean"].mean())

    def mean_yearly_precipitation(self) -> float:
        """Average total precipitation per year in mm."""
        return float(self.yearly_summary()["precipitation"].mean())

    def warming_trend(self) -> float:
        """Linear trend of the yearly mean temperature in °C per decade."""
        return _trend_per_decade(self.yearly_summary()["temp_mean"])

    def yearly_trend_line(self) -> pd.Series:
        """Values of the fitted linear trend line for each year."""
        yearly = self.yearly_summary()["temp_mean"].dropna()
        years = yearly.index.to_numpy(dtype=float)
        slope, intercept = np.polyfit(years, yearly.to_numpy(dtype=float), deg=1)
        return pd.Series(slope * years + intercept, index=yearly.index)

    def temperature_anomalies(self) -> pd.Series:
        """Yearly mean temperature minus the average of the whole period."""
        yearly = self.yearly_summary()["temp_mean"]
        return yearly - yearly.mean()

    def hottest_year(self) -> tuple[int, float]:
        """The year with the highest mean temperature and its value."""
        yearly = self.yearly_summary()["temp_mean"]
        return int(yearly.idxmax()), float(yearly.max())

    def coldest_year(self) -> tuple[int, float]:
        """The year with the lowest mean temperature and its value."""
        yearly = self.yearly_summary()["temp_mean"]
        return int(yearly.idxmin()), float(yearly.min())

    def hottest_day(self) -> tuple[pd.Timestamp, float]:
        """The day with the highest maximum temperature and its value."""
        row = self.data.loc[self.data["temp_max"].idxmax()]
        return row["date"], float(row["temp_max"])

    def coldest_day(self) -> tuple[pd.Timestamp, float]:
        """The day with the lowest minimum temperature and its value."""
        row = self.data.loc[self.data["temp_min"].idxmin()]
        return row["date"], float(row["temp_min"])

    def extreme_heat_days(self, quantile: float = 0.95) -> pd.Series:
        """Count extreme heat days per year.

        A day counts as extreme if its maximum temperature is higher than
        the given quantile of all maximum temperatures in the same calendar
        month. Comparing within each month means a very warm day in winter
        counts as well, and the definition works for hot and cold cities.

        Args:
            quantile: Threshold quantile between 0 and 1.

        Returns:
            A Series indexed by year with the number of extreme heat days.
        """
        thresholds = self.data.groupby("month")["temp_max"].transform(
            lambda values: values.quantile(quantile)
        )
        is_extreme = self.data["temp_max"] > thresholds
        return is_extreme.groupby(self.data["year"]).sum().astype(int)

    def period_comparison(self) -> PeriodComparison:
        """Compare the first ten years with the last ten years.

        If there are fewer than 20 years of data, the first and second
        half of the data are compared instead.
        """
        yearly = self.yearly_summary()
        heat_days = self.extreme_heat_days()
        length = min(10, len(yearly) // 2)
        early = yearly.index[:length]
        recent = yearly.index[-length:]

        return PeriodComparison(
            first_period=(int(early[0]), int(early[-1])),
            last_period=(int(recent[0]), int(recent[-1])),
            temp_change=float(
                yearly.loc[recent, "temp_mean"].mean()
                - yearly.loc[early, "temp_mean"].mean()
            ),
            heat_days_early=float(heat_days.loc[early].mean()),
            heat_days_recent=float(heat_days.loc[recent].mean()),
        )

    def monthly_climate(self) -> pd.DataFrame:
        """Average temperature and precipitation for each calendar month.

        Returns:
            A DataFrame indexed by month (1-12) with the mean temperature
            in °C and the mean monthly precipitation total in mm.
        """
        monthly_totals = self.data.groupby(["year", "month"])["precipitation"].sum()
        return pd.DataFrame(
            {
                "temp_mean": self.data.groupby("month")["temp_mean"].mean(),
                "precipitation": monthly_totals.groupby("month").mean(),
            }
        )

    def seasonal_summary(self) -> pd.DataFrame:
        """Mean temperature and warming trend for each season.

        December is counted towards the winter of the following year, so
        each Dec-Feb season is continuous. Incomplete seasons at the start
        and end of the data are left out.

        Returns:
            A DataFrame indexed by season with the mean temperature in °C
            and the trend in °C per decade.
        """
        data = self.data.copy()
        data["season_year"] = data["year"] + (data["month"] == 12)
        grouped = data.groupby(["season", "season_year"])
        is_complete = grouped["month"].nunique() == 3
        season_means = grouped["temp_mean"].mean()[is_complete]

        rows = {}
        for season in SEASON_ORDER:
            values = season_means.loc[season]
            rows[season] = {
                "temp_mean": float(values.mean()),
                "trend_per_decade": _trend_per_decade(values),
            }
        return pd.DataFrame.from_dict(rows, orient="index")


def _trend_per_decade(series: pd.Series) -> float:
    """Fit a straight line to a Series indexed by year, return °C/decade."""
    series = series.dropna()
    years = series.index.to_numpy(dtype=float)
    slope, _ = np.polyfit(years, series.to_numpy(dtype=float), deg=1)
    return float(slope * 10)
