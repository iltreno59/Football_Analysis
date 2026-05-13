import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from .clusterer import compute_clusters
from .data_preparator import get_prepared_data

# Метрики для отображения (включая расчетные коэффициенты)
ZONE_METRICS = {
    'GK': [
        'Saves', 
        'High Claims', 
        'Sweeper clearances', 
        'verticality',          # Насколько часто вратарь обостряет игру длинным пасом
        'Accurate long balls'
    ],
    'CB': [
        'Tackles', 
        'Interceptions', 
        'aerial_win_rate',     # Качество верховой борьбы (а не просто количество)
        'def_proactivity',     # Агрессивность в защите (отборы+перехваты на матч)
        'Headed Clearance'
    ],
    'FB': [
        'Crosses', 
        'Dribbles', 
        'creative_eff',        # Эффективность созидания (шансы на количество пасов)
        'def_proactivity',     # Активность в защите на фланге
        'Key passes'
    ],
    'CM': [
        'Passes', 
        'creative_eff',        # Поможет отличить "плеймейкера" от "разрушителя"
        'def_proactivity',     # Объем черновой работы
        'Through balls', 
        'verticality'          # Склонность к продвижению мяча вперед
    ],
    'WG': [
        'Dribbles', 
        'creative_eff',        # Насколько опасны его действия для соперника
        'finishing_clutch',    # Хладнокровие (голы относительно моментов)
        'Big chances created', 
        'Shots on target'
    ],
    'ST': [
        'Goals', 
        'finishing_clutch',    # Главный маркер форварда-киллера
        'Touches in box', 
        'aerial_win_rate',     # Поможет выделить "таргетмена"
        'Big chances missed'   # Важно видеть для оценки вовлеченности в моменты
    ]
}

def plot_radar(profiles, zone_name, counts):
    """
    ЛОГИКА ОТРИСОВКИ И СОХРАНЕНИЯ (БЕЗ ИЗМЕНЕНИЙ)
    """
    zone_roles = [r for r in profiles.index if str(r).startswith(zone_name)]
    if not zone_roles:
        return

    df_plot = profiles.loc[zone_roles]
    metrics = [m for m in ZONE_METRICS[zone_name] if m in df_plot.columns]
    
    if not metrics:
        return

    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, polar=True)
    
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75])
    ax.set_yticklabels(["Ниже ср.", "Среднее", "Топ"], color="grey", size=9)

    for role, values in df_plot[metrics].iterrows():
        data = values.tolist()
        data += data[:1]
        label_text = f"{role} (n={counts.get(role, 0)})"
        ax.plot(angles, data, label=label_text, linewidth=3, linestyle='solid')
        ax.fill(angles, data, alpha=0.2)

    ax.set_thetagrids(np.degrees(angles[:-1]), metrics, fontsize=11)
    
    plt.title(f"Тактический профиль: {zone_name}\n(Центр 0.5 = среднее по позиции)", size=16, y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
    plt.tight_layout()

    os.makedirs('output_charts', exist_ok=True)
    filename = f'output_charts/radar_{zone_name}.png'
    
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"    💾 График успешно сохранен: {filename}")
    
    plt.close(fig)

def inspect_results():
    print(">>> Шаг 1: Кластеризация...")
    clusters_dict = compute_clusters()
    
    print(">>> Шаг 2: Подготовка данных...")
    stats_df = get_prepared_data()
    
    if not clusters_dict or stats_df is None:
        print("!!! Ошибка: Данные пусты.")
        return

    # Подготовка DF с ролями
    res_df = pd.DataFrame.from_dict(clusters_dict, orient='index', columns=['role'])
    res_df.index.name = 'player_name'
    
    if 'player_name' in stats_df.columns:
        stats_df = stats_df.set_index('player_name')
    
    combined = stats_df.join(res_df, how='inner')

    # --- ДОБАВЛЕНИЕ КОЭФФИЦИЕНТОВ ---
    combined['creative_risk'] = combined.get('Through balls', 0) / (combined.get('Passes', 1) + 1)
    combined['defensive_volume'] = (combined.get('Tackles', 0) + combined.get('Interceptions', 0) + combined.get('Recoveries', 0))
    combined['aerial_dominance'] = combined.get('Aerial battles won', 0) / (combined.get('Aerial battles lost', 0) + 1)
    combined['directness'] = (combined.get('Accurate long balls', 0) + combined.get('Crosses', 0)) / (combined.get('Passes', 1) + 1)
    combined['finishing_skill'] = combined.get('Goals', 0) / (combined.get('Shots on target', 1) + 1)
    # Внутри inspect_results, после объединения stats_df и res_df:

    # 1. Эффективность созидания
    combined['creative_eff'] = (combined.get('Big chances created', 0) + combined.get('Assists', 0)) / (combined.get('Passes', 1) + 1)

    # 2. Качество верховой борьбы
    combined['aerial_win_rate'] = combined.get('Aerial battles won', 0) / (combined.get('Aerial battles won', 0) + combined.get('Aerial battles lost', 0) + 1)

    # 3. Реализация моментов
    combined['finishing_clutch'] = combined.get('Goals', 0) / (combined.get('Big chances missed', 0) + 1)

    # 4. Агрессия в защите
    combined['def_proactivity'] = (combined.get('Tackles', 0) + combined.get('Interceptions', 0) + combined.get('Recoveries', 0)) / (combined.get('Appearances', 1) + 1)

    # 5. Вертикальность (Directness)
    combined['verticality'] = (combined.get('Accurate long balls', 0) + combined.get('Through balls', 0)) / (combined.get('Passes', 1) + 1)
    # Принудительная конвертация числовых столбцов
    cols_to_convert = combined.columns.drop(['role', 'position'], errors='ignore')
    for col in cols_to_convert:
        combined[col] = pd.to_numeric(combined[col], errors='coerce')

    role_counts = combined['role'].value_counts()

    # --- ПОЗОНАЛЬНАЯ НОРМАЛИЗАЦИЯ ---
    radar_data_list = []
    # Группируем по позициям (GK, CB, CM и т.д.) и нормализуем внутри каждой группы
    for pos in combined['position'].unique():
        zone_subset = combined[combined['position'] == pos].copy()
        numeric_cols = zone_subset.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            v_min, v_max = zone_subset[col].min(), zone_subset[col].max()
            if v_max > v_min:
                zone_subset[col] = (zone_subset[col] - v_min) / (v_max - v_min)
            else:
                zone_subset[col] = 0.5
        radar_data_list.append(zone_subset)
    
    radar_df = pd.concat(radar_data_list).fillna(0)

    # Группируем по ролям для получения средних профилей
    role_profiles = radar_df.groupby('role').mean(numeric_only=True)
    
    print(f"\n>>> Найдено ролей: {len(role_profiles)}")
    print(role_counts.sort_index())

    print("\n>>> Шаг 3: Генерация графиков в 'output_charts'...")
    for zone in ZONE_METRICS.keys():
        plot_radar(role_profiles, zone, role_counts)

    print("\n✅ Все готово! Графики в папке 'output_charts' теперь отражают специфику позиций.")

if __name__ == "__main__":
    inspect_results()