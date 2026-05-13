import pandas as pd
import numpy as np
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler
from app.core.db_conn import SessionLocal

def get_prepared_data():
    db = SessionLocal()
    query = text("""
        SELECT p.player_name, p.position, m.metric_name, sm.season_metric_value
        FROM season_metric sm
        JOIN player p ON sm.player_id = p.player_id
        JOIN metric m ON sm.metric_id = m.metric_id
    """)
    
    result = db.execute(query)
    df_raw = pd.DataFrame(result.fetchall(), columns=['player_name', 'position', 'metric_name', 'value'])
    db.close()

    if df_raw.empty: return None

    # Создаем сводную таблицу (индекс — имя и позиция)
    df_pivot = df_raw.pivot_table(index=['player_name', 'position'], columns='metric_name', values='value').fillna(0)

    def scale_group(group):
        # Выбираем только числовые столбцы для масштабирования
        numeric_cols = group.select_dtypes(include=[np.number]).columns.tolist()
        cols_to_scale = [c for c in numeric_cols if c not in ['Age', 'Appearances', 'Wins', 'Losses']]
        
        if not cols_to_scale or len(group) < 2:
            return group
            
        scaler = StandardScaler()
        group[cols_to_scale] = scaler.fit_transform(group[cols_to_scale].astype(np.float32))
        return group

    # Масштабируем внутри каждой базовой позиции
    df_scaled = df_pivot.groupby(level='position', group_keys=False).apply(scale_group)
    
    # ПРЕВРАЩАЕМ В ПЛОСКИЙ ВИД: player_name и position становятся обычными колонками
    df_final = df_scaled.reset_index()
    df_final = df_final.set_index('player_name')
    
    return df_final