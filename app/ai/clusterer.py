import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, robust_scale
from sklearn.decomposition import PCA
from .data_preparator import get_prepared_data

def create_style_ratios(numeric_data, zone):
    """
    Создаёт соотношения метрик для выявления СТИЛИСТИКИ.
    Вместо абсолютных объемов используем пропорции/ratios.
    
    Примеры:
    - Для CM: Tackles/Passes = защитность, Shots/Passes = атакованность
    - Для FB: Crosses/Passes = высокая игра, Dribbles/Passes = техничность
    - Для WG: Dribbles/Crosses = инди-стиль vs классический фланговый
    """
    ratios = pd.DataFrame(index=numeric_data.index)
    
    if zone == 'CM':
        # Защитный vs атакующий полузащитник
        ratios['defense_ratio'] = numeric_data.get('Tackles', 0) / (numeric_data.get('Passes', 1) + 1)
        ratios['attack_ratio'] = numeric_data.get('Shots', 0) / (numeric_data.get('Passes', 1) + 1)
        ratios['creativity_ratio'] = numeric_data.get('Through balls', 0) / (numeric_data.get('Passes', 1) + 1)
        
        # Длинная игра vs короткая передача
        ratios['long_ball_ratio'] = numeric_data.get('Accurate long balls', 0) / (numeric_data.get('Passes', 1) + 1)
        
        # Восстановление мяча
        ratios['ball_recovery_ratio'] = numeric_data.get('Recoveries', 0) / (numeric_data.get('Tackles', 1) + numeric_data.get('Interceptions', 1) + 1)
        
        # Создание шансов
        ratios['chance_creation'] = numeric_data.get('Big chances created', 0) / (numeric_data.get('Passes', 1) + 1)
        
    elif zone == 'FB':
        # Фланговый vs оборонительный защитник
        ratios['crossing_ratio'] = numeric_data.get('Crosses', 0) / (numeric_data.get('Passes', 1) + 1)
        ratios['defense_ratio'] = numeric_data.get('Tackles', 0) / (numeric_data.get('Passes', 1) + 1)
        
        # Техничность: дриблинг vs передачи
        ratios['dribble_ratio'] = numeric_data.get('Dribbles', 0) / (numeric_data.get('Passes', 1) + 1)
        
        # Участие в игре спереди
        ratios['attacking_ratio'] = numeric_data.get('Big chances created', 0) / (numeric_data.get('Passes', 1) + 1)
        
    elif zone == 'CB':
        # Длинная игра vs короткая передача
        ratios['long_ball_ratio'] = numeric_data.get('Accurate long balls', 0) / (numeric_data.get('Passes', 1) + numeric_data.get('Clearances', 1) + 1)
        
        # Игра в воздухе
        ratios['aerial_ratio'] = numeric_data.get('Aerial battles won', 0) / (numeric_data.get('Tackles', 1) + 1)
        
        # Агрессивность - перехваты vs кидки
        ratios['interception_ratio'] = numeric_data.get('Interceptions', 0) / (numeric_data.get('Tackles', 1) + 1)
        
        # Игра с мячом
        ratios['possession_ratio'] = numeric_data.get('Passes', 0) / (numeric_data.get('Clearances', 1) + numeric_data.get('Passes', 1) + 1)
        
    elif zone == 'WG':
        # Дриблер vs крайний пас
        ratios['dribble_ratio'] = numeric_data.get('Dribbles', 0) / (numeric_data.get('Crosses', 1) + numeric_data.get('Dribbles', 1) + 1)
        
        # Финишер vs создатель
        ratios['finish_ratio'] = numeric_data.get('Shots', 0) / (numeric_data.get('Big chances created', 1) + 1)
        
        # Активность на поле
        ratios['activity_ratio'] = (numeric_data.get('Tackles', 0) + numeric_data.get('Interceptions', 0)) / (numeric_data.get('Passes', 1) + 1)
        
    elif zone == 'ST':
        # Поле штрафной vs игра на выход
        ratios['box_ratio'] = numeric_data.get('Shots on target', 0) / (numeric_data.get('Shots', 1) + 1)
        
        # Изоляция в строке атаки
        ratios['selfishness'] = numeric_data.get('Shots', 0) / (numeric_data.get('Assists', 1) + numeric_data.get('Shots', 1) + 1)
        
        # Воздушное мастерство
        ratios['aerial_ratio'] = numeric_data.get('Aerial battles won', 0) / (numeric_data.get('Passes', 1) + 1)
        
    elif zone == 'GK':
        # Игра с ногами vs классический вратарь
        ratios['distribution_ratio'] = numeric_data.get('Goal Kicks', 0) / (numeric_data.get('Throws', 0) + numeric_data.get('Goal Kicks', 1) + 1)
        
        # Проактивность
        ratios['claim_ratio'] = (numeric_data.get('High Claims', 0) + numeric_data.get('Catches', 0)) / (numeric_data.get('Punches', 1) + 1)
        
    return ratios.fillna(0).clip(-5, 5)  # Защита от экстремальных выбросов

