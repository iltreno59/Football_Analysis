import soccerdata as sd
from app.core.db_conn import SessionLocal
from app.models import Metric
import pandas as pd

def rebuild_metrics():
    db = SessionLocal()
    # Только те разделы, которые разрешила библиотека в твоем логе
    stat_types = ['standard', 'keeper', 'shooting', 'playing_time', 'misc']
    
    fbref = sd.FBref(leagues=['ENG-Premier League'], seasons='2324')
    unique_names = set()

    try:
        for stype in stat_types:
            print(f"Извлечение из: {stype}...")
            df = fbref.read_player_season_stats(stat_type=stype)
            
            if isinstance(df.columns, pd.MultiIndex):
                cols = [c[-1] if isinstance(c, tuple) and not str(c[-1]).startswith('Unnamed') else c for c in df.columns]
            else:
                cols = df.columns.tolist()

            for col in cols:
                name = str(col).strip()
                if name and name.lower() not in ['player', 'squad', 'team', 'season', 'league', 'nation', 'pos', 'age', 'born']:
                    unique_names.add(name)
        
        for m_name in unique_names:
            if not db.query(Metric).filter(Metric.metric_name == m_name).first():
                db.add(Metric(metric_name=m_name))
        
        db.commit()
        print(f"\nГотово! Справочник Metric теперь содержит {len(unique_names)} уникальных имен.")
    finally:
        db.close()

if __name__ == "__main__":
    rebuild_metrics()