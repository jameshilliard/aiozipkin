import asyncio

import aiohttp
import pytest
from yarl import URL

import aiozipkin as az


@pytest.mark.asyncio  # type: ignore[misc]
async def test_basic(
    jaeger_url: str,
    jaeger_api_url: str,
    client: aiohttp.ClientSession,
    loop: asyncio.AbstractEventLoop,
) -> None:
    endpoint = az.create_endpoint("simple_service", ipv4="127.0.0.1", port=80)
    interval = 50
    tracer = await az.create(
        jaeger_url, endpoint, sample_rate=1.0, send_interval=interval, loop=loop
    )

    with tracer.new_trace(sampled=True) as span:
        span.name("jaeger_span")
        span.tag("span_type", "root")
        span.kind(az.CLIENT)
        span.annotate("SELECT * FROM")
        await asyncio.sleep(0.1)
        span.annotate("start end sql")

    # close forced sending data to server regardless of send interval
    await tracer.close()
    trace_id = span.context.trace_id[-16:]
    url = URL(jaeger_api_url) / "api" / "traces" / trace_id
    resp = await client.get(url, headers={"Content-Type": "application/json"})
    assert resp.status == 200
    data = await resp.json()
    assert data["data"][0]["traceID"] in trace_id
