import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from .data_preparator import get_prepared_data

def compute_clusters():
    df_scaled = get_prepared_data()
    if df_scaled is None: return None

    zones_config = {
        'GK': {'n': 2, 'prefix': 'GK_'},
        'CB': {'n': 2, 'prefix': 'CB_'},
        'FB': {'n': 2, 'prefix': 'FB_'},
        'CM': {'n': 2, 'prefix': 'CM_'}, # Уменьшил до 2 для надежности
        'WG': {'n': 2, 'prefix': 'WG_'},
        'ST': {'n': 2, 'prefix': 'ST_'}
    }

    # 1. Распределяем по виртуальным зонам
    player_zones = {}
    for name, row in df_scaled.iterrows():
        pos = row['position']
        target = pos
        if pos == 'DF':
            target = 'FB' if row.get('Crosses', 0) > 0 else 'CB'
        elif pos == 'MF':
            target = 'WG' if row.get('Shots', 0) > 0.5 or row.get('Dribbles', 0) > 0.5 else 'CM'
        elif pos == 'FW':
            target = 'ST'
        player_zones[name] = target

    # 2. Кластеризуем
    final_results = {}
    for zone, config in zones_config.items():
        names = [n for n, z in player_zones.items() if z == zone]
        
        # Только числовые данные для KMeans
        data = df_scaled.loc[names].select_dtypes(include=[np.number])
        
        # ГЛАВНАЯ ПРОВЕРКА: Если данных нет или игроков меньше, чем кластеров
        if data.empty or len(data) < config['n']:
            print(f"!!! Пропуск зоны {zone}: недостаточно данных ({len(data)} игроков)")
            continue

        try:
            kmeans = KMeans(n_clusters=config['n'], random_state=42, n_init=10)
            labels = kmeans.fit_predict(data)
            
            dist = kmeans.transform(data).min(axis=1)
            conf = 1 / (1 + dist)

            for i, name in enumerate(names):
                final_results[name] = {
                    'role': f"{config['prefix']}{labels[i] + 1}",
                    'confidence': round(float(conf[i]), 4)
                }
        except Exception as e:
            print(f"Ошибка в зоне {zone}: {e}")

    return final_results