def compute_clusters(method='profile_kmeans'):
    df_scaled = get_prepared_data()
    if df_scaled is None: return None

    if df_scaled.index.name == 'player_name':
        df_scaled = df_scaled.reset_index()

    df_numeric_check = df_scaled.apply(pd.to_numeric, errors='coerce')

    # Конфигурация кластеров
    zones_config = {
        'GK': {'n': 2, 'prefix': 'GK_'},
        'CB': {'n': 2, 'prefix': 'CB_'}, 
        'FB': {'n': 2, 'prefix': 'FB_'},
        'CM': {'n': 4, 'prefix': 'CM_'},
        'WG': {'n': 2, 'prefix': 'WG_'},
        'ST': {'n': 3, 'prefix': 'ST_'}
    }

    player_zones = {}
    for i, row in df_scaled.iterrows():
        name = row['player_name']
        pos = row['position']
        num_row = df_numeric_check.iloc[i]
        
        target = pos
        # Улучшенная логика распределения
        if pos == 'DF':
            # Настоящий FB должен и кроссить, и пытаться обводить
            crosses = num_row.get('Crosses', 0)
            dribbles = num_row.get('Dribbles', 0)
            target = 'FB' if (crosses > 0.5 or dribbles > 0.4) else 'CB'
            
        elif pos == 'MF':
            # Вингеры — это про дриблинг и навесы, а не просто про удары
            dribbles = num_row.get('Dribbles', 0)
            crosses = num_row.get('Crosses', 0)
            target = 'WG' if (dribbles > 0.8 or crosses > 1.2) else 'CM'
            
        elif pos == 'FW':
            target = 'ST'
            
        player_zones[name] = target

    final_results = {}

    for zone, config in zones_config.items():
        names_in_zone = [n for n, z in player_zones.items() if z == zone]
        zone_data = df_numeric_check[df_scaled['player_name'].isin(names_in_zone)]
        
        # Фильтруем метрики: только объемы, без качества (%)
        cols_to_drop = ['Age', 'Appearances', 'Wins', 'Losses', 'player_id']
        quality_metrics = [c for c in zone_data.columns if '%' in c or 'accuracy' in c.lower()]
        
        final_drop = list(set(cols_to_drop + quality_metrics))
        numeric_data = zone_data.drop(columns=[c for c in final_drop if c in zone_data.columns]).fillna(0)

        if numeric_data.shape[1] == 0 or len(numeric_data) < config['n']:
            continue

        # Применяем выбранный метод кластеризации
        if method == 'ratio_kmeans':
            # *** РЕКОМЕНДУЕМЫЙ МЕТОД ***
            # Создаём ratio-based метрики, которые отражают СТИЛЬ игры
            clustering_data = create_style_ratios(numeric_data, zone)
            
        elif method == 'profile_kmeans':
            # L1-нормализация: представляем игрока как распределение действий
            from sklearn.preprocessing import normalize
            clustering_data = normalize(numeric_data.values, norm='l1', axis=1)
            clustering_data = pd.DataFrame(clustering_data, columns=numeric_data.columns, index=numeric_data.index)
            
        else:  # absolute_kmeans
            # Старый метод: абсолютные значения
            scaler = StandardScaler()
            clustering_data = pd.DataFrame(
                scaler.fit_transform(numeric_data),
                columns=numeric_data.columns,
                index=numeric_data.index
            )
        
        # Убедимся, что есть данные
        if clustering_data.shape[1] == 0:
            continue
        
        # KMeans с более агрессивной инициализацией
        kmeans = KMeans(
            n_clusters=config['n'], 
            random_state=42, 
            n_init=30,  # Больше попыток для лучшей сходимости
            max_iter=1000
        )
        labels = kmeans.fit_predict(clustering_data.fillna(0))
        
        for i, idx in enumerate(zone_data.index):
            player_name = df_scaled.loc[idx, 'player_name']
            final_results[player_name] = {'role': f"{config['prefix']}{labels[i] + 1}"}

    return final_results