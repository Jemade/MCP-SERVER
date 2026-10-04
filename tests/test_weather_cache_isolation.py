import httpx

from personal_mcp.weather import WeatherClient


async def test_callers_cannot_change_cached_weather():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(200, json={"current": {"temperature_2m": 24}})

    client = WeatherClient(httpx.MockTransport(handle))
    first = await client.forecast(0, 0)
    first["data"]["current"]["temperature_2m"] = 999
    second = await client.forecast(0, 0)
    assert second["data"]["current"]["temperature_2m"] == 24
    second["data"]["current"]["temperature_2m"] = -999
    third = await client.forecast(0, 0)
    assert third["data"]["current"]["temperature_2m"] == 24
    assert third["cached"] and not first["cached"]
    assert len(calls) == 1
