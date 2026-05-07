import soccerdata as sd
import pandas as pd
from app.core.db_conn import SessionLocal
from app.models import Player, Metric, SeasonMetric

def load_metrics_values():
    db = SessionLocal()
    start_year = 2023
    
    players_map = {str(p.player_name).strip(): p.player_id for p in db.query(Player).all()}
    metrics_map = {str(m.metric_name).strip(): m.metric_id for m in db.query(Metric).all()}
    
    # Кэширование уже существующих в базе записей, чтобы не добавлять их снова
    # Хранение кортежа (player_id, metric_id, year)
    existing_records = set(
        db.query(SeasonMetric.player_id, SeasonMetric.metric_id, SeasonMetric.season_start_year).all()
    )

    fbref = sd.FBref(leagues=['ENG-Premier League'], seasons='2324')
    stat_types = ['standard', 'shooting', 'playing_time', 'misc', 'keeper']

    for stype in stat_types:
        print(f"\n>>> ОБРАБОТКА РАЗДЕЛА: {stype}")
        try:
            df = fbref.read_player_season_stats(stat_type=stype)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[-1] if isinstance(c, tuple) and not str(c[-1]).startswith('Unnamed') else str(c) for c in df.columns]
            
            df = df.reset_index()
            p_col = next((c for c in ['player', 'Player'] if c in df.columns), 'player')
            
            added = 0
            skipped = 0

            for _, row in df.iterrows():
                p_name = str(row[p_col]).strip()
                p_id = players_map.get(p_name)
                if not p_id: continue

                for col_name, value in row.items():
                    m_name = str(col_name).strip()
                    m_id = metrics_map.get(m_name)
                    
                    if m_id and pd.notna(value):
                        # Проверяем на дубликат через кэш
                        record_key = (p_id, m_id, start_year)
                        if record_key in existing_records:
                            skipped += 1
                            continue

                        try:
                            val_raw = str(value).replace('%', '').replace(',', '').split()[0]
                            new_record = SeasonMetric(
                                player_id=p_id,
                                metric_id=m_id,
                                season_start_year=start_year,
                                season_metric_value=float(val_raw)
                            )
                            db.add(new_record)
                            existing_records.add(record_key) # Обновляем кэш в памяти
                            added += 1
                        except: continue

                # Коммит по игрокам
                db.commit()

            print(f"ИТОГ {stype}: Добавлено {added}, Пропущено дублей {skipped}")

        except Exception as e:
            print(f"Ошибка в {stype}: {e}")
            db.rollback()

    db.close()

if __name__ == "__main__":
    load_metrics_values()