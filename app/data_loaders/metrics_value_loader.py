import soccerdata as sd
import pandas as pd
from app.core.db_conn import SessionLocal
from app.models import Player, Metric, SeasonMetric

def load_metrics_values():
    db = SessionLocal()
    start_year = 2023
    
    # Загружаем карты и СРАЗУ выводим их размер
    players_map = {str(p.player_name).strip(): p.player_id for p in db.query(Player).all()}
    metrics_map = {str(m.metric_name).strip(): m.metric_id for m in db.query(Metric).all()}
    
    print(f"DEBUG: Игроков в кэше: {len(players_map)}")
    print(f"DEBUG: Метрик в кэше: {len(metrics_map)}")

    fbref = sd.FBref(leagues=['ENG-Premier League'], seasons='2324')
    # Используем только те разделы, которые точно работают
    stat_types = ['standard', 'shooting', 'playing_time', 'misc', 'keeper']

    for stype in stat_types:
        print(f"\n>>> РАЗДЕЛ: {stype}")
        df = fbref.read_player_season_stats(stat_type=stype)
        
        # Сплющивание колонок
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[-1] if isinstance(c, tuple) and not str(c[-1]).startswith('Unnamed') else str(c) for c in df.columns]
        
        df = df.reset_index()
        p_col = next((c for c in ['player', 'Player'] if c in df.columns), 'player')
        
        added = 0
        errors = 0

        for _, row in df.iterrows():
            p_name = str(row[p_col]).strip()
            p_id = players_map.get(p_name)
            
            if not p_id:
                continue

            for col_name, value in row.items():
                m_name = str(col_name).strip()
                m_id = metrics_map.get(m_name)
                
                # Если метрика найдена в базе и значение не пустое
                if m_id and pd.notna(value):
                    try:
                        # Чистим строку от процентов и скобок
                        clean_val = str(value).replace('%', '').replace(',', '').split()[0]
                        
                        new_record = SeasonMetric(
                            player_id=p_id,
                            metric_id=m_id,
                            season_start_year=start_year,
                            season_metric_value=float(clean_val)
                        )
                        db.add(new_record)
                        added += 1
                    except Exception as e:
                        # Если упало на конкретном значении — выводим почему
                        if errors < 3:
                            print(f"Ошибка значения ({m_name}): {e}")
                        errors += 1

            # Коммит после каждого игрока (медленно, но надежно для отладки)
            try:
                db.commit()
            except Exception as e:
                print(f"Ошибка коммита игрока {p_name}: {e}")
                db.rollback()

        print(f"ИТОГ ПО {stype}: Добавлено {added}, Ошибок {errors}")

    db.close()

if __name__ == "__main__":
    load_metrics_values()