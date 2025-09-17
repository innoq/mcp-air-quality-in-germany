from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from urllib.parse import urljoin

from data_validation_models import (
    ComponentsAnnuallyParams,
    StationsForComponentParams,
    MetadataParams,
    StationsNearbyParams,
    QualityForStationNowParams,
    QualityForStationParams,
    COMPONENTS_BY_NUMBER
)


# Initialize FastMCP server
mcp = FastMCP("airdata")

# Constants
UBA_API_BASE = "https://www.umweltbundesamt.de/api/air_data/v3/"
USER_AGENT = "airdata-app/1.0"
ACCEPT = "application/json"

SCOPE = {
    '1': 'Tagesmittel',
    '2': 'Ein-Stunden-Mittelwert',
    '3': 'Ein-Stunden-Tagesmaxima',
    '4': 'Acht-Stunden-Mittelwert',
    '5': 'Acht-Stunden-Tagesmaxima',
    '6': 'Tagesmittel'
}


def generate_url(base, endpoint, params=None):
    url = httpx.URL(urljoin(base, endpoint)).copy_merge_params(params)
    return str(url)


async def make_request(url: str) -> dict[str, Any] | None:
    """Make a request to the API and return the response."""
    headers = {"User-Agent": USER_AGENT,
               "Accept": ACCEPT}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()

            return response.json()
        except Exception as e:
            return None


def extract_city_street_coordinates(data, post_code):
    # Iterating over the response `data` dictionary, returning only stations with post code that starts with the same number
    extracted_info = []
    # As LLMs are better with post codes than with coordinates: If first digit of input post code is the same as station post code, append station data
    # Possibility: Integrate with map MCP
    for id, info in data.items():
        if info[19][0] == post_code[0]:
            station_info = {
                "Stations-ID": id,
                "Stadt": info[3],
                "Straße": f"{info[17]} {info[18]}",
                "PLZ": info[19],
                "Koordinaten": (info[7], info[8])
            }
            extracted_info.append(station_info)
    return extracted_info


def get_time_three_hours_ago_and_now(timezone):
    # Get current time in specified timezone
    now = datetime.now(ZoneInfo(timezone))
    three_hours_ago = now - timedelta(hours=3)

    # Format dates and times for API
    date_from = three_hours_ago.strftime("%Y-%m-%d")
    date_to = now.strftime("%Y-%m-%d")
    time_from = three_hours_ago.strftime("%H")
    time_to = now.strftime("%H")
    return date_from, date_to, time_from, time_to


@mcp.tool()
async def get_components_annually(year: str, component: str) -> dict:
    """Holt die Jahresmittelwerte für einen bestimmten Schadstoff in µg/m³ für alle Stationen, die ihn messen, in der Form {'<Station>': '<Jahresmittelwert>'}. Nimmt als Parameter ein Jahr in der Form YYYY und die Schadstoffnummer des Schadstoffs, zu finden unter der mcp-Funktion get_components_by_number()."""

    try:
        ComponentsAnnuallyParams(year=year, component=component)

    except Exception as e:
        return {'error': ('Parameterfehler: ' + str(e))}

    annual_components_url = generate_url(UBA_API_BASE, "annualbalances/json", {"component": component, "year": year})
    try:
        response = await make_request(annual_components_url)
        if response is None or 'data' not in response:
            return {'response': 'Es wurden keine Werte für diesen Schadstoff gefunden.'}
        else:
            result = {}
            data = response['data']
            for pollutant_for_station in data:
                result[pollutant_for_station[0]] = pollutant_for_station[1]
            return {'response': result}
    except Exception as e:
        return {'error': ('Es ist ein Fehler aufgetreten: ' + str(e))}


@mcp.tool()
async def get_stations_scope_and_span_for_component(component: str) -> dict:
    """Holt die IDs der Stationen, die Häufigkeit und die Zeitspanne der Messungen einer bestimmten Komponente. Parameter ist eine der Komponenten-IDs, die get_components_by_number() als Keys zurückgibt."""

    try:
        StationsForComponentParams(component=component)

    except Exception as e:
        return {'error': ('Parameterfehler: ' + str(e))}

    scope_and_span_url = generate_url(UBA_API_BASE, "measures/limits")
    try:
        response = await make_request(scope_and_span_url)
        if response is None or 'data' not in response:
            return {'response': 'Es wurden keine Daten gefunden.'}

        # Only collect data for the requested component
        stations_for_component = []
        for _, measurement_limits in response['data'].items():
            if (isinstance(measurement_limits, list) and
                    len(measurement_limits) >= 5 and
                    measurement_limits[1] == component):
                scope_id = measurement_limits[0]
                station_id = measurement_limits[2]
                messbeginn = measurement_limits[3]
                letzte_messung = measurement_limits[4]

                stations_for_component.append({
                    'Station': station_id,
                    'Messbeginn': messbeginn,
                    'Letzte_Messung': letzte_messung,
                    'Häufigkeit': SCOPE[scope_id]
                })
        if stations_for_component:
            component_name = COMPONENTS_BY_NUMBER[component]
            return {'response': {component_name: stations_for_component}}
        else:
            return {'response': 'Es wurden keine Messstationen für diese Komponente gefunden.'}
    except Exception as e:
        return {'error': ('Es ist ein Fehler aufgetreten: ' + str(e))}


