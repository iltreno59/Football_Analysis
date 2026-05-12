import pandas as pd
import numpy as np
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler
from app.core.db_conn import SessionLocal

def get_prepared_data():
    db = SessionLocal()
    query = text("""
        SELECT 
            p.player_name,
            m.metric_name,
            sm.season_metric_value
        FROM season_metric sm
        JOIN player p ON sm.player_id = p.player_id
        JOIN metric m ON sm.metric_id = m.metric_id
        WHERE sm.season_start_year = '2023'
    """)
    
    print(">>> Извлечение данных из БД...")
    result = db.execute(query)
    df_raw = pd.DataFrame(result.fetchall(), columns=['player_name', 'metric_name', 'value'])
    db.close()

    if df_raw.empty:
        print("Данные не найдены. Проверь наличие записей в season_metric.")
        return None

    # 1. Матрица "Игрок x Метрики"
    df_pivot = df_raw.pivot_table(
        index='player_name', 
        columns='metric_name', 
        values='value', 
        aggfunc='mean'
    )
    
    # Заполнение пропусков нулями
    df_pivot = df_pivot.fillna(0)

    # 2. Фильтрация "шума"
    if 'Min' in df_pivot.columns:
        df_pivot = df_pivot[df_pivot['Min'] >= 450]

    # 3. Z-масштабирование (Standardization)
    scaler = StandardScaler()
    
    # Обучение скейлера и трансформирмация данных
    data_scaled = scaler.fit_transform(df_pivot)
    
    # DataFrame с масштабированными данными для удобства
    df_scaled = pd.DataFrame(data_scaled, index=df_pivot.index, columns=df_pivot.columns)

    print(f">>> Z-масштабирование завершено.")
    print(f">>> Итоговая матрица: {df_scaled.shape[0]} игроков на {df_scaled.shape[1]} метрик.")
    
    return df_scaled

if __name__ == "__main__":
    df_final = get_prepared_data()
    if df_final is not None:
        print("\nФрагмент подготовленных данных (первые 5 строк и 5 метрик):")
        print(df_final.iloc[:5, :5])