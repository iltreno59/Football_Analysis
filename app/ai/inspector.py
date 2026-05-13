import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from .clusterer import compute_clusters
from .data_preparator import get_prepared_data

ZONE_METRICS = {
    'GK': ['Saves', 'Clean sheets', 'Penalties saved', 'Punches', 'High Claims'],
    'CB': ['Tackles', 'Interceptions', 'Clearances', 'Blocked shots', 'Aerial battles won'],
    'FB': ['Tackles', 'Interceptions', 'Crosses', 'Clearances'],
    'CM': ['Passes', 'Big chances created', 'Through balls', 'Recoveries'],
    'WG': ['Dribbles', 'Key passes', 'Assists', 'Crosses', 'Shots'],
    'ST': ['Goals', 'Shots on target', 'Shooting accuracy %', 'Touches in box']
}

def plot_radar(profiles, zone_name):
    # Ищем роли этой зоны (например, CB_1, CB_2)
    zone_roles = [r for r in profiles.index if str(r).startswith(zone_name)]
    if not zone_roles: return

    rows = profiles.loc[zone_roles]
    metrics = [m for m in ZONE_METRICS[zone_name] if m in rows.columns]
    
    if not metrics: return

    # Масштабирование для отрисовки (0...1)
    scaler = MinMaxScaler()
    df_plot = pd.DataFrame(scaler.fit_transform(rows[metrics]), index=rows.index, columns=metrics)

    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    for role, values in df_plot.iterrows():
        data = values.tolist()
        data += data[:1]
        ax.plot(angles, data, label=role, linewidth=2)
        ax.fill(angles, data, alpha=0.1)

    ax.set_thetagrids(np.degrees(angles[:-1]), metrics)
    plt.title(f"Тактический профиль: {zone_name}", size=15, y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    plt.show()

def inspect_results():
    print(">>> Сбор данных и запуск кластеризации...")
    clusters = compute_clusters()
    stats = get_prepared_data()
    
    if not clusters or stats is None:
        print("!!! Данные не найдены.")
        return

    res_df = pd.DataFrame.from_dict(clusters, orient='index')
    # Объединяем результаты и статистику по имени игрока (индексу)
    combined = stats.join(res_df, how='inner')
    
    if 'role' not in combined.columns:
        print("!!! Ошибка: Роли не назначены.")
        return

    # Считаем средний профиль каждой роли
    role_profiles = combined.groupby('role').mean(numeric_only=True)

    for zone in ZONE_METRICS.keys():
        plot_radar(role_profiles, zone)

if __name__ == "__main__":
    inspect_results()