@mcp.tool()
async def get_metadata_now(timezone: str = "Europe/Berlin") -> dict:
    """Holt Metadaten. Nimmt als Parameter die Zeitzone. Response hat eine hohe Tokenzahl. Erst zu verwenden, wenn alle anderen Calls nicht die gewünschten Informationen enthalten."""

    try:
        MetadataParams(timezone=timezone)

    except Exception as e:
        return {'error': ('Parameterfehler: ' + str(e))}

    date_from, date_to, time_from, time_to = get_time_three_hours_ago_and_now(timezone)

    meta_url = generate_url(UBA_API_BASE, "meta/json",
                            {"use": "airquality", "lang": "de", "date_from": date_from, "date_to": date_to,
                             "time_from": time_from, "time_to": time_to})
    try:
        response = await make_request(meta_url)
        if response is None:
            return {'response': 'Es wurden keine Metadaten gefunden.'}
        return {'response': response}
    except Exception as e:
        return {'error': ('Es ist ein Fehler aufgetreten: ' + str(e))}


@mcp.tool()
async def get_all_stations_nearby_today(post_code: str) -> dict:
    """Holt alle Messstationen inklusive ID, Stadt und Straße zu diesem Zeitpunkt, deren Postleitzahl mit der ersten Zahl des Parameters übereinstimmt. Nur die erste Ziffer der Postleitzahl wird berücksichtigt! Nimmt als Parameter eine fünfstellige Postleitzahl."""
    date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d") # Yesterday
    date_to = datetime.now().strftime("%Y-%m-%d")

    try:
        StationsNearbyParams(post_code=post_code)

    except Exception as e:
        return {'error': ('Parameterfehler: ' + str(e))}

    stations_url = generate_url(UBA_API_BASE, "stations/json",
                                {"use": "airquality", "lang": "de", "date_from": date_from, "date_to": date_to,
                                 "time_from": "9", "time_to": "18"})

    try:
        response = await make_request(stations_url)
        if response is None or 'data' not in response:
            return {'response': 'Es wurden keine Messstationen gefunden.'}

        else:
            data = response['data']
            extracted_info = extract_city_street_coordinates(data, post_code)
            return {'response': ('Die folgenden Messstationen sind in der Nähe von ' + post_code + ' aktiv: ' + str(extracted_info))}
    except Exception as e:
        return {'error': ('Es ist ein Fehler aufgetreten: ' + str(e))}


@mcp.tool()
async def get_quality_for_station_now(station: str, timezone: str = "Europe/Berlin") -> dict:
    """Holt die aktuelle Luftqualität für eine bestimmte Messstation."""

    try:
        QualityForStationNowParams(station=station, timezone=timezone)

    except Exception as e:
        return {'error': ('Parameterfehler: ' + str(e))}

    try:
        date_from, date_to, time_from, time_to = get_time_three_hours_ago_and_now(timezone)
        result = await get_quality_for_station(station, date_from, date_to, time_from, time_to)
        if result is None:
            return {'response': 'Es wurden keine aktuellen Luftdaten gefunden.'}
        return {'response': result}
    except Exception as e:
        return {'error': ('Es ist ein Fehler aufgetreten: ' + str(e))}


@mcp.tool()
async def get_quality_for_station(station: str, date_from: str, date_to: str, time_from: str, time_to: str) -> dict:
    """Holt die Luftqualitätsdaten für eine bestimmte Messstation für einen bestimmten Zeitraum und gibt die Messwerte nach Komponenten gruppiert zurück.
    Parameter:
    - station: ID der Messstation
    - date_from und date_to: Datumsbereich im Format YYYY-MM-DD (in der Vergangenheit oder Gegenwart)
    - time_from und time_to: Uhrzeitbereich im Format HH
    Rückgabe: Ein Dictionary mit Schadstoffkomponenten als Schlüssel und den zugehörigen Messwerten für verschiedene Zeitpunkte.
    Die Werte werden stundenweise zurückgegeben. Zu lange Zeitspannen resultieren also in einem sehr großen Datenset. Die Komponenten in get_components_anually() sind in diesen stündlichen Messungen oft nicht enthalten. Informationen zur Häufigkeit der Messungen eines Schadstoffs pro Station sind in get_stations_scope_and_span_for_component(component: str) zu finden."""

    try:
        QualityForStationParams(station=station, date_from=date_from, date_to=date_to, time_from=time_from, time_to=time_to)

    except Exception as e:
        return {'error': ('Parameterfehler: ' + str(e))}

    airquality_url = generate_url(UBA_API_BASE, "measures/json",
                                  {"date_from": date_from, "time_from": time_from, "date_to": date_to,
                                   "time_to": time_to, "station": station})

    try:
        response = await make_request(airquality_url)

        if not response or 'data' not in response:
            return {'response': 'Es wurden keine Luftdaten für diese Station für diesen Zeitraum gefunden.'}

        station_data = response['data'][station]

        # Initialize the result dictionary with metadata and components structure
        result = {
            'metadata': {
                'station': station,
                'date_range': f'{date_from} bis {date_to}',
                'time_range': f'{time_from}:00 bis {time_to}:00'
            },
            'components': {}
        }

        # Process each time entry and organize by components
        for start_time, values in station_data.items():
            if not isinstance(values, list) or len(values) < 5:
                continue

            end_time = values[3] if len(values) > 3 else None
            component_id = str(values[0])
            component_name = COMPONENTS_BY_NUMBER.get(component_id, "Unbekannte Komponente")
            component_value = values[4] if len(values) > 4 else None

            # Initialize component entry if it doesn't exist
            if component_name not in result['components']:
                result['components'][component_name] = {}

            # Add the measurement data for this timestamp
            result['components'][component_name][start_time] = {
                'starttime': start_time,
                'endtime': end_time,
                'measurement': component_value
            }
        return result
    except Exception as e:
        return {'error': ('Es ist ein Fehler aufgetreten: ' + str(e))}


@mcp.tool()
def get_components_by_number() -> dict:
    """Gibt die IDs aller Schadstoffe zurück."""
    return {'components:': COMPONENTS_BY_NUMBER}

if __name__ == "__main__":
    mcp.run(transport='stdio')
