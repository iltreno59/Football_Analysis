import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from .data_preparator import get_prepared_data

def create_style_ratios(numeric_data, zone):
    ratios = pd.DataFrame(index=numeric_data.index)
    
    # Функция для безопасного извлечения данных
    def g(name):
        # В numeric_data колонки УЖЕ в нижнем регистре (мы сделали это в compute_clusters)
        if name in numeric_data.columns:
            return numeric_data[name]
        return pd.Series(0.0, index=numeric_data.index)

    # Используем названия метрик в нижнем регистре, как они приходят из БД
    if zone == 'CM':
        ratios['def'] = (g('tackles') + g('interceptions')) / (g('passes') + 1)
        ratios['atk'] = g('shots') / (g('passes') + 1)
        ratios['cre'] = (g('through balls') + g('big chances created')) / (g('passes') + 1)
    elif zone == 'FB':
        ratios['wing'] = (g('crosses') + g('dribbles')) / (g('passes') + 1)
        ratios['def'] = g('tackles') / (g('passes') + 1)
    elif zone == 'CB':
        ratios['air'] = g('aerial battles won') / (g('tackles') + g('clearances') + 1)
        ratios['prog'] = g('accurate long balls') / (g('passes') + 1)
    elif zone == 'WG':
        ratios['drb'] = g('dribbles') / (g('crosses') + 1)
        ratios['shot'] = g('shots') / (g('passes') + 1)
    elif zone == 'ST':
        ratios['fin'] = g('shots on target') / (g('shots') + 1)
        ratios['vol'] = g('shots') / (g('appearances') + 1)
    
    # Если все ratios оказались нулевыми, добавим базовые метрики, чтобы K-Means было за что зацепиться
    if ratios.sum().sum() == 0:
        return numeric_data[['passes', 'tackles', 'shots']].copy() if 'passes' in numeric_data.columns else numeric_data
        
    return ratios

def compute_clusters():
    raw_df = get_prepared_data()
    if raw_df is None: return {}

    df_working = raw_df.reset_index()
    # Приводим к нижнему регистру названия колонок
    df_working.columns = [c.lower() for c in df_working.columns]
    
    if 'position' in df_working.columns:
        df_working['position'] = df_working['position'].astype(str).str.strip().str.upper()
    
    if 'name' in df_working.columns and 'player_name' not in df_working.columns:
        df_working = df_working.rename(columns={'name': 'player_name'})

    # Распределение 4 -> 6 зон
    MAP = {'GK': 'GK', 'CB': 'DF', 'FB': 'DF', 'CM': 'MF', 'WG': 'FW', 'ST': 'FW'}
    zones_config = {
        'GK': {'n': 2, 'prefix': 'GK_'}, 'CB': {'n': 3, 'prefix': 'CB_'}, 
        'FB': {'n': 3, 'prefix': 'FB_'}, 'CM': {'n': 4, 'prefix': 'CM_'},
        'WG': {'n': 3, 'prefix': 'WG_'}, 'ST': {'n': 3, 'prefix': 'ST_'}
    }

    player_zones = {}
    for i, row in df_working.iterrows():
        pos = str(row['position']).upper()
        if pos == 'DF':
            target = 'FB' if (row.get('crosses', 0) > 0.5 or row.get('dribbles', 0) > 0.4) else 'CB'
        elif pos == 'MF':
            target = 'WG' if (row.get('dribbles', 0) > 0.8 or row.get('crosses', 0) > 1.2) else 'CM'
        else:
            target = 'ST' if pos == 'FW' else pos
        player_zones[row['player_name']] = target

    final_results = {}

    for zone, config in zones_config.items():
        names = [n for n, z in player_zones.items() if z == zone]
        zone_df = df_working[df_working['player_name'].isin(names)]
        
        if len(zone_df) < config['n']: continue

        # Подготовка данных
        num_data = zone_df.select_dtypes(include=[np.number]).fillna(0)
        input_data = create_style_ratios(num_data, zone)

        # МАСШТАБИРОВАНИЕ
        try:
            # Если данных мало или они константные, StandardScaler может выдать предупреждение,
            # но это лучше, чем подавать сырые нули.
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(input_data)
            
            # Добавим мизерный шум, если точки идентичны (защита от ConvergenceWarning)
            if np.allclose(features_scaled, features_scaled[0]):
                features_scaled += np.random.normal(0, 1e-7, features_scaled.shape)

            kmeans = KMeans(n_clusters=config['n'], random_state=42, n_init=20)
            labels = kmeans.fit_predict(features_scaled)
            
            for i, p_name in enumerate(zone_df['player_name']):
                final_results[p_name] = f"{config['prefix']}{labels[i] + 1}"
                
        except Exception as e:
            print(f"Ошибка в зоне {zone}: {e}")
            continue

    return final_results