from app.core.db_conn import SessionLocal
import app.models as models

def seed_exercises():
    db = SessionLocal()
    
    # 25 упражнений, разделенных по зонам влияния
    exercises_data = [
        # --- АТАКА (Метрики: Gls, SoT, G/Sh) ---
        {"name": "1v1 Finishing Drill", "diff": 8, "desc": "Выход 1 на 1. Реализация (Gls) и точность (SoT)."},
        {"name": "Cross & Volley", "diff": 7, "desc": "Завершение после фланговых навесов. Влияет на Gls."},
        {"name": "Long Range Shooting", "diff": 6, "desc": "Удары из-за штрафной. Точность дальних ударов."},
        {"name": "Penalty Shootout", "diff": 3, "desc": "Отработка 11-метровых (PK)."},
        {"name": "Attacking Overload (3v2)", "diff": 9, "desc": "Численное преимущество. Принятие решений в финальной трети."},

        # --- ПАС И СОЗИДАНИЕ (Метрики: Ast, KP, PasTotCmp%) ---
        {"name": "Rondo 4v2", "diff": 5, "desc": "Квадрат. Точность передач (PasTotCmp%) под давлением."},
        {"name": "Direct Play Transition", "diff": 8, "desc": "Быстрая смена вектора. Точность длинных передач (PasLonCmp%)."},
        {"name": "Final Third Pass Flow", "diff": 6, "desc": "Комбинации перед штрафной. Влияет на KP и Ast."},
        {"name": "Through Ball Timing", "diff": 7, "desc": "Пасы вразрез. Отработка xAG и передач в штрафную."},
        {"name": "Triangle Passing", "diff": 4, "desc": "Культура паса и движение после передачи."},

        # --- ЗАЩИТА (Метрики: TklW, Int, Clr, Blk) ---
        {"name": "1v1 Defensive Stance", "diff": 9, "desc": "Отбор мяча в дуэли. Влияет на TklW."},
        {"name": "Zonal Positioning", "diff": 7, "desc": "Расположение в защите. Повышает перехваты (Int)."},
        {"name": "Header Clearance", "diff": 6, "desc": "Выносы мяча головой. Влияет на Clr."},
        {"name": "Shot Blocking Drill", "diff": 8, "desc": "Тренировка блокировки ударов (Blk)."},
        {"name": "High Pressing Triggers", "diff": 9, "desc": "Прессинг при потере. Отборы в атакующей трети."},

        # --- ВРАТАРИ (Метрики: Save%, CS, PSxG) ---
        {"name": "Reaction Saves", "diff": 9, "desc": "Удары с близкой дистанции. Процент сейвов (Save%)."},
        {"name": "Cross Claiming", "diff": 7, "desc": "Игра на выходе при навесах."},
        {"name": "GK Distribution", "diff": 4, "desc": "Ввод мяча. Точность передач вратаря."},
        {"name": "One-on-One Smothering", "diff": 10, "desc": "Сокращение дистанции. Влияет на PSxG +/-."},

        # --- ФИЗИКА И КОНТРОЛЬ (Метрики: Touches, Rec%, PPM) ---
        {"name": "Shuttle Runs (Beep Test)", "diff": 10, "desc": "Челночный бег. Выносливость на 90 минут."},
        {"name": "Agility Ladder Drills", "diff": 5, "desc": "Координация и скорость ног."},
        {"name": "First Touch Control", "diff": 6, "desc": "Прием тяжелых мячей. Процент успешных приемов (Rec%)."},
        {"name": "Interval Sprints", "diff": 9, "desc": "Спринты для фланговых игроков."},
        {"name": "Recovery Possession", "diff": 7, "desc": "Удержание мяча после отбора. Повышает PPM."},
        {"name": "Set Piece Defense", "diff": 6, "desc": "Стандарты у своих ворот. Снижает GA."}
    ]

    print(">>> Seeding exercises (Lean MVP Version with Sections)...")
    for ex in exercises_data:
        existing = db.query(models.Exercise).filter(models.Exercise.exercise_name == ex["name"]).first()
        
        if existing:
            existing.exercise_description = ex["desc"]
            existing.difficulty = ex["diff"]
        else:
            db.add(models.Exercise(
                exercise_name=ex["name"],
                exercise_description=ex["desc"],
                difficulty=ex["diff"]
            ))
    
    try:
        db.commit()
        print("Success: Exercises seeded and grouped by zones.")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_exercises()