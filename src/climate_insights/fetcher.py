"""Download historical daily weather data and cache it locally."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from climate_insights.geocoding import City

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Daily variables requested from the API, mapped to shorter column names.
DAILY_VARIABLES = {
    "temperature_2m_mean": "temp_mean",
    "temperature_2m_max": "temp_max",
    "temperature_2m_min": "temp_min",
    "precipitation_sum": "precipitation",
}

DEFAULT_CACHE_DIR = Path("data")


class WeatherFetcher:
    """Download daily weather data for a city and cache it as CSV.

    Data is only downloaded once. Later requests for the same city and
    time range are loaded from the cache directory instead.

    Args:
        cache_dir: Directory where downloaded data is stored.
    """

    def __init__(self, cache_dir: str | Path = DEFAULT_CACHE_DIR):
        self.cache_dir = Path(cache_dir)

    def fetch(self, city: City, years: int) -> pd.DataFrame:
        """Return daily weather data for the last `years` complete years.

        Args:
            city: The city to get data for.
            years: Number of complete calendar years, ending last year.

        Returns:
            A DataFrame with one row per day and the columns
            date, temp_mean, temp_max, temp_min and precipitation.
        """
        if years < 1:
            raise ValueError("years must be at least 1.")

        end_year = datetime.now(timezone.utc).year - 1
        start_year = end_year - years + 1
        cache_file = self._cache_path(city, start_year, end_year)

        if cache_file.exists():
            print(f"Loading cached data for {city} from {cache_file}")
            return pd.read_csv(cache_file, parse_dates=["date"])

        print(f"Downloading {years} years of weather data for {city}...")
        data = self._download(city, f"{start_year}-01-01", f"{end_year}-12-31")

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        data.to_csv(cache_file, index=False)
        return data

    def _cache_path(self, city: City, start_year: int, end_year: int) -> Path:
        """Build the cache file name for a city and year range."""
        slug = f"{city.name}_{city.country}".lower().replace(" ", "-")
        return self.cache_dir / f"{slug}_{start_year}_{end_year}.csv"

    @staticmethod
    def _download(city: City, start_date: str, end_date: str) -> pd.DataFrame:
        """Download daily weather data from the Open-Meteo archive API."""
        params = {
            "latitude": city.latitude,
            "longitude": city.longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": ",".join(DAILY_VARIABLES),
            "timezone": "auto",
        }
        response = requests.get(ARCHIVE_URL, params=params, timeout=120)
        response.raise_for_status()

        daily = response.json()["daily"]
        data = pd.DataFrame(daily)
        data = data.rename(columns={"time": "date", **DAILY_VARIABLES})
        data["date"] = pd.to_datetime(data["date"])
        return data
