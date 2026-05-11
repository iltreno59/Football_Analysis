from app.core.db_conn import SessionLocal
import app.models as models

def seed_exercise_metric_links():
    db = SessionLocal()

    mapping = {
        # --- АТАКА ---
        "1v1 Finishing Drill": ["Gls", "SoT", "G/Sh"],
        "Cross & Volley": ["Gls", "SoT"],
        "Long Range Shooting": ["Gls", "SoT", "G/Sh"],
        "Penalty Shootout": ["PK", "Gls"],
        "Attacking Overload (3v2)": ["Gls", "Ast", "KP", "xAG"],

        # --- ПАС И СОЗИДАНИЕ ---
        "Rondo 4v2": ["PasTotCmp%", "Touches", "Rec%"],
        "Direct Play Transition": ["PasLonCmp%", "PasMedCmp%"],
        "Final Third Pass Flow": ["KP", "Ast", "PPA"],
        "Through Ball Timing": ["TB", "xAG", "KP"],
        "Triangle Passing": ["PasTotCmp%", "PasShoCmp%"],

        # --- ЗАЩИТА ---
        "1v1 Defensive Stance": ["TklW", "Tkl%", "Blocks"],
        "Zonal Positioning": ["Int", "Blocks", "Err"],
        "Header Clearance": ["Clr"],
        "Shot Blocking Drill": ["Blocks", "Blk"],
        "High Pressing Triggers": ["Tkl", "Recov"],

        # --- ВРАТАРИ ---
        "Reaction Saves": ["Save%", "PSxG", "SoTA"],
        "Cross Claiming": ["CS%", "GA"],
        "GK Distribution": ["PasTotCmp%"],
        "One-on-One Smothering": ["Save%", "PSxG"],

        # --- ФИЗИКА И КОНТРОЛЬ ---
        "Shuttle Runs (Beep Test)": ["Min", "90s"],
        "First Touch Control": ["Mis", "Dis", "Rec%"],
        "Recovery Possession": ["PPM", "Recov"],
        "Set Piece Defense": ["GA", "Clr", "Blocks"]
    }

    print(">>> Creating Exercise-Metric associations...")

    added_count = 0
    for ex_name, metric_names in mapping.items():
        # 1. Поиск упражнения в базе
        exercise = db.query(models.Exercise).filter(models.Exercise.exercise_name == ex_name).first()
        if not exercise:
            continue

        for m_name in metric_names:
            # 2. Поиск метрики в базе по названию
            metric = db.query(models.Metric).filter(models.Metric.metric_name == m_name).first()
            if not metric:
                print(f"Warning: Metric '{m_name}' not found in DB.")
                continue

            # 3. Создание связи
            exists = db.query(models.ExerciseForMetric).filter(
                models.ExerciseForMetric.exercise_id == exercise.exercise_id,
                models.ExerciseForMetric.metric_id == metric.metric_id
            ).first()

            if not exists:
                new_link = models.ExerciseForMetric(
                    exercise_id=exercise.exercise_id,
                    metric_id=metric.metric_id,
                    weight=1.0  # Коэффициент влияния (для MVP 1.0)
                )
                db.add(new_link)
                added_count += 1

    try:
        db.commit()
        print(f"DONE: Created {added_count} Exercise-Metric links.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_exercise_metric_links()