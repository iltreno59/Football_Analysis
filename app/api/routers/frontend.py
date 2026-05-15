"""
API endpoints для фронтенда
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import httpx
import jwt
from datetime import datetime, timedelta
import os
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
    Получить гостевой токен для встраивания Superset dashboard.
    Использует JWT для создания токена, который признает Superset.
    """
    try:
        # Читаем секретный ключ из переменных окружения
        secret_key = os.getenv("GUEST_TOKEN_JWT_SECRET", "test-guest-token-secret-key-123")
        
        # Время жизни токена (1 час)
        exp = datetime.utcnow() + timedelta(hours=1)
        
        # Payload для JWT токена (совместимо с Superset)
        payload = {
            "user_id": 1,  # ID гостевого пользователя в Superset
            "username": "guest",
            "email": "guest@localhost",
            "first_name": "Guest",
            "last_name": "User",
            "exp": int(exp.timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
        }
        
        # Кодируем JWT токен
        token = jwt.encode(
            payload,
            secret_key,
            algorithm="HS256"
        )
        
        return {
            "token": token,
            "expiresIn": 3600,  # 1 час в секундах
            "expiresAt": exp.isoformat()
        }
    except Exception as e:
        print(f"Error generating guest token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации токена: {str(e)}")


@router.get("/superset-dashboard/{dashboard_id}", response_class=HTMLResponse)
def get_superset_dashboard_proxy(dashboard_id: int):
    """
    Прокси для встраивания Superset dashboard.
    Решает проблемы с X-Frame-Options и CORS.
    """
    try:
        # Проверяем доступность Superset
        try:
            response = httpx.get("http://localhost:8080/health", timeout=2)
            if response.status_code != 200:
                raise Exception("Superset недоступен")
        except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
            # Superset не запущен - возвращаем HTML с инструкциями
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Apache Superset - Не запущен</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                        max-width: 600px;
                        text-align: center;
                    }}
                    h1 {{ color: #333; margin-top: 0; }}
                    p {{ color: #666; line-height: 1.6; }}
                    .code {{
                        background: #f4f4f4;
                        border-left: 4px solid #667eea;
                        padding: 15px;
                        margin: 20px 0;
                        text-align: left;
                        font-family: monospace;
                        border-radius: 4px;
                        overflow-x: auto;
                    }}
                    .warning {{
                        color: #d9534f;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>⚠️ Apache Superset не запущен</h1>
                    <p>Интерактивная аналитика требует Apache Superset.</p>
                    <p>Запустите один из следующих команд:</p>
                    
                    <h3>Способ 1: Docker (рекомендуется)</h3>
                    <div class="code">
                    docker run -d \\<br>
                      -p 8080:8088 \\<br>
                      --name superset \\<br>
                      apache/superset
                    </div>
                    
                    <h3>Способ 2: Локальная установка</h3>
                    <div class="code">
                    pip install apache-superset<br>
                    superset db upgrade<br>
                    superset fab create-admin<br>
                    superset load_examples<br>
                    superset run -p 8080
                    </div>
                    
                    <p class="warning">После запуска Superset перезагрузите эту страницу.</p>
                </div>
            </body>
            </html>
            """
        
        # Если Superset доступен, перенаправляем на него
        superset_url = f"http://localhost:8080/superset/dashboard/{dashboard_id}/?standalone=true&embed_options=%7B%22native_filters%22:%5B%22allow_all_selectors%22%5D%7D"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Superset Dashboard</title>
            <style>
                body {{ margin: 0; padding: 0; }}
                iframe {{ width: 100%; height: 100vh; border: none; }}
            </style>
        </head>
        <body>
            <iframe src="{superset_url}" sandbox="allow-same-origin allow-scripts allow-popups allow-forms" allow="fullscreen"></iframe>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>❌ Ошибка при загрузке dashboard</h2>
            <p>Детали: {str(e)}</p>
            <p><a href="javascript:location.reload()">Попробовать снова</a></p>
        </body>
        </html>
        """
