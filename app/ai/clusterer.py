import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from .data_preparator import get_prepared_data

def create_style_ratios(numeric_data, zone):
    ratios = pd.DataFrame(index=numeric_data.index)
    
    def g(name):
        if name in numeric_data.columns:
            return numeric_data[name]
        return pd.Series(0.0, index=numeric_data.index)

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
    elif zone == 'GK':
        ratios['dist'] = g('goal kicks') / (g('throw outs') + g('goal kicks') + 1)
        ratios['clm'] = (g('high claims') + g('catches')) / (g('punches') + 1)
    
    if ratios.empty or ratios.sum().sum() == 0:
        cols = ['passes', 'tackles', 'shots']
        existing = [c for c in cols if c in numeric_data.columns]
        return numeric_data[existing] if existing else numeric_data
        
    return ratios

def softmax(distances, T=1.0):
    exp_dist = np.exp(-distances / T)
    return exp_dist / np.sum(exp_dist, axis=1, keepdims=True)

def compute_clusters():
    raw_df = get_prepared_data()
    if raw_df is None: return {}, {}

    df_working = raw_df.reset_index()
    df_working.columns = [c.lower() for c in df_working.columns]
    
    if 'position' in df_working.columns:
        df_working['position'] = df_working['position'].astype(str).str.strip().str.upper()
    
    if 'name' in df_working.columns and 'player_name' not in df_working.columns:
        df_working = df_working.rename(columns={'name': 'player_name'})

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
            target = 'ST' if pos == 'FW' else (pos if pos in zones_config else 'CM')
        player_zones[row['player_name']] = target

    final_labels = {}
    confidence_scores = {}

    for zone, config in zones_config.items():
        names = [n for n, z in player_zones.items() if z == zone]
        zone_df = df_working[df_working['player_name'].isin(names)]
        if len(zone_df) < config['n']: continue

        num_data = zone_df.select_dtypes(include=[np.number]).fillna(0)
        input_data = create_style_ratios(num_data, zone)

        try:
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(input_data)
            
            if np.allclose(features_scaled, features_scaled[0]):
                features_scaled += np.random.normal(0, 1e-7, features_scaled.shape)

            kmeans = KMeans(n_clusters=config['n'], random_state=42, n_init=30)
            labels = kmeans.fit_predict(features_scaled)
            
            distances = kmeans.transform(features_scaled)
            probs = softmax(distances, T=1.0)
            
            for i, p_name in enumerate(zone_df['player_name']):
                c_idx = labels[i]
                role_name = f"{config['prefix']}{c_idx + 1}"
                final_labels[p_name] = role_name
                confidence_scores[p_name] = {
                    'role': role_name,
                    'confidence': round(float(probs[i][c_idx]), 3),
                    'probabilities': {f"{config['prefix']}{j+1}": round(float(p), 3) for j, p in enumerate(probs[i])}
                }
        except Exception as e:
            continue

    return final_labels, confidence_scores