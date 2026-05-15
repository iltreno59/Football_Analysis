import pandas as pd
import numpy as np
from sqlalchemy import text
from sklearn.preprocessing import MinMaxScaler
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

    if df_raw.empty:
        return None

    # Создание сводной таблцицы
    df_pivot = df_raw.pivot_table(index=['player_name', 'position'], columns='metric_name', values='value').fillna(0)

    # Базовая фильтрация по объему данных (минимум 10 матчей)
    if 'Appearances' in df_pivot.columns:
        df_pivot = df_pivot[df_pivot['Appearances'] >= 10]
        
        # Переводим абсолютные метрики в "за 90 минут" (усреднение по играм)
        exclude_cols = ['Age', 'Appearances', 'Wins', 'Losses', 'player_id']
        cols_to_avg = [c for c in df_pivot.columns if c not in exclude_cols and '%' not in c]
        
        for col in cols_to_avg:
            df_pivot[col] = df_pivot[col] / df_pivot['Appearances']

    def scale_group(group):
        """
        Масштабируем данные внутри каждой позиции отдельно.
        Используем MinMaxScaler (0-1), чтобы подготовить базу под L1-нормализацию в кластере.
        """
        numeric_cols = group.select_dtypes(include=[np.number]).columns.tolist()
        cols_to_scale = [c for c in numeric_cols if c not in ['Age', 'Appearances', 'Wins', 'Losses']]
        
        if not cols_to_scale or len(group) < 2:
            return group
            
        scaler = MinMaxScaler()
        group[cols_to_scale] = scaler.fit_transform(group[cols_to_scale].astype(np.float32))
        return group

    # Группировка по позициям и масштабирование
    df_scaled = df_pivot.groupby('position', group_keys=False).apply(scale_group)
    
    return df_scaled.reset_index()