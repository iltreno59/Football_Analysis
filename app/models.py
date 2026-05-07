from sqlalchemy import Column, Integer, String, Text, Date, Numeric, ForeignKey, SmallInteger, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from .db_conn import Base

class League(Base):
    __tablename__ = "league"
    league_id = Column(Integer, primary_key=True)
    league_name = Column(Text, nullable=False)
    country = Column(Text)
    
    teams = relationship("Team", back_populates="league")
    benchmarks = relationship("Benchmark", back_populates="league")

class Team(Base):
    __tablename__ = "team"
    team_id = Column(Integer, primary_key=True)
    team_name = Column(Text, nullable=False)
    city = Column(Text)
    league_id = Column(Integer, ForeignKey("league.league_id"))
    coach_name = Column(Text)
    
    league = relationship("League", back_populates="teams")
    users = relationship("User", back_populates="team")
    players = relationship("Player", back_populates="team")

class User(Base):
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True)
    user_login = Column(Text, unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    user_role = Column(Text)
    team_id = Column(Integer, ForeignKey("team.team_id"))
    
    team = relationship("Team", back_populates="users")
    reports = relationship("Report", back_populates="user")

class Player(Base):
    __tablename__ = "player"
    player_id = Column(Integer, primary_key=True)
    player_name = Column(Text, nullable=False)
    birth_date = Column(Date)
    national_team = Column(Text)
    position = Column(String(3))
    team_id = Column(Integer, ForeignKey("team.team_id"))
    
    team = relationship("Team", back_populates="players")
    season_metrics = relationship("SeasonMetric", back_populates="player")
    cluster_analyses = relationship("ClusterAnalysis", back_populates="player")
    reports = relationship("Report", back_populates="player")

class Metric(Base):
    __tablename__ = "metric"
    metric_id = Column(Integer, primary_key=True)
    metric_name = Column(Text, nullable=False)
    metric_description = Column(Text)
    metric_category = Column(Text)
    
    season_metrics = relationship("SeasonMetric", back_populates="metric")
    benchmarks = relationship("Benchmark", back_populates="metric")
    exercise_for_metrics = relationship("ExerciseForMetric", back_populates="metric")

class SeasonMetric(Base):
    __tablename__ = "season_metric"
    season_metric_id = Column(Integer, primary_key=True)
    season_start_year = Column(SmallInteger)
    metric_id = Column(Integer, ForeignKey("metric.metric_id"))
    player_id = Column(Integer, ForeignKey("player.player_id"))
    season_metric_value = Column(Numeric(10, 2))
    
    metric = relationship("Metric", back_populates="season_metrics")
    player = relationship("Player", back_populates="season_metrics")

class Role(Base):
    __tablename__ = "role"
    role_id = Column(Integer, primary_key=True)
    role_name = Column(Text, nullable=False)
    zone = Column(String(3))
    role_description = Column(Text)
    
    cluster_analyses = relationship("ClusterAnalysis", back_populates="role")
    benchmarks = relationship("Benchmark", back_populates="role")

class ClusterAnalysis(Base):
    __tablename__ = "cluster_analysis"
    analysis_id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("player.player_id"))
    role_id = Column(Integer, ForeignKey("role.role_id"))
    trust_score = Column(Numeric(4, 2))
    
    player = relationship("Player", back_populates="cluster_analyses")
    role = relationship("Role", back_populates="cluster_analyses")

class Benchmark(Base):
    __tablename__ = "benchmark"
    benchmark_id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("role.role_id"))
    league_id = Column(Integer, ForeignKey("league.league_id"))
    metric_id = Column(Integer, ForeignKey("metric.metric_id"))
    mean = Column(Numeric(10, 2))
    standard_deviation = Column(Numeric(10, 2))
    
    role = relationship("Role", back_populates="benchmarks")
    league = relationship("League", back_populates="benchmarks")
    metric = relationship("Metric", back_populates="benchmarks")

class Exercise(Base):
    __tablename__ = "exercise"
    exercise_id = Column(Integer, primary_key=True)
    exercise_name = Column(Text, nullable=False)
    exercise_description = Column(Text)
    difficulty = Column(SmallInteger)
    recomended_duration = Column(Integer)
    recomended_reps = Column(Integer)
    
    exercise_for_metrics = relationship("ExerciseForMetric", back_populates="exercise")
    exercise_in_reports = relationship("ExerciseInReport", back_populates="exercise")

class ExerciseForMetric(Base):
    __tablename__ = "exercise_for_metric"
    exercise_for_metric_id = Column(Integer, primary_key=True)
    exercise_id = Column(Integer, ForeignKey("exercise.exercise_id"))
    metric_id = Column(Integer, ForeignKey("metric.metric_id"))
    weight = Column(Numeric(2, 1))
    
    exercise = relationship("Exercise", back_populates="exercise_for_metrics")
    metric = relationship("Metric", back_populates="exercise_for_metrics")

class Report(Base):
    __tablename__ = "report"
    report_id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("player.player_id"))
    user_id = Column(Integer, ForeignKey("user.user_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    player = relationship("Player", back_populates="reports")
    user = relationship("User", back_populates="reports")
    exercise_in_reports = relationship("ExerciseInReport", back_populates="report")

class ExerciseInReport(Base):
    __tablename__ = "exercise_in_report"
    exercise_in_report_id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey("report.report_id"))
    exercise_id = Column(Integer, ForeignKey("exercise.exercise_id"))
    
    report = relationship("Report", back_populates="exercise_in_reports")
    exercise = relationship("Exercise", back_populates="exercise_in_reports")