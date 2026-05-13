"""
Модуль анализа производительности игроков и рекомендации упражнений
"""
from app.core.db_conn import SessionLocal
from app.models import (
    Player,
    ClusterAnalysis,
    Benchmark,
    SeasonMetric,
    ExerciseForMetric,
    Report,
    ExerciseInReport,
)

# Пороги в единицах стандартного отклонения (Z-score относительно бенчмарка роли/лиги)
Z_DEFICIT_THRESHOLD = -1.0
Z_SEVERE_THRESHOLD = -2.0
# При Z <= Z_SEVERE_THRESHOLD — только упражнения с difficulty не выше этого значения
SEVERE_MAX_EXERCISE_DIFFICULTY = 5


def recommend_exercises_for_player(
    player_id, user_id=None, user_login=None, season_year=None
):
    """
    Анализирует метрики игрока и рекомендует упражнения на основе отклонений от бенчмарков.
    
    Логика:
    - Z-score <= Z_DEFICIT_THRESHOLD (-1): метрика в дефиците, подбираются упражнения
    - если хотя бы одна метрика с Z <= Z_SEVERE_THRESHOLD (-2): в отчёт попадают
      только упражнения с difficulty <= SEVERE_MAX_EXERCISE_DIFFICULTY (5);
      упражнения без оценки сложности (NULL) не отсекаются
    
    Args:
        player_id: ID игрока
        user_id: ID пользователя (опционально, может быть None)
        user_login: Логин автора отчёта (опционально; пока допускается None)
        season_year: Год сезона для фильтра (если None, берутся все сезоны)
    
    Returns:
        dict с ключами success, player_name, role; при успехе с рекомендациями —
        deficit_count, deficits, exercises_count, exercises, report_id;
        при отсутствии дефицитов — message
    """
    db = SessionLocal()
    
    try:
        # Получаем игрока
        player = db.query(Player).filter(Player.player_id == player_id).first()
        if not player:
            return {'success': False, 'error': f'Игрок с ID {player_id} не найден'}
        
        # Получаем роль игрока (берём первую с наибольшей доверенностью)
        cluster_analysis = db.query(ClusterAnalysis).filter(
            ClusterAnalysis.player_id == player_id
        ).order_by(ClusterAnalysis.trust_score.desc()).first()
        
        if not cluster_analysis:
            return {'success': False, 'error': f'Нет кластерного анализа для игрока {player.player_name}'}
        
        role = cluster_analysis.roles
        league_id = player.team.league_id if player.team else None
        
        if not league_id:
            return {'success': False, 'error': f'Лига не определена для игрока {player.player_name}'}
        
        # Собираем дефицитные метрики
        deficit_metrics = []
        
        # Получаем все метрики игрока
        season_metrics = db.query(SeasonMetric).filter(
            SeasonMetric.player_id == player_id
        )
        
        if season_year:
            season_metrics = season_metrics.filter(SeasonMetric.season_start_year == season_year)
        
        season_metrics = season_metrics.all()
        
        for season_metric in season_metrics:
            metric = season_metric.metric
            actual_value = float(season_metric.season_metric_value) if season_metric.season_metric_value else 0
            
            # Получаем бенчмарк для этого метрика, роли и лиги
            benchmark = db.query(Benchmark).filter(
                Benchmark.metric_id == metric.metric_id,
                Benchmark.role_id == role.role_id,
                Benchmark.league_id == league_id
            ).first()
            
            if not benchmark or benchmark.standard_deviation == 0:
                continue
            
            # Рассчитываем Z-score
            z_score = (actual_value - float(benchmark.mean)) / float(benchmark.standard_deviation)
            
            if z_score <= Z_DEFICIT_THRESHOLD:
                deficit_metrics.append({
                    'metric_id': metric.metric_id,
                    'metric_name': metric.metric_name,
                    'actual': actual_value,
                    'mean': float(benchmark.mean),
                    'std': float(benchmark.standard_deviation),
                    'z_score': round(z_score, 2),
                    'severity': (
                        'CRITICAL' if z_score <= Z_SEVERE_THRESHOLD else 'MODERATE'
                    ),
                })
        
        if not deficit_metrics:
            return {
                'success': True,
                'player_name': player.player_name,
                'role': role.role_name,
                'message': 'Нет дефицитов, рекомендации не требуются'
            }
        
        recommended_exercises = []
        max_difficulty = (
            SEVERE_MAX_EXERCISE_DIFFICULTY
            if any(d['z_score'] <= Z_SEVERE_THRESHOLD for d in deficit_metrics)
            else None
        )

        for deficit in deficit_metrics:
            metric_id = deficit['metric_id']

            exercises_for_metric = db.query(ExerciseForMetric).filter(
                ExerciseForMetric.metric_id == metric_id
            ).all()

            for efm in exercises_for_metric:
                exercise = efm.exercise

                if max_difficulty is not None:
                    diff = exercise.difficulty
                    if diff is not None and diff > max_difficulty:
                        continue
                
                # Избегаем дубликатов
                if not any(e['exercise_id'] == exercise.exercise_id for e in recommended_exercises):
                    recommended_exercises.append({
                        'exercise_id': exercise.exercise_id,
                        'exercise_name': exercise.exercise_name,
                        'exercise_description': exercise.exercise_description,
                        'difficulty': exercise.difficulty,
                        'metric_name': deficit['metric_name'],
                        'z_score': deficit['z_score']
                    })
        
        # Создаём запись в таблице Report
        report = Report(
            player_id=player_id,
            user_id=user_id,
            user_login=user_login,
        )
        db.add(report)
        db.flush()  # Чтобы получить report_id
        report_id = report.report_id
        
        # Создаём записи в ExerciseInReport для каждого упражнения
        for exercise_data in recommended_exercises:
            exercise_in_report = ExerciseInReport(
                report_id=report_id,
                exercise_id=exercise_data['exercise_id']
            )
            db.add(exercise_in_report)
        
        db.commit()
        
        return {
            'success': True,
            'player_name': player.player_name,
            'role': role.role_name,
            'deficit_count': len(deficit_metrics),
            'deficits': deficit_metrics,
            'exercises_count': len(recommended_exercises),
            'exercises': recommended_exercises,
            'report_id': report_id
        }
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ОШИБКА при анализе игрока: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
    
    finally:
        db.close()


