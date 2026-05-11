from app.core.db_conn import SessionLocal
from app.models import Exercise

def seed_exercises():
    db = SessionLocal()
    
    # Набор из 25 упражнений, охватывающих разные аспекты игры
    exercises_data = [
        # АТАКА (Метрики: Gls, SoT, G/Sh)
        {"name": "1v1 Finishing Drill", "desc": "Выход один на один с вратарем. Развивает реализацию (Gls) и точность ударов (SoT)."},
        {"name": "Cross & Volley", "desc": "Завершение после фланговых навесов. Влияет на количество голов (Gls) и игру в касание."},
        {"name": "Long Range Shooting", "desc": "Отработка ударов из-за штрафной. Прокачивает точность и количество дальних ударов."},
        {"name": "Penalty Shootout", "desc": "Отработка 11-метровых. Прямое влияние на метрику PK."},
        {"name": "Attacking Overload (3v2)", "desc": "Создание численного преимущества. Развивает принятие решений в финальной трети."},

        # ПАС И СОЗИДАНИЕ (Метрики: Ast, KP, PasTotCmp%)
        {"name": "Rondo 4v2", "desc": "Классический «квадрат». Повышает точность передач (PasTotCmp%) и владение под давлением."},
        {"name": "Direct Play Transition", "desc": "Отработка лонгболлов и быстрой смены вектора. Влияет на точность длинных передач (PasLonCmp%)."},
        {"name": "Final Third Pass Flow", "desc": "Комбинации перед штрафной. Влияет на ключевые передачи (KP) и ассисты (Ast)."},
        {"name": "Through Ball Timing", "desc": "Пасы вразрез на ход. Отработка метрик xAG и передач в штрафную."},
        {"name": "Triangle Passing", "desc": "Базовое упражнение на культуру паса и движение после передачи."},

        # ЗАЩИТА (Метрики: TklW, Int, Clr, Blk)
        {"name": "1v1 Defensive Stance", "desc": "Отработка отбора мяча в дуэли. Прямое влияние на выигранные единоборства (TklW)."},
        {"name": "Zonal Positioning", "desc": "Тактическая тренировка расположения в защите. Повышает количество перехватов (Int)."},
        {"name": "Header Clearance", "desc": "Отработка выносов мяча головой. Влияет на метрику Clr (Clearances)."},
        {"name": "Shot Blocking Drill", "desc": "Тренировка блокировки ударов защитниками (Blk)."},
        {"name": "High Pressing Triggers", "desc": "Отработка прессинга при потере. Повышает количество отборов в атакующей трети."},

        # ВРАТАРИ (Метрики: Save%, CS, PSxG)
        {"name": "Reaction Saves", "desc": "Отработка ударов с близкой дистанции. Повышает процент сейвов (Save%)."},
        {"name": "Cross Claiming", "desc": "Игра на выходе при навесах. Снижает количество допущенных моментов у ворот."},
        {"name": "GK Distribution", "desc": "Ввод мяча рукой и ногой. Влияет на начало атак и точность передач вратаря."},
        {"name": "One-on-One Smothering", "desc": "Сокращение дистанции при выходе форварда. Влияет на PSxG +/-."},

        # ФИЗИКА И ОБЩЕЕ (Метрики: Touches, Rec%)
        {"name": "Shuttle Runs (Beep Test)", "desc": "Челночный бег для повышения выносливости и объема работы на 90 минут."},
        {"name": "Agility Ladder Drills", "desc": "Работа на координацию и скорость работы ног."},
        {"name": "First Touch Control", "desc": "Прием тяжелых мячей. Повышает процент успешных приемов (Rec%)."},
        {"name": "Interval Sprints", "desc": "Спринты высокой интенсивности для фланговых игроков (Wingers/Full Backs)."},
        {"name": "Recovery Possession", "desc": "Удержание мяча после отбора. Повышает контроль игры (PPM)."},
        {"name": "Set Piece Defense", "desc": "Отработка стандартов у своих ворот. Снижает количество пропущенных голов (GA)."}
    ]

    print(">>> Seeding exercises...")
    for ex in exercises_data:
        exists = db.query(Exercise).filter(Exercise.exercise_name == ex["name"]).first()
        if not exists:
            db.add(Exercise(
                exercise_name=ex["name"],
                exercise_description=ex["desc"]
            ))
    
    try:
        db.commit()
        print(f"Successfully seeded {len(exercises_data)} football exercises.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_exercises()