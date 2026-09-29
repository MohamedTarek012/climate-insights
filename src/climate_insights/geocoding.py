"""Look up the geographic coordinates of a city by its name."""

from dataclasses import dataclass

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


class CityNotFoundError(Exception):
    """Raised when no city matches the given name."""


@dataclass(frozen=True)
class City:
    """A city with its geographic coordinates.

    Attributes:
        name: The city's name, e.g. "Dortmund".
        country: The country the city is in, e.g. "Germany".
        latitude: Latitude in degrees.
        longitude: Longitude in degrees.
    """

    name: str
    country: str
    latitude: float
    longitude: float

    def __str__(self) -> str:
        return f"{self.name}, {self.country}"


def find_city(name: str) -> City:
    """Find a city by name using the Open-Meteo geocoding API.

    Args:
        name: The name of the city to search for.

    Returns:
        The best-matching City.

    Raises:
        CityNotFoundError: If no city with that name exists.
        requests.HTTPError: If the API request fails.
    """
    params = {"name": name, "count": 1, "language": "en", "format": "json"}
    response = requests.get(GEOCODING_URL, params=params, timeout=30)
    response.raise_for_status()

    results = response.json().get("results")
    if not results:
        raise CityNotFoundError(f"Could not find a city named {name!r}.")

    match = results[0]
    return City(
        name=match["name"],
        country=match.get("country", "Unknown"),
        latitude=match["latitude"],
        longitude=match["longitude"],
    )