def print_recommendation_report(recommendation):
    """
    Красиво выводит результаты анализа
    """
    if not recommendation['success']:
        print(f"❌ Ошибка: {recommendation.get('error', 'Неизвестная ошибка')}")
        return
    
    print("\n" + "=" * 80)
    print(f"📋 АНАЛИЗ ИГРОКА: {recommendation['player_name']} ({recommendation['role']})")
    print("=" * 80)
    
    if 'message' in recommendation:
        print(f"✅ {recommendation['message']}")
        return
    
    print(f"\n🔴 НАЙДЕНО ДЕФИЦИТОВ: {recommendation['deficit_count']}\n")
    
    print(">>> Дефицитные метрики:")
    for deficit in recommendation['deficits']:
        severity_icon = "🔴" if deficit['severity'] == 'CRITICAL' else "🟡"
        print(f"  {severity_icon} {deficit['metric_name']:30s} | Z-score: {deficit['z_score']:6.2f} | Actual: {deficit['actual']:8.2f} | Bench: {deficit['mean']:8.2f}")
    
    print(f"\n💪 РЕКОМЕНДУЕМЫЕ УПРАЖНЕНИЯ: {recommendation['exercises_count']}\n")
    
    print(">>> Упражнения по метрикам:")
    for exercise in recommendation['exercises']:
        print(f"  • {exercise['exercise_name']:40s} | Метрик: {exercise['metric_name']:20s} | Сложность: {exercise['difficulty']}")
        print(f"    └─ {exercise['exercise_description']}")
    
    print(f"\n✅ Создан отчёт с ID: {recommendation['report_id']}")
    print("=" * 80)
