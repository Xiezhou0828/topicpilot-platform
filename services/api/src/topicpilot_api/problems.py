from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from topicpilot_api.schemas import ProblemDetails


class ApiProblem(Exception):
    def __init__(self, status: int, title: str, detail: str, problem_type: str) -> None:
        self.status = status
        self.title = title
        self.detail = detail
        self.problem_type = problem_type
        super().__init__(detail)


class NotFoundProblem(ApiProblem):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status=404,
            title="Resource not found",
            detail=detail,
            problem_type="https://topicpilot.example/problems/not-found",
        )


def problem_response(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    problem_type: str,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body = ProblemDetails(
        type=problem_type,
        title=title,
        status=status,
        detail=detail,
        instance=str(request.url.path),
        errors=errors,
    )
    return JSONResponse(
        status_code=status,
        content=body.model_dump(mode="json", by_alias=True, exclude_none=True),
        media_type="application/problem+json",
    )


def install_problem_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiProblem)
    async def api_problem_handler(request: Request, exc: ApiProblem) -> JSONResponse:
        return problem_response(
            request,
            status=exc.status,
            title=exc.title,
            detail=exc.detail,
            problem_type=exc.problem_type,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_problem_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return problem_response(
            request,
            status=422,
            title="Request validation failed",
            detail="One or more request parameters are invalid.",
            problem_type="https://topicpilot.example/problems/validation",
            errors=exc.errors(),
        )

    @app.exception_handler(HTTPException)
    async def http_problem_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return problem_response(
            request,
            status=exc.status_code,
            title="HTTP error",
            detail=str(exc.detail),
            problem_type="https://topicpilot.example/problems/http-error",
        )
