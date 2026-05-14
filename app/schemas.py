from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Optional, List

# --- БАЗОВАЯ КОНФИГУРАЦИЯ ---
class BaseSchema(BaseModel):
    """Базовый класс для всех схем ответа, чтобы работал маппинг с SQLAlchemy."""
    model_config = ConfigDict(from_attributes=True)

# --- LEAGUE (Лиги) ---
class LeagueBase(BaseModel):
    league_name: str
    country: Optional[str] = None

class LeagueCreate(LeagueBase):
    pass

class League(LeagueBase, BaseSchema):
    league_id: int

# --- TEAM (Команды) ---
class TeamBase(BaseModel):
    team_name: str
    city: Optional[str] = None
    league_id: int
    coach_name: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class Team(TeamBase, BaseSchema):
    team_id: int

# --- USER (Пользователи) ---
class UserBase(BaseModel):
    user_login: str
    user_role: Optional[str] = None
    team_id: Optional[int] = None

class UserCreate(UserBase):
    password: str # Принимается пароль для хэширования, но не хранится в схеме User

class User(UserBase, BaseSchema):
    user_id: int

# --- EXERCISE (Упражнения) ---
class ExerciseBase(BaseModel):
    exercise_name: str
    exercise_description: Optional[str] = None
    difficulty: Optional[int] = None # SmallInteger в моделях

class ExerciseCreate(ExerciseBase):
    pass

class Exercise(ExerciseBase, BaseSchema):
    exercise_id: int

# --- METRIC (Справочник метрик) ---
class MetricBase(BaseModel):
    metric_name: str
    metric_description: Optional[str] = None
    metric_category: Optional[str] = None

class MetricCreate(MetricBase):
    pass

# --- ПРОСЛОЙКА УПРАЖНЕНИЕ-МЕТРИКА (С сохранением weight) ---
class ExerciseForMetricBase(BaseModel):
    exercise_id: int
    metric_id: int
    weight: float = Field(..., ge=0, le=1.0) # Атрибут веса из модели

class ExerciseForMetricCreate(ExerciseForMetricBase):
    pass

class ExerciseForMetric(ExerciseForMetricBase, BaseSchema):
    exercise_for_metric_id: int
    exercise: Optional[Exercise] = None # Вложенное упражнение

# Финальная схема метрики со списком упражнений и их весами
class Metric(MetricBase, BaseSchema):
    metric_id: int
    exercise_for_metrics: List[ExerciseForMetric] = [] # Связь 1:M к прослойке

# --- PLAYER (Игроки) ---
class PlayerBase(BaseModel):
    player_name: str
    birth_date: Optional[date] = None
    national_team: Optional[str] = None
    position: Optional[str] = None
    team_id: int

class PlayerCreate(PlayerBase):
    pass

class Player(PlayerBase, BaseSchema):
    player_id: int
    team: Optional[Team] = None

# --- SEASON METRIC (Статистика) ---
class SeasonMetricBase(BaseModel):
    season_start_year: int # SmallInteger в моделях
    metric_id: int
    player_id: int
    season_metric_value: float # Numeric(10,2)

class SeasonMetricCreate(SeasonMetricBase):
    pass

class SeasonMetric(SeasonMetricBase, BaseSchema):
    season_metric_id: int
    metric: Optional[Metric] = None

# --- ROLE (Тактические роли) ---
class RolesBase(BaseModel):
    role_name: str
    zone: Optional[str] = Field(None, max_length=3)
    role_description: Optional[str] = None

class RolesCreate(RolesBase):
    pass

class Roles(RolesBase, BaseSchema):
    role_id: int

# --- BENCHMARK (Эталоны) ---
class BenchmarkBase(BaseModel):
    role_id: int
    league_id: int
    metric_id: int
    mean: float
    standard_deviation: float

class BenchmarkCreate(BenchmarkBase):
    pass

class Benchmark(BenchmarkBase, BaseSchema):
    benchmark_id: int

# --- CLUSTER ANALYSIS (Результаты кластеризации) ---
class ClusterAnalysisBase(BaseModel):
    player_id: int
    role_id: int
    trust_score: float # Numeric(4,2)

class ClusterAnalysisCreate(ClusterAnalysisBase):
    pass

class ClusterAnalysis(ClusterAnalysisBase, BaseSchema):
    analysis_id: int
    roles: Optional[Roles] = None

# --- ПРОСЛОЙКА УПРАЖНЕНИЕ-ОТЧЕТ ---
class ExerciseInReportBase(BaseModel):
    report_id: int
    exercise_id: int

class ExerciseInReportCreate(ExerciseInReportBase):
    pass

class ExerciseInReport(ExerciseInReportBase, BaseSchema):
    exercise_in_report_id: int
    exercise: Optional[Exercise] = None

# --- REPORT (Отчеты) ---
class ReportBase(BaseModel):
    player_id: int
    user_id: int

class ReportCreate(ReportBase):
    exercise_ids: List[int] = [] # Список ID упражнений для добавления при создании

class Report(ReportBase, BaseSchema):
    report_id: int
    created_at: datetime
    user_login: Optional[str] = None
    exercise_in_reports: List[ExerciseInReport] = [] # Список упражнений в отчете


# --- API (аутентификация и списки) ---
class LoginRequest(BaseModel):
    user_login: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PlayerListOut(BaseModel):
    """Игрок в списке с опциональной командой (для ответа GET /players)."""
    model_config = ConfigDict(from_attributes=True)

    player_id: int
    player_name: str
    birth_date: Optional[date] = None
    position: Optional[str] = None
    team_id: Optional[int] = None
    team: Optional[Team] = None