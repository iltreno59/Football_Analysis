import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler, normalize
from .data_preparator import get_prepared_data

def create_style_ratios(df, zone):
    """
    Создает производные индексы специализации (Feature Engineering).
    """
    idx = pd.DataFrame(index=df.index)
    
    if zone == 'CM':
        idx['defensive_mindset'] = (df.get('Tackles', 0) + df.get('Recoveries', 0)) / (df.get('Passes', 1) + 1)
        idx['attack_involvement'] = (df.get('Shots', 0) + df.get('Touches in box', 0)) / (df.get('Passes', 1) + 1)
        idx['creative_risk'] = df.get('Through balls', 0) / (df.get('Passes', 1) + 1)
        
    elif zone == 'FB':
        idx['wing_aggression'] = (df.get('Crosses', 0) + df.get('Dribbles', 0)) / (df.get('Tackles', 1) + 1)
        idx['progression_style'] = df.get('Key passes', 0) / (df.get('Passes', 1) + 1)
        
    elif zone == 'ST':
        idx['physicality_ratio'] = df.get('Aerial battles won', 0) / (df.get('Shots', 1) + 1)
        idx['box_efficiency'] = df.get('Goals', 0) / (df.get('Touches in box', 1) + 1)
        
    elif zone == 'CB':
        idx['proactivity'] = (df.get('Interceptions', 0) + df.get('Tackles', 0)) / (df.get('Clearances', 1) + 1)
        idx['ball_playing_ratio'] = df.get('Accurate long balls', 0) / (df.get('Passes', 1) + 1)

    elif zone == 'WG':
        idx['directness'] = df.get('Shots', 0) / (df.get('Crosses', 1) + 1)
        idx['dribble_ratio'] = df.get('Dribbles', 0) / (df.get('Passes', 1) + 1)

    elif zone == 'GK':
        idx['proactivity'] = (df.get('Punches', 0) + df.get('High Claims', 0)) / (df.get('Saves', 1) + 1)

    # Если DataFrame пустой (например, для новой зоны), создаем нейтральную колонку
    if idx.empty or idx.shape[1] == 0:
        idx['placeholder'] = 0

    return idx.fillna(0)

def compute_clusters():
    df_scaled = get_prepared_data()
    if df_scaled is None: return None

    if df_scaled.index.name == 'player_name':
        df_scaled = df_scaled.reset_index()

    df_numeric = df_scaled.apply(pd.to_numeric, errors='coerce')
    
    zones_config = {
        'GK': {'n': 2, 'prefix': 'GK_'},
        'CB': {'n': 2, 'prefix': 'CB_'}, 
        'FB': {'n': 2, 'prefix': 'FB_'},
        'CM': {'n': 3, 'prefix': 'CM_'},
        'WG': {'n': 2, 'prefix': 'WG_'},
        'ST': {'n': 2, 'prefix': 'ST_'}
    }

    # Распределение по игровым зонам на основе медиан
    player_zones = {}
    for i, row in df_scaled.iterrows():
        name = row['player_name']
        pos = row['position']
        num_row = df_numeric.iloc[i]
        
        target = pos
        if pos == 'DF':
            target = 'FB' if (num_row.get('Crosses', 0) > 0.5 or num_row.get('Dribbles', 0) > 0.4) else 'CB'
        elif pos == 'MF':
            target = 'WG' if (num_row.get('Dribbles', 0) > 0.8 or num_row.get('Crosses', 0) > 1.2) else 'CM'
        elif pos == 'FW':
            target = 'ST'
        player_zones[name] = target

    final_results = {}
    for zone, config in zones_config.items():
        names_in_zone = [n for n, z in player_zones.items() if z == zone]
        zone_indices = df_scaled[df_scaled['player_name'].isin(names_in_zone)].index
        zone_data = df_numeric.loc[zone_indices]
        
        if len(zone_data) < config['n']: continue

        # 1. Подготовка базовых метрик (L1 нормализация профиля)
        cols_to_drop = ['Age', 'Appearances', 'Wins', 'Losses', 'player_id']
        base_features = zone_data.drop(columns=[c for c in cols_to_drop if c in zone_data.columns]).fillna(0)
        base_normalized = normalize(base_features.values, norm='l1', axis=1)
        
        # 2. Подготовка стилистических коэффициентов
        style_indices = create_style_ratios(base_features, zone)
        scaler = MinMaxScaler()
        scaled_indices = scaler.fit_transform(style_indices)
        
        # Усиливаем влияние коэффициентов (вес 2.0)
        weighted_indices = scaled_indices * 2.0
        
        # 3. Соединение данных
        combined_data = np.hstack([base_normalized, weighted_indices])

        # 4. Кластеризация
        kmeans = KMeans(
            n_clusters=config['n'], 
            init='k-means++', 
            random_state=42, 
            n_init=50, 
            max_iter=1000
        )
        labels = kmeans.fit_predict(combined_data)
        
        for i, idx_row in enumerate(zone_indices):
            player_name = df_scaled.loc[idx_row, 'player_name']
            final_results[player_name] = {'role': f"{config['prefix']}{labels[i] + 1}"}

    return final_results