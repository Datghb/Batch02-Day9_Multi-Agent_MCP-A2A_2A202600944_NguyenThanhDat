"""FastAPI dashboard for visualising multi-agent state execution."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from time import perf_counter
from urllib.parse import unquote

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from stages.stage_4_milti_agent.main import create_graph

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Multi-Agent State Dashboard")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


SERVICES = [
    {"id": "registry", "name": "Registry", "url": "http://localhost:10000"},
    {"id": "customer", "name": "Customer Agent", "url": "http://localhost:10100"},
    {"id": "law", "name": "Law Agent", "url": "http://localhost:10101"},
    {"id": "tax", "name": "Tax Agent", "url": "http://localhost:10102"},
    {"id": "compliance", "name": "Compliance Agent", "url": "http://localhost:10103"},
]


NODE_LABELS = {
    "analyze_law": "Analyze Law",
    "check_routing": "Check Routing",
    "call_tax_specialist": "Tax Specialist",
    "call_compliance_specialist": "Compliance Specialist",
    "call_privacy_specialist": "Privacy Specialist",
    "aggregate": "Aggregate",
}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/services")
async def services() -> dict:
    async with httpx.AsyncClient(timeout=2.0) as client:
        checks = await asyncio.gather(
            *[_check_service(client, service) for service in SERVICES],
            return_exceptions=True,
        )
    return {"services": checks}


async def _check_service(client: httpx.AsyncClient, service: dict) -> dict:
    if service["id"] == "registry":
        endpoint = f"{service['url']}/discover/legal_question"
    else:
        endpoint = f"{service['url']}/.well-known/agent.json"

    started = perf_counter()
    try:
        response = await client.get(endpoint)
        elapsed = round((perf_counter() - started) * 1000)
        return {
            **service,
            "status": "online" if response.status_code < 400 else "error",
            "status_code": response.status_code,
            "latency_ms": elapsed,
        }
    except Exception as exc:
        elapsed = round((perf_counter() - started) * 1000)
        return {
            **service,
            "status": "offline",
            "status_code": None,
            "latency_ms": elapsed,
            "error": str(exc),
        }


@app.get("/api/run-stage4")
async def run_stage4(question: str) -> StreamingResponse:
    async def event_stream():
        decoded_question = unquote(question).strip()
        if not decoded_question:
            decoded_question = (
                "If a company breaks a contract, avoids taxes, and leaks customer data, "
                "what are the legal, regulatory, and privacy consequences?"
            )

        started = perf_counter()
        yield _sse(
            "reset",
            {
                "question": decoded_question,
                "nodes": [
                    {"id": node_id, "label": label, "status": "pending"}
                    for node_id, label in NODE_LABELS.items()
                ],
            },
        )

        graph = create_graph()
        state = {
            "question": decoded_question,
            "law_analysis": "",
            "needs_tax": False,
            "needs_compliance": False,
            "needs_privacy": False,
            "tax_result": "",
            "compliance_result": "",
            "privacy_result": "",
            "final_answer": "",
        }

        try:
            async for chunk in graph.astream(state, stream_mode="updates"):
                for node_id, update in chunk.items():
                    elapsed = round(perf_counter() - started, 2)
                    yield _sse(
                        "node",
                        {
                            "id": node_id,
                            "label": NODE_LABELS.get(node_id, node_id),
                            "status": "completed",
                            "elapsed": elapsed,
                            "summary": _summarise_update(update),
                            "update": _compact_update(update),
                        },
                    )
                    if "final_answer" in update:
                        yield _sse(
                            "answer",
                            {
                                "answer": update["final_answer"],
                                "elapsed": elapsed,
                            },
                        )

            yield _sse("done", {"elapsed": round(perf_counter() - started, 2)})
        except Exception as exc:
            yield _sse(
                "error",
                {
                    "message": str(exc),
                    "elapsed": round(perf_counter() - started, 2),
                },
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/run-demo")
async def run_demo(question: str) -> StreamingResponse:
    async def event_stream():
        decoded_question = unquote(question).strip()
        if not decoded_question:
            decoded_question = "Demo multi-agent legal request"

        started = perf_counter()
        yield _sse(
            "reset",
            {
                "question": decoded_question,
                "nodes": [
                    {"id": node_id, "label": label, "status": "pending"}
                    for node_id, label in NODE_LABELS.items()
                ],
            },
        )

        demo_updates = [
            (
                "analyze_law",
                {
                    "law_analysis": (
                        "The company faces contract liability, possible tax enforcement, "
                        "and privacy/regulatory exposure if customer data is involved."
                    )
                },
            ),
            (
                "check_routing",
                {"needs_tax": True, "needs_compliance": True, "needs_privacy": True},
            ),
            (
                "call_tax_specialist",
                {
                    "tax_result": (
                        "Tax specialist: distinguish lawful avoidance from illegal evasion; "
                        "risk includes back taxes, interest, civil fraud penalties, and criminal referral."
                    )
                },
            ),
            (
                "call_compliance_specialist",
                {
                    "compliance_result": (
                        "Compliance specialist: possible FTC, SEC, SOX, AML, or industry-specific "
                        "reporting duties depending on the facts."
                    )
                },
            ),
            (
                "call_privacy_specialist",
                {
                    "privacy_result": (
                        "Privacy specialist: data leaks may trigger breach notification, GDPR/CCPA "
                        "penalties, consumer claims, and remediation duties."
                    )
                },
            ),
            (
                "aggregate",
                {
                    "final_answer": (
                        "Demo final answer:\n\n"
                        "1. Contract breach can create damages, injunction, restitution, and business risk.\n"
                        "2. Tax evasion can create back-tax liability, penalties, interest, and criminal exposure.\n"
                        "3. Data leakage can trigger privacy notices, regulator investigations, consumer claims, "
                        "and compliance remediation.\n\n"
                        "This demo mode shows the state flow without calling Gemini, so it does not hit API quota."
                    )
                },
            ),
        ]

        for node_id, update in demo_updates:
            await asyncio.sleep(0.55)
            elapsed = round(perf_counter() - started, 2)
            yield _sse(
                "node",
                {
                    "id": node_id,
                    "label": NODE_LABELS.get(node_id, node_id),
                    "status": "completed",
                    "elapsed": elapsed,
                    "summary": _summarise_update(update),
                    "update": update,
                },
            )
            if "final_answer" in update:
                yield _sse("answer", {"answer": update["final_answer"], "elapsed": elapsed})

        yield _sse("done", {"elapsed": round(perf_counter() - started, 2)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _compact_update(update: dict) -> dict:
    compact = {}
    for key, value in update.items():
        if isinstance(value, str):
            compact[key] = value[:700]
        else:
            compact[key] = value
    return compact


def _summarise_update(update: dict) -> str:
    if "needs_tax" in update or "needs_compliance" in update or "needs_privacy" in update:
        return (
            f"tax={update.get('needs_tax')} "
            f"compliance={update.get('needs_compliance')} "
            f"privacy={update.get('needs_privacy')}"
        )
    for key in (
        "law_analysis",
        "tax_result",
        "compliance_result",
        "privacy_result",
        "final_answer",
    ):
        value = update.get(key)
        if value:
            return f"{len(value)} characters"
    return "state updated"


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
