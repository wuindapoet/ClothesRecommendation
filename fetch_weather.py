import requests
from statistics import mean

# --- WEATHER CODE MAP ---
WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm with hail"
}

def fetch_weather_data(lat, lng):
    # --- FETCH WEATHER DATA ---
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
        "forecast_days": 14,
        "timezone": "Asia/Singapore"
    }

    response = requests.get(url, params=params)
    data = response.json()
    return data

def process_weather_data(data):
    """data fetched from fetch_weather_data, pass as is, don't change
    {'selectedOption1': 'option2', 'selectedOption2': '', 'location': {'lat': 30.90850901987831, 'lng': 121.47644044831395}}"""

def categorize_season(weather_data: dict) -> str:
    # Use absolute value to handle Northern and Southern hemispheres equally
    lat = abs(weather_data.get('latitude', 0))

    max_temps = weather_data.get('temperature_2m_max', [])
    min_temps = weather_data.get('temperature_2m_min', [])

    if not max_temps or not min_temps:
        return "Autumn" # Default to this season if no available data

    # Calculate the average temperature across the period
    daily_avgs = [(mx + mn) / 2 for mx, mn in zip(max_temps, min_temps)]
    avg_t = sum(daily_avgs) / len(daily_avgs)

    # 1. Tropical Zones (0° - 23.5°)
    # Small temp fluctuations. Thresholds are high.
    if lat < 23.5:
        if avg_t < 22: return "Winter"
        if avg_t < 25: return "Spring"
        if avg_t < 28: return "Autumn"
        return "Summer"

    # 2. Subtropical & Temperate Zones (23.5° - 55°)
    # Defined by clear seasonality.
    elif lat < 55:
        if avg_t < 8:  return "Winter"
        if avg_t < 16: return "Spring"
        if avg_t < 24: return "Autumn"
        return "Summer"

    # 3. Polar / Subpolar Zones (55°+)
    # Lower thresholds; anything above 10°C is effectively Summer.
    else:
        if avg_t < 0:  return "Winter"
        if avg_t < 6:  return "Spring"
        if avg_t < 11: return "Autumn"
        return "Summer"

def print_test(data):
    daily = data['daily']
    # --- FORMAT & PRINT ---
    print("\n===== 14-Day Weather Forecast =====\n")

    for i in range(len(daily["time"])):
        date = daily["time"][i]
        tmax = daily["temperature_2m_max"][i]
        tmin = daily["temperature_2m_min"][i]
        rain = daily["precipitation_sum"][i]
        code = daily["weathercode"][i]
        label = WEATHER_CODE_MAP.get(code, "Unknown")

        print(f"{date}")
        print(f"  · Weather: {label} (code {code})")
        print(f"  · Max Temp: {tmax}°C")
        print(f"  · Min Temp: {tmin}°C")
        print(f"  · Rain: {rain} mm")
        print()
