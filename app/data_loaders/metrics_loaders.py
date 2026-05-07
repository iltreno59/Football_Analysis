import soccerdata as sd
from app.core.db_conn import SessionLocal
from app import models

def init_metrics_from_fbref():
    db = SessionLocal()
    # Инициализация чтения FBref для одной лиги (для получения структуры колонок)
    fbref = sd.FBref(leagues=['ENG-Premier League'], seasons='2324')
    
    # Список разделов, из которых вытягиваются названия метрик
    stat_types = ['standard', 'shooting', 'playing_time', 'misc', 'keeper']
    
    existing_metrics = {m.metric_name for m in db.query(models.Metric).all()}
    new_metrics_count = 0

    for stype in stat_types:
        try:
            # Получение DataFrame (скрапинг)
            df = fbref.read_player_season_stats(stat_type=stype)
            
            # В FBref колонки — это MultiIndex (например, ('Performance', 'Gls'))
            # Необходимо второе значение (название самой метрики)
            all_cols = df.columns.get_level_values(1).unique()
            
            for col_name in all_cols:
                # Пропуск технических полей и уже существующих
                if not col_name or str(col_name).strip() == "" or col_name in ['squad', 'born', 'pos', 'age'] or col_name in existing_metrics:
                    continue
                
                new_metric = models.Metric(
                    metric_name=col_name,
                    metric_category=stype.capitalize(), # Категория по типу раздела
                    metric_description=f"Automated import from FBref {stype} stats"
                )
                db.add(new_metric)
                existing_metrics.add(col_name)
                new_metrics_count += 1
                
        except Exception as e:
            print(f"Ошибка при обработке раздела {stype}: {e}")

    db.commit()
    print(f"Готово! Добавлено новых метрик: {new_metrics_count}")
    db.close()

if __name__ == "__main__":
    init_metrics_from_fbref()