"""
API endpoints для фронтенда
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import (
    Player, ClusterAnalysis, Roles, Report, ExerciseInReport, Exercise,
    Benchmark, SeasonMetric, Team, League
)
from app.core.db_conn import SessionLocal
from app.ai.analyzer import recommend_exercises_for_player

router = APIRouter(prefix="/api", tags=["frontend"])


def get_db():
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Получить основную статистику"""
    try:
        total_players = db.query(Player).count()
        total_roles = db.query(Roles).distinct().count()
        total_reports = db.query(Report).count()
        
        return {
            "totalPlayers": total_players,
            "totalRoles": total_roles,
            "totalReports": total_reports
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/players/search")
def search_players(name: str, db: Session = Depends(get_db)):
    """Поиск игрока по имени"""
    try:
        player = db.query(Player).filter(
            Player.player_name.ilike(f"%{name}%")
        ).first()
        
        if not player:
            raise HTTPException(status_code=404, detail="Игрок не найден")
        
        # Получаем роль
        cluster = db.query(ClusterAnalysis).filter(
            ClusterAnalysis.player_id == player.player_id
        ).order_by(ClusterAnalysis.trust_score.desc()).first()
        
        role_name = cluster.roles.role_name if cluster else "Не определена"
        team_name = player.team.team_name if player.team else "Неизвестна"
        
        return {
            "player_id": player.player_id,
            "player_name": player.player_name,
            "position": player.position,
            "team_name": team_name,
            "role_name": role_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/players/{player_id}/recommendations")
def get_player_recommendations(player_id: int, db: Session = Depends(get_db)):
    """Получить рекомендации упражнений для игрока"""
    try:
        # Используем функцию из analyzer
        result = recommend_exercises_for_player(player_id=player_id)
        
        if not result.get('success'):
            raise HTTPException(status_code=404, detail=result.get('error', 'Ошибка'))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports")
def get_reports(db: Session = Depends(get_db)):
    """Получить список всех отчётов"""
    try:
        reports = db.query(
            Report.report_id,
            Player.player_name,
            Player.position,
            Team.team_name,
            Report.created_at,
            func.count(ExerciseInReport.exercise_id).label('exercise_count')
        ).join(Player, Report.player_id == Player.player_id).outerjoin(
            Team, Player.team_id == Team.team_id
        ).outerjoin(
            ExerciseInReport, Report.report_id == ExerciseInReport.report_id
        ).group_by(
            Report.report_id, Player.player_name, Player.position,
            Team.team_name, Report.created_at
        ).order_by(Report.created_at.desc()).all()
        
        return [
            {
                "report_id": r[0],
                "player_name": r[1],
                "position": r[2],
                "team_name": r[3],
                "created_at": r[4],
                "exercise_count": r[5]
            }
            for r in reports
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}")
def get_report_details(report_id: int, db: Session = Depends(get_db)):
    """Получить детали отчёта"""
    try:
        report = db.query(Report).filter(Report.report_id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Отчёт не найден")
        
        player = report.player
        team = player.team
        
        # Получаем роль
        cluster = db.query(ClusterAnalysis).filter(
            ClusterAnalysis.player_id == player.player_id
        ).order_by(ClusterAnalysis.trust_score.desc()).first()
        
        # Получаем упражнения
        exercises = db.query(Exercise).join(
            ExerciseInReport, Exercise.exercise_id == ExerciseInReport.exercise_id
        ).filter(ExerciseInReport.report_id == report_id).all()
        
        return {
            "report_id": report.report_id,
            "player_name": player.player_name,
            "position": player.position,
            "team_name": team.team_name if team else "Неизвестна",
            "role_name": cluster.roles.role_name if cluster else "Не определена",
            "created_at": report.created_at,
            "exercises": [
                {
                    "exercise_id": e.exercise_id,
                    "exercise_name": e.exercise_name,
                    "exercise_description": e.exercise_description,
                    "difficulty": e.difficulty
                }
                for e in exercises
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/superset-token")
def get_superset_token():
    """
    Получить гостевой токен для Superset (заглушка).
    В production нужно получить реальный токен от Superset API.
    """
    try:
        # TODO: Реализовать получение реального токена от Superset
        # Для теста просто возвращаем пустой токен
        return {
            "token": "guest_token_placeholder",
            "expiresIn": 3600
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
