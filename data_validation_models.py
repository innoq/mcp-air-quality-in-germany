from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, field_validator, Field

COMPONENTS_BY_NUMBER = {
    '1': 'Feinstaub (PM10)',
    '2': 'Kohlenmonoxid',
    '3': 'Ozon',
    '4': 'Schwefeldioxid',
    '5': 'Stickstoffdioxid',
    '6': 'Blei im Feinstaub',
    '7': 'Benzo(a)pyren im Feinstaub',
    '8': 'Benzol',
    '9': 'Feinstaub (PM2,5)',
    '10': 'Arsen im Feinstaub',
    '11': 'Cadmium im Feinstaub',
    '12': 'Nickel im Feinstaub'
}

class ComponentsAnnuallyParams(BaseModel):
    year: str
    component: str

    @field_validator('year')
    def validate_year(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError('Jahr muss im Format YYYY sein')
        return v

    @field_validator('component')
    def validate_component(cls, v):
        if v not in COMPONENTS_BY_NUMBER:
            raise ValueError(
                f'Ungültige Komponenten-ID. Muss eine der folgenden sein: {", ".join(COMPONENTS_BY_NUMBER.keys())}')
        return v


class StationsForComponentParams(BaseModel):
    component: str

    @field_validator('component')
    def validate_component(cls, v):
        if v not in COMPONENTS_BY_NUMBER:
            raise ValueError(
                f'Ungültige Komponenten-ID. Muss eine der folgenden sein: {", ".join(COMPONENTS_BY_NUMBER.keys())}')
        return v

class MetadataParams(BaseModel):
    timezone: str

    @field_validator('timezone')
    def validate_timezone(cls, v):
        try:
            ZoneInfo(v)
            return v
        except Exception:
            raise ValueError(f'Ungültige Zeitzone: {v}')



class StationsNearbyParams(BaseModel):
    post_code: str

    @field_validator('post_code')
    def validate_post_code(cls, v):
        if not v.isdigit() or len(v) != 5:
            raise ValueError('Postleitzahl muss 5-stellig sein')
        return v


class QualityForStationNowParams(BaseModel):
    station: str
    timezone: str = Field(default="Europe/Berlin")

    @field_validator('station')
    def validate_station(cls, v):
        if not v.isdigit():
            raise ValueError('Stations-ID muss numerisch sein')
        return v

    @field_validator('timezone')
    def validate_timezone(cls, v):
        try:
            ZoneInfo(v)
            return v
        except Exception:
            raise ValueError(f'Ungültige Zeitzone: {v}')


class QualityForStationParams(BaseModel):
    station: str
    date_from: str
    date_to: str
    time_from: str
    time_to: str

    @field_validator('station')
    def validate_station(cls, v):
        if not v.isdigit():
            raise ValueError('Stations-ID muss numerisch sein')
        return v

    @field_validator('date_from', 'date_to')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError('Datum muss im Format YYYY-MM-DD sein')

    @field_validator('time_from', 'time_to')
    def validate_time(cls, v):
        if not (v.isdigit() and int(v) in range(24)):
            raise ValueError('Zeit muss im Format HH und im Bereich 00-23 sein')
        return v