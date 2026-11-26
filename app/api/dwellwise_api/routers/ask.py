from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..ai_client import AiUnavailable
from ..ai_tools import AppTools
from ..ask import Limited
from ..schemas import Answer, AssistantStatus, ErrorBody, Question

router = APIRouter(prefix="/v1", tags=["assistant"])


def _visitor(request: Request) -> str:
    """The client's address for the hourly limit (first in Render's X-Forwarded-For). Never logged."""
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


@router.get("/assistant", response_model=AssistantStatus)
def assistant_status(request: Request) -> AssistantStatus:
    """Whether the assistant is on. Costs no quota: the web app asks before showing the question box."""
    return AssistantStatus(enabled=getattr(request.app.state, "ai", None) is not None)


@router.post(
    "/ask",
    response_model=Answer,
    responses={422: {"model": ErrorBody}, 429: {"model": ErrorBody}, 503: {"model": ErrorBody}},
)
async def ask(question: Question, request: Request) -> Answer:
    """A question about Irish towns, answered from DwellWise's data, every number checked first."""
    service = getattr(request.app.state, "ai", None)
    if service is None:
        raise HTTPException(
            503, "The assistant is switched off. Every other part of DwellWise works without it."
        )
    try:
        result = await service.ask(
            question.question,
            question.settlement,
            _visitor(request),
            AppTools(request.app),
            [h.model_dump() for h in question.history],
        )
    except Limited as exc:
        raise HTTPException(429, str(exc)) from exc
    except AiUnavailable as exc:
        raise HTTPException(503, "The assistant cannot reach its model right now. Try again later.") from exc
    return Answer(
        answer=result["answer"],
        grounded=result["grounded"],
        tools=result["tools"],
        cached=result["cached"],
        shortlists=result.get("shortlists", []),
    )
