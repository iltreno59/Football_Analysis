import soccerdata as sd
import pandas as pd
from app.core.db_conn import SessionLocal
from app.models import Metric

def rebuild_metrics():
    db = SessionLocal()
    fbref = sd.FBref(leagues=['ENG-Premier League'], seasons='2324')
    stat_types = ['standard', 'shooting', 'playing_time', 'misc', 'keeper']
    
    unique_metrics = set()
    
    try:
        for stype in stat_types:
            print(f"Извлечение имен из раздела: {stype}")
            df = fbref.read_player_season_stats(stat_type=stype)
            
            # Схлопывание MultiIndex до последнего уровня
            if isinstance(df.columns, pd.MultiIndex):
                cols = [c[-1] if isinstance(c, tuple) and not str(c[-1]).startswith('Unnamed') else c for c in df.columns]
            else:
                cols = df.columns.tolist()
            
            # Фильтрация технических колонок
            for col in cols:
                clean_name = str(col).strip()
                if clean_name and clean_name not in ['player', 'squad', 'team', 'season', 'league', 'nation', 'pos', 'age', 'born']:
                    unique_metrics.add(clean_name)
        
        # Запись в БД
        for m_name in unique_metrics:
            if not db.query(Metric).filter(Metric.metric_name == m_name).first():
                db.add(Metric(metric_name=m_name))
        
        db.commit()
        print(f"[УСПЕХ] Справочник пересобран. Всего метрик: {len(unique_metrics)}")
        
    except Exception as e:
        db.rollback()
        print(f"[ОШИБКА] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    rebuild_metrics()