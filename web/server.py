"""Kabadi Khata web front end: serves web/ and forwards /api/* to the API.

    make web                      # http://localhost:8600 (API at KK_API_URL, default http://localhost:3000)

The pages call /api/<path> with an X-Principal header; this forwards the method, query, body and that
header unchanged and returns the API's status and body, so a Cedar 403 reaches the page as a 403.
Nothing is decided here: the API and Cedar decide everything.
"""
from __future__ import annotations

import os
from pathlib import Path

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

WEB_DIR = Path(__file__).resolve().parent
FORWARD_HEADERS = ("x-principal", "content-type")


def api_url() -> str:
    return os.getenv("KK_API_URL", "http://localhost:3000").rstrip("/")


async def forward(request: Request) -> Response:
    path = request.path_params["path"]
    headers = {k: v for k, v in request.headers.items() if k.lower() in FORWARD_HEADERS}
    try:
        async with httpx.AsyncClient(timeout=float(os.getenv("KK_API_TIMEOUT", "60"))) as client:
            upstream = await client.request(request.method, f"{api_url()}/{path}", params=request.query_params,
                                            content=await request.body(), headers=headers)
    except httpx.HTTPError:
        return JSONResponse({"detail": f"API unreachable at {api_url()}; start it with `make api`"}, status_code=502)
    return Response(upstream.content, status_code=upstream.status_code,
                    media_type=upstream.headers.get("content-type", "application/json"))


app = Starlette(routes=[
    Route("/api/{path:path}", forward, methods=["GET", "POST", "PUT"]),
    Mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web"),
])

if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("KK_WEB_PORT", "8600")))
