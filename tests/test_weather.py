import httpx
import pytest

from personal_mcp.weather import WeatherClient


async def test_forecast_and_cache():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(
            200, json={"current": {"temperature_2m": 24}, "current_units": {"temperature_2m": "°C"}}
        )

    client = WeatherClient(httpx.MockTransport(handle))
    first = await client.forecast(-17.83, 31.05)
    second = await client.forecast(-17.83, 31.05)
    assert first["data"]["current"]["temperature_2m"] == 24
    assert second["cached"]
    assert len(calls) == 1
    assert calls[0].url.host == "api.open-meteo.com"


async def test_retry():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(503 if len(calls) < 3 else 200, json={})

    await WeatherClient(httpx.MockTransport(handle)).forecast(0, 0)
    assert len(calls) == 3


async def test_location_candidates():
    def handle(request):
        assert request.url.params["countryCode"] == "ZW"
        return httpx.Response(200, json={"results": [{"name": "Harare"}]})

    result = await WeatherClient(httpx.MockTransport(handle)).locations("Harare", "zw")
    assert result["data"]["results"][0]["name"] == "Harare"


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(400, json={"error": True}),
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"error": True}),
        httpx.Response(200, content=b"x" * 1_000_001),
    ],
)
async def test_bad_upstream(response):
    client = WeatherClient(httpx.MockTransport(lambda _: response))
    with pytest.raises(ValueError):
        await client.forecast(0, 0)


async def test_timeout():
    def handle(request):
        raise httpx.ReadTimeout("timeout", request=request)

    with pytest.raises(ValueError, match="unavailable"):
        await WeatherClient(httpx.MockTransport(handle)).forecast(0, 0)


@pytest.mark.parametrize("args", [(91, 0, 3), (0, 181, 3), (0, 0, 8)])
async def test_coordinate_validation(args):
    with pytest.raises(ValueError):
        await WeatherClient().forecast(*args)
