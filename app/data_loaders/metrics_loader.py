import pandas as pd
from app.core.db_conn import SessionLocal
from app.models import Metric, Player, Team, SeasonMetric

def load_metrics_from_kaggle(csv_path=r"D:\\Football_Analysis\\app\\data_loaders\\dataset.csv"):
    db = SessionLocal()
    df = pd.read_csv(csv_path)

    # Список колонок, которые НЕ являются метриками (текстовые данные)
    tech_cols = ['Name', 'Club', 'Position', 'Nationality', 'Jersey Number']
    
    # Все остальные колонки — это наши метрики
    metric_cols = [c for c in df.columns if c not in tech_cols]

    print(f">>> Найдено {len(metric_cols)} метрик. Регистрация...")
    
    # 1. РЕГИСТРАЦИЯ МЕТРИК
    for m_name in metric_cols:
        if not db.query(Metric).filter_by(metric_name=m_name).first():
            db.add(Metric(metric_name=m_name))
    db.commit()

    metrics_map = {m.metric_name: m.metric_id for m in db.query(Metric).all()}

    # 2. ЗАГРУЗКА ЗНАЧЕНИЙ
    print(">>> Заполнение статистики игроков...")
    added_stats = 0
    
    for _, row in df.iterrows():
        # Ищем игрока по имени и клубу
        player = db.query(Player).join(Team).filter(
            Player.player_name == row['Name'],
            Team.team_name == row['Club']
        ).first()

        if player:
            for m_name in metric_cols:
                val = row[m_name]
                if pd.isna(val): continue
                
                # Обработка процентов (например "23%") и числовых строк
                try:
                    if isinstance(val, str) and '%' in val:
                        clean_val = float(val.replace('%', ''))
                    else:
                        clean_val = float(val)
                        
                    m_id = metrics_map.get(m_name)
                    # Создаем запись в season_metric
                    db.add(SeasonMetric(
                        player_id=player.player_id,
                        metric_id=m_id,
                        season_metric_value=clean_val
                    ))
                    added_stats += 1
                except: continue
        
        # Коммитим после каждого игрока (или пачкой)
        db.commit()

    db.close()
    print(f">>> Готово! Загружено значений: {added_stats}")

if __name__ == "__main__":
    load_metrics_from_kaggle()