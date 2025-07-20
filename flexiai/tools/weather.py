"""
Weather tool for FlexiAI assistant models.

This tool provides comprehensive weather information using OpenWeatherMap's
One Call API 3.0, including current conditions, forecasts, and alerts.
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from .base import Tool, ToolParameter, ToolResult, ParameterType, ToolExecutionError
from ..config.api_keys import get_api_key
from ..utils import debug_print


class WeatherTool(Tool):
    """
    Weather information tool using OpenWeatherMap One Call API 3.0.

    Provides current weather conditions, hourly forecasts, daily forecasts,
    weather alerts, and comprehensive weather summaries for any location.
    """

    @property
    def name(self) -> str:
        """Return the tool name."""
        return "get_weather"

    @property
    def description(self) -> str:
        """Return tool description."""
        return "Get comprehensive weather information including current conditions, forecasts, and alerts for any location"

    @property
    def parameters(self) -> List[ToolParameter]:
        """Return tool parameters."""
        return [
            ToolParameter(
                name="location",
                param_type=ParameterType.STRING,
                description="Location to get weather for (city name, coordinates, or 'City, Country' format)",
                required=True,
                min_length=1,
                max_length=200
            ),
            ToolParameter(
                name="include_forecast",
                param_type=ParameterType.BOOLEAN,
                description="Include hourly and daily forecasts in the response",
                required=False,
                default=True
            ),
            ToolParameter(
                name="include_alerts",
                param_type=ParameterType.BOOLEAN,
                description="Include weather alerts in the response",
                required=False,
                default=True
            ),
            ToolParameter(
                name="forecast_days",
                param_type=ParameterType.INTEGER,
                description="Number of days to include in daily forecast (1-8)",
                required=False,
                default=5,
                min_value=1,
                max_value=8
            )
        ]

    @property
    def version(self) -> str:
        """Return tool version."""
        return "2.0.0"

    @property
    def category(self) -> str:
        """Return tool category."""
        return "information"

    @property
    def requires_auth(self) -> bool:
        """Return True as this tool requires an OpenWeatherMap API key."""
        return True

    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the weather tool.

        Args:
            location: Location to get weather for
            include_forecast: Whether to include forecasts
            include_alerts: Whether to include alerts
            forecast_days: Number of days for daily forecast

        Returns:
            ToolResult with weather information
        """
        location = kwargs['location']
        include_forecast = kwargs.get('include_forecast', True)
        include_alerts = kwargs.get('include_alerts', True)
        forecast_days = kwargs.get('forecast_days', 5)

        try:
            # Get API key
            api_key = get_api_key('OPENWEATHERMAP_API_KEY')

            debug_print(f"🔑 Weather Tool Execution Debug:")
            debug_print(f"   Location requested: {location}")
            debug_print(f"   Include forecast: {include_forecast}")
            debug_print(f"   Include alerts: {include_alerts}")
            debug_print(f"   Forecast days: {forecast_days}")

            if api_key:
                masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
                debug_print(f"   API key found: {masked_key} (length: {len(api_key)})")
            else:
                debug_print(f"   API key: NOT FOUND")

            if not api_key:
                return ToolResult(
                    success=False,
                    error="OpenWeatherMap API key not found. Set OPENWEATHERMAP_API_KEY environment variable or in .env file.",
                    metadata={
                        "help": "Get your free API key at: https://openweathermap.org/api",
                        "setup": "Add OPENWEATHERMAP_API_KEY=your_key_here to your .env file"
                    }
                )

            # Get coordinates for location
            coords = self._get_coordinates(location, api_key)
            if not coords:
                return ToolResult(
                    success=False,
                    error=f"Could not resolve location: {location}",
                    metadata={"location_input": location}
                )

            # Get weather data from One Call API 3.0
            weather_data = self._fetch_weather_data(coords, api_key, include_forecast, include_alerts)

            # Format the response
            formatted_data = self._format_weather_data(
                weather_data,
                coords.get('name', location),
                include_forecast,
                include_alerts,
                forecast_days
            )

            return ToolResult(
                success=True,
                data=formatted_data,
                metadata={
                    "location_resolved": coords.get('name', location),
                    "coordinates": f"{coords['lat']}, {coords['lon']}",
                    "api_version": "One Call API 3.0",
                    "include_forecast": include_forecast,
                    "include_alerts": include_alerts
                }
            )

        except requests.exceptions.RequestException as e:
            debug_print(f"❌ Network/HTTP error in weather tool:")
            debug_print(f"   Exception type: {type(e).__name__}")
            debug_print(f"   Exception message: {str(e)}")
            debug_print(f"   Location: {location}")
            return ToolResult(
                success=False,
                error=f"Network error: {str(e)}",
                metadata={"error_type": "network", "location": location}
            )
        except Exception as e:
            debug_print(f"❌ Unexpected error in weather tool:")
            debug_print(f"   Exception type: {type(e).__name__}")
            debug_print(f"   Exception message: {str(e)}")
            debug_print(f"   Location: {location}")
            import traceback
            debug_print(f"   Traceback: {traceback.format_exc()}")
            return ToolResult(
                success=False,
                error=f"Weather data unavailable: {str(e)}",
                metadata={"error_type": "general", "location": location}
            )

    def _get_coordinates(self, location: str, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Get coordinates for a location using OpenWeatherMap Geocoding API.
        """
        try:
            # Parse if location is already coordinates (lat,lon)
            if ',' in location:
                parts = [part.strip() for part in location.split(',')]
                if len(parts) == 2:
                    try:
                        lat, lon = float(parts[0]), float(parts[1])
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            return {
                                'lat': lat,
                                'lon': lon,
                                'name': f"Coordinates ({lat}, {lon})"
                            }
                    except ValueError:
                        pass

            # Use geocoding API
            geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
            params = {
                'q': location,
                'limit': 1,
                'appid': api_key
            }

            debug_print(f"🌍 Geocoding API Request:")
            debug_print(f"   URL: {geocoding_url}")
            debug_print(f"   Params: {params}")

            response = requests.get(geocoding_url, params=params, timeout=10)

            debug_print(f"🌍 Geocoding API Response:")
            debug_print(f"   Status: {response.status_code}")
            debug_print(f"   Headers: {dict(response.headers)}")
            debug_print(f"   Content: {response.text}")

            if response.status_code == 200:
                data = response.json()
                if data:
                    geo_data = data[0]
                    return {
                        'lat': geo_data['lat'],
                        'lon': geo_data['lon'],
                        'name': f"{geo_data.get('name', location)}, {geo_data.get('country', '')}"
                    }

            debug_print(f"❌ Geocoding failed for {location}: HTTP {response.status_code}")
            debug_print(f"   Response text: {response.text}")
            return None

        except Exception as e:
            debug_print(f"❌ Geocoding exception for {location}:")
            debug_print(f"   Exception type: {type(e).__name__}")
            debug_print(f"   Exception message: {str(e)}")
            import traceback
            debug_print(f"   Traceback: {traceback.format_exc()}")
            return None

    def _fetch_weather_data(self, coords: Dict[str, Any], api_key: str,
                           include_forecast: bool, include_alerts: bool) -> Dict[str, Any]:
        """
        Fetch weather data from One Call API 3.0.
        """
        url = "https://api.openweathermap.org/data/3.0/onecall"

        # Build exclusions to save API quota
        exclude_parts = ['minutely']  # Always exclude minutely
        if not include_forecast:
            exclude_parts.extend(['hourly', 'daily'])
        if not include_alerts:
            exclude_parts.append('alerts')

        params = {
            'lat': coords['lat'],
            'lon': coords['lon'],
            'appid': api_key,
            'units': 'metric',
            'exclude': ','.join(exclude_parts) if exclude_parts else None
        }

        debug_print(f"Fetching weather data for {coords.get('name', 'coordinates')}")
        debug_print(f"🌤️ One Call API Request:")
        debug_print(f"   URL: {url}")
        debug_print(f"   Params: {params}")

        # Retry logic for network issues
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=15)
                break  # Success, exit retry loop
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt == max_retries - 1:  # Last attempt
                    debug_print(f"🌤️ API Request failed after {max_retries} attempts: {e}")
                    raise e
                else:
                    debug_print(f"🌤️ API Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                    debug_print(f"🌤️ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

        debug_print(f"🌤️ One Call API Response:")
        debug_print(f"   Status: {response.status_code}")
        debug_print(f"   Headers: {dict(response.headers)}")
        debug_print(f"   Content: {response.text}")

        # Handle API errors
        if response.status_code == 401:
            raise ToolExecutionError("Invalid API key or One Call API 3.0 subscription required")
        elif response.status_code == 404:
            raise ToolExecutionError(f"Invalid coordinates for location")
        elif response.status_code == 429:
            raise ToolExecutionError("API rate limit exceeded. Try again later.")

        response.raise_for_status()
        return response.json()

    def _format_weather_data(self, data: Dict[str, Any], location_name: str,
                           include_forecast: bool, include_alerts: bool,
                           forecast_days: int) -> Dict[str, Any]:
        """
        Format weather data into a structured response.
        """
        current = data.get('current', {})
        hourly = data.get('hourly', [])
        daily = data.get('daily', [])
        alerts = data.get('alerts', [])

        # Format current conditions
        formatted_data = {
            "location": location_name,
            "current": {
                "temperature": f"{round(current.get('temp', 0))}°C",
                "condition": current.get('weather', [{}])[0].get('description', 'Unknown').title(),
                "humidity": f"{current.get('humidity', 0)}%",
                "wind": self._format_wind_info(current),
                "pressure": f"{current.get('pressure', 0)} hPa",
                "visibility": f"{current.get('visibility', 0)} meters",
                "feels_like": f"{round(current.get('feels_like', 0))}°C",
                "uv_index": round(current.get('uvi', 0), 1),
                "clouds": f"{current.get('clouds', 0)}%",
                "timestamp": current.get('dt', 0)
            }
        }

        # Add forecasts if requested
        if include_forecast:
            formatted_data["forecast"] = {}

            if hourly:
                formatted_data["forecast"]["next_24h"] = self._format_hourly_forecast(hourly[:24])

            if daily:
                formatted_data["forecast"]["daily"] = self._format_daily_forecast(daily[:forecast_days])

        # Add alerts if requested and available
        if include_alerts and alerts:
            formatted_data["alerts"] = self._format_weather_alerts(alerts)
        elif include_alerts:
            formatted_data["alerts"] = []

        # Add comprehensive summary
        formatted_data["summary"] = self._generate_weather_summary(current, daily, alerts)

        return formatted_data

    def _format_wind_info(self, current_data: Dict) -> str:
        """Format wind information."""
        speed = current_data.get('wind_speed', 0)  # m/s
        speed_kmh = round(speed * 3.6)  # Convert to km/h

        direction = current_data.get('wind_deg')
        gust = current_data.get('wind_gust')

        wind_parts = [f"{speed_kmh} km/h"]

        if direction is not None:
            dir_str = self._wind_direction(direction)
            wind_parts.append(dir_str)

        if gust and gust > speed:
            gust_kmh = round(gust * 3.6)
            wind_parts.append(f"(gusts up to {gust_kmh} km/h)")

        return " ".join(wind_parts)

    def _wind_direction(self, degrees: float) -> str:
        """Convert wind direction from degrees to cardinal direction."""
        if degrees is None:
            return ""

        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]

    def _format_hourly_forecast(self, hourly_data: List) -> List[Dict]:
        """Format hourly forecast data."""
        forecast = []
        for i, hour in enumerate(hourly_data):
            forecast.append({
                "hour": i + 1,
                "timestamp": hour.get('dt', 0),
                "temperature": f"{round(hour.get('temp', 0))}°C",
                "condition": hour.get('weather', [{}])[0].get('description', '').title(),
                "precipitation_chance": f"{round(hour.get('pop', 0) * 100)}%",
                "wind_speed": f"{round(hour.get('wind_speed', 0) * 3.6)} km/h"
            })
        return forecast

    def _format_daily_forecast(self, daily_data: List) -> List[Dict]:
        """Format daily forecast data."""
        forecast = []
        for i, day in enumerate(daily_data):
            temp = day.get('temp', {})
            forecast.append({
                "day": i + 1,
                "timestamp": day.get('dt', 0),
                "condition": day.get('weather', [{}])[0].get('description', '').title(),
                "temperature_high": f"{round(temp.get('max', 0))}°C",
                "temperature_low": f"{round(temp.get('min', 0))}°C",
                "precipitation_chance": f"{round(day.get('pop', 0) * 100)}%",
                "humidity": f"{day.get('humidity', 0)}%",
                "wind_speed": f"{round(day.get('wind_speed', 0) * 3.6)} km/h",
                "uv_index": round(day.get('uvi', 0), 1),
                "summary": day.get('summary', 'No summary available')
            })
        return forecast

    def _format_weather_alerts(self, alerts: List) -> List[Dict]:
        """Format weather alerts."""
        formatted_alerts = []
        for alert in alerts:
            formatted_alerts.append({
                "event": alert.get('event', 'Weather Alert'),
                "description": alert.get('description', 'No description available'),
                "start": alert.get('start', 0),
                "end": alert.get('end', 0),
                "sender": alert.get('sender_name', 'Weather Service'),
                "tags": alert.get('tags', [])
            })
        return formatted_alerts

    def _generate_weather_summary(self, current: Dict, daily: List, alerts: List) -> str:
        """Generate a comprehensive weather summary."""
        try:
            condition = current.get('weather', [{}])[0].get('description', 'unknown')
            temp = round(current.get('temp', 0))
            feels_like = round(current.get('feels_like', 0))
            humidity = current.get('humidity', 0)
            uvi = current.get('uvi', 0)

            summary_parts = [f"Currently {condition} with temperature {temp}°C (feels like {feels_like}°C)."]

            # Add humidity context
            if humidity > 80:
                summary_parts.append("High humidity.")
            elif humidity < 30:
                summary_parts.append("Low humidity - air feels dry.")

            # Add UV context
            if uvi > 6:
                summary_parts.append("High UV index - sun protection recommended.")
            elif uvi > 3:
                summary_parts.append("Moderate UV levels.")

            # Add alerts context
            if alerts:
                alert_count = len(alerts)
                summary_parts.append(f"⚠️ {alert_count} weather alert{'s' if alert_count > 1 else ''} active.")

            # Add tomorrow's outlook if available
            if daily and len(daily) > 1:
                tomorrow = daily[1]
                tomorrow_condition = tomorrow.get('weather', [{}])[0].get('description', '')
                if tomorrow_condition:
                    summary_parts.append(f"Tomorrow: {tomorrow_condition}.")

            return " ".join(summary_parts)

        except (KeyError, TypeError, IndexError):
            return f"Current conditions: {condition}."
