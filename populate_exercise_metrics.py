"""
Заполнение таблицы ExerciseForMetric связями между упражнениями и метриками
"""
from app.core.db_conn import SessionLocal
from app.models import Exercise, Metric, ExerciseForMetric


def populate_exercise_metrics():
    """
    Заполняет таблицу ExerciseForMetric на основе описаний упражнений
    """
    db = SessionLocal()
    
    # Маппинг: exercise_id -> [(metric_name, weight), ...]
    exercise_metric_mapping = {
        26: [('Goals', 0.8), ('Shots on target', 0.7)],  # 1v1 Finishing
        27: [('Goals', 0.9), ('Shots on target', 0.8)],  # Cross & Volley
        28: [('Shots', 0.8), ('Shots on target', 0.7)],  # Long Range Shooting
        29: [('Penalties scored', 0.9)],  # Penalty Shootout
        30: [('Big chances created', 0.8), ('Assists', 0.7)],  # Attacking Overload
        31: [('Passes', 0.7), ('Passes per match', 0.8)],  # Rondo 4v2
        32: [('Accurate long balls', 0.9)],  # Direct Play Transition
        33: [('Big chances created', 0.8), ('Assists', 0.8)],  # Final Third Pass Flow
        34: [('Through balls', 0.9), ('Big chances created', 0.7)],  # Through Ball Timing
        35: [('Passes', 0.8), ('Passes per match', 0.7)],  # Triangle Passing
        36: [('Tackles', 0.9)],  # 1v1 Defensive Stance
        37: [('Interceptions', 0.8), ('Recoveries', 0.7)],  # Zonal Positioning
        38: [('Clearances', 0.9), ('Headed Clearance', 0.8)],  # Header Clearance
        39: [('Blocked shots', 0.8)],  # Shot Blocking Drill
        40: [('Tackles', 0.7), ('Interceptions', 0.7)],  # High Pressing Triggers
        41: [('Saves', 0.9)],  # Reaction Saves
        42: [('Catches', 0.8), ('High Claims', 0.7)],  # Cross Claiming
        43: [('Passes', 0.8), ('Accurate long balls', 0.7)],  # GK Distribution
        44: [('Saves', 0.8)],  # One-on-One Smothering
        # 45 и 46 - физические упражнения, не влияют на конкретные метрики
        47: [('Recoveries', 0.8)],  # First Touch Control
        48: [('Dribbles', 0.7)],  # Interval Sprints (для фланговых)
        49: [('Passes', 0.7), ('Passes per match', 0.7)],  # Recovery Possession
        50: [('Interceptions', 0.8), ('Clearances', 0.7)],  # Set Piece Defense
    }
    
    added_count = 0
    skipped_count = 0
    
    try:
        for exercise_id, metrics_list in exercise_metric_mapping.items():
            # Получаем упражнение
            exercise = db.query(Exercise).filter(Exercise.exercise_id == exercise_id).first()
            if not exercise:
                print(f"  ⚠ Упражнение с ID {exercise_id} не найдено")
                skipped_count += 1
                continue
            
            for metric_name, weight in metrics_list:
                # Получаем метрик
                metric = db.query(Metric).filter(Metric.metric_name == metric_name).first()
                if not metric:
                    print(f"  ⚠ Метрик '{metric_name}' не найден")
                    continue
                
                # Проверяем, не существует ли уже связь
                existing = db.query(ExerciseForMetric).filter(
                    ExerciseForMetric.exercise_id == exercise_id,
                    ExerciseForMetric.metric_id == metric.metric_id
                ).first()
                
                if not existing:
                    efm = ExerciseForMetric(
                        exercise_id=exercise_id,
                        metric_id=metric.metric_id,
                        weight=weight
                    )
                    db.add(efm)
                    added_count += 1
        
        db.commit()
        print(f"\n✅ ЗАПОЛНЕНА ТАБЛИЦА ExerciseForMetric:")
        print(f"   Добавлено связей: {added_count}")
        print(f"   Пропущено: {skipped_count}")
        
        return added_count
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ОШИБКА при заполнении ExerciseForMetric: {e}")
        import traceback
        traceback.print_exc()
        return 0
    
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(">>> Заполнение связей упражнений и метрик...")
    print("=" * 80)
    populate_exercise_metrics()
