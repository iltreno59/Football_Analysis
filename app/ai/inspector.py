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
    zone_roles = [r for r in profiles.index if str(r).startswith(zone_name)]
    if not zone_roles: return

    rows = profiles.loc[zone_roles]
    # Проверка регистра: Pandas чувствителен к 'Goals' vs 'goals'
    metrics = [m for m in ZONE_METRICS[zone_name] if m in rows.columns]
    
    if not metrics:
        print(f"!!! Для зоны {zone_name} не найдено ни одной метрики из списка в столбцах: {list(rows.columns)}")
        return

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

    # 1. Превращаем результат кластеризации в DataFrame
    res_df = pd.DataFrame.from_dict(clusters, orient='index') # Индекс — player_name
    
    # 2. Подготавливаем stats: если player_name в индексе — сбрасываем, чтобы сделать join
    if stats.index.name == 'player_name' or 'player_name' not in stats.columns:
        stats = stats.reset_index()
    
    # 3. Объединяем по колонке player_name
    combined = stats.merge(res_df, left_on='player_name', right_index=True)
    
    if combined.empty:
        print("!!! Ошибка объединения: имена игроков в кластерах и статистике не совпали.")
        return

    print("\n>>> РАСПРЕДЕЛЕНИЕ ПО РОЛЯМ:")
    print(combined['role'].value_counts())
    print("-" * 30)

    # 4. Группируем. ВАЖНО: убеждаемся, что метрики числовые
    # Сначала конвертируем всё, кроме имен и ролей, в числа
    cols_to_numeric = combined.columns.drop(['player_name', 'position', 'role'])
    combined[cols_to_numeric] = combined[cols_to_numeric].apply(pd.to_numeric, errors='coerce')

    # Считаем среднее для каждой роли
    role_profiles = combined.groupby('role')[cols_to_numeric].mean()

    # 5. Рисуем радары
    for zone in ZONE_METRICS.keys():
        plot_radar(role_profiles, zone)

if __name__ == "__main__":
    inspect_results()