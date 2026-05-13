import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from .data_preparator import get_prepared_data

def compute_clusters():
    df_scaled = get_prepared_data()
    if df_scaled is None: return None

    MIN_PLAYERS_PER_ZONE = 5 
    if df_scaled.index.name == 'player_name':
        df_scaled = df_scaled.reset_index()

    df_numeric_check = df_scaled.apply(pd.to_numeric, errors='coerce')

    zones_config = {
        'GK': {'n': 2, 'prefix': 'GK_'},
        'CB': {'n': 2, 'prefix': 'CB_'}, 
        'FB': {'n': 2, 'prefix': 'FB_'},
        'CM': {'n': 2, 'prefix': 'CM_'},
        'WG': {'n': 2, 'prefix': 'WG_'},
        'ST': {'n': 2, 'prefix': 'ST_'}
    }

    player_zones = {}
    for i, row in df_scaled.iterrows():
        name = row['player_name']
        # Очистка названия позиции от пробелов и регистра
        pos = str(row['position']).strip().upper()
        num_row = df_numeric_check.iloc[i]
        
        target = pos
        if pos == 'DF':
            # Ищем Crosses без учета регистра для надежности
            crosses = num_row.get('Crosses', 0) or num_row.get('crosses', 0)
            target = 'FB' if crosses > 0 else 'CB'
        elif pos == 'MF':
            shots = num_row.get('Shots', 0) or num_row.get('shots', 0)
            target = 'WG' if shots > 0.5 else 'CM'
        elif pos == 'FW':
            target = 'ST'
        
        player_zones[name] = target

    final_results = {}
    for zone, config in zones_config.items():
        names_in_zone = [n for n, z in player_zones.items() if z == zone]
        zone_data = df_numeric_check[df_scaled['player_name'].isin(names_in_zone)]
        numeric_data = zone_data.dropna(axis=1, how='all').astype(np.float32)

        # Убираем только те колонки, которые точно технические
        cols_to_drop = ['Age', 'Appearances', 'Wins', 'Losses', 'Min', 'player_id']
        numeric_data = numeric_data.drop(columns=[c for c in cols_to_drop if c in numeric_data.columns])

        if numeric_data.shape[1] == 0:
            continue # Пропускаем молча, если нет чисел

        if len(numeric_data) < MIN_PLAYERS_PER_ZONE:
            continue

        kmeans = KMeans(n_clusters=config['n'], random_state=42, n_init=10)
        labels = kmeans.fit_predict(numeric_data)
        
        dist = kmeans.transform(numeric_data).min(axis=1)
        conf = 1 / (1 + dist)

        for i, idx in enumerate(zone_data.index):
            player_name = df_scaled.loc[idx, 'player_name']
            # Возвращаем только роль
            final_results[player_name] = {
                'role': f"{config['prefix']}{labels[i] + 1}"
            }

    return final_results