"""FastAPI application exposing study planner endpoints."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status

from .models import StudyPlanCreateRequest, StudyPlanModel
from .service import StudyPlannerService


class PlannerDependencies:
    """Container storing shared service instances for dependency injection."""

    def __init__(self, service: StudyPlannerService) -> None:
        self.service = service

    def get_service(self) -> StudyPlannerService:
        return self.service


def create_app(service: StudyPlannerService | None = None) -> FastAPI:
    """Instantiate a configured FastAPI app for the study planner."""

    planner_service = service or StudyPlannerService()
    dependencies = PlannerDependencies(planner_service)
    app = FastAPI(title="MS2 Study Planner API", version="1.0.0")

    def get_service() -> StudyPlannerService:
        return dependencies.get_service()

    @app.post("/plans", response_model=StudyPlanModel, status_code=status.HTTP_201_CREATED)
    def create_plan(
        payload: StudyPlanCreateRequest, service: StudyPlannerService = Depends(get_service)
    ) -> StudyPlanModel:
        try:
            return service.create_plan(payload)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/plans", response_model=list[StudyPlanModel])
    def list_plans(service: StudyPlannerService = Depends(get_service)) -> list[StudyPlanModel]:
        return service.list_plans()

    @app.get("/plans/{plan_id}", response_model=StudyPlanModel)
    def get_plan(plan_id: str, service: StudyPlannerService = Depends(get_service)) -> StudyPlanModel:
        try:
            return service.get_plan(plan_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_plan(plan_id: str, service: StudyPlannerService = Depends(get_service)) -> None:
        try:
            service.delete_plan(plan_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return app


__all__ = ["create_app"]
