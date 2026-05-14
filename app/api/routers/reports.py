"""Отчёты: список по команде, детали, удаление своих (RLS)."""
from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import CurrentUser, get_current_user, get_db_rls
from app.models import ExerciseInReport, Report
from app.schemas import ReportDetailOut, ReportListItem

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=List[ReportListItem])
def list_reports(
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_rls)],
) -> List[ReportListItem]:
    rows = (
        db.query(Report)
        .options(joinedload(Report.player))
        .order_by(Report.created_at.desc().nulls_last())
        .all()
    )
    out: List[ReportListItem] = []
    for r in rows:
        out.append(
            ReportListItem(
                report_id=r.report_id,
                player_id=r.player_id,
                user_id=r.user_id,
                user_login=r.user_login,
                created_at=r.created_at,
                player_name=r.player.player_name if r.player else None,
            )
        )
    return out


@router.get("/{report_id}", response_model=ReportDetailOut)
def get_report(
    report_id: int,
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_rls)],
) -> ReportDetailOut:
    r = (
        db.query(Report)
        .options(
            joinedload(Report.exercise_in_reports).joinedload(
                ExerciseInReport.exercise
            )
        )
        .filter(Report.report_id == report_id)
        .first()
    )
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отчёт не найден"
        )
    return ReportDetailOut.model_validate(r)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_report(
    report_id: int,
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_rls)],
) -> Response:
    r = db.query(Report).filter(Report.report_id == report_id).first()
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отчёт не найден"
        )
    db.delete(r)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
