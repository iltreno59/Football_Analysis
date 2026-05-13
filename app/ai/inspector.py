import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from .clusterer import compute_clusters
from .data_preparator import get_prepared_data

ZONE_METRICS = {
    'GK': ['Saves', 'Punches', 'High Claims', 'Accurate long balls', 'Passes'],
    'CB': ['Tackles', 'Interceptions', 'Clearances', 'Aerial battles won', 'Blocked shots', 'Accurate long balls'],
    'FB': ['Crosses', 'Dribbles', 'Key passes', 'Tackles', 'Interceptions', 'Big chances created'],
    # Для ST добавим метрику "воздушности" и "касаний", чтобы отличить столба от бегунка
    'ST': ['Goals', 'Shots on target', 'Touches in box', 'Aerial battles won', 'Key passes', 'Dribbles'],
    'WG': ['Dribbles', 'Crosses', 'Shots', 'Key passes', 'Goals', 'Assists'],
    'CM': ['Passes', 'Through balls', 'Recoveries', 'Tackles', 'Shots', 'Big chances created']
}

def plot_radar(profiles, zone_name, counts):
    # 1. Фильтрация ролей для конкретной зоны
    zone_roles = [r for r in profiles.index if str(r).startswith(zone_name)]
    if not zone_roles:
        return

    df_plot = profiles.loc[zone_roles]
    metrics = [m for m in ZONE_METRICS[zone_name] if m in df_plot.columns]
    
    if not metrics:
        return

    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    # 2. Создаем фигуру ЯВНО
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, polar=True)
    
    # Твои настройки сетки
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75])
    ax.set_yticklabels(["Ниже ср.", "Среднее", "Топ"], color="grey", size=9)

    # 3. Отрисовка данных
    for role, values in df_plot[metrics].iterrows():
        values = values.fillna(0)
        data = values.astype(float).tolist()
        data += data[:1]
        label_text = f"{role} (n={counts.get(role, 0)})"
        ax.plot(angles, data, label=label_text, linewidth=3, linestyle='solid')
        ax.fill(angles, data, alpha=0.2)

    # 4. Оформление осей
    ax.set_thetagrids(np.degrees(angles[:-1]), metrics, fontsize=11)
    
    plt.title(f"Тактический профиль: {zone_name}\n(Центр 0.5 = среднее по позиции)", size=16, y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
    plt.tight_layout()

    # 5. Сохранение
    os.makedirs('output_charts', exist_ok=True)
    filename = f'output_charts/radar_{zone_name}.png'
    
    # Используем fig.savefig вместо plt.savefig для надежности
    fig.canvas.draw()
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"    💾 График успешно сохранен: {filename}")
    
    plt.close(fig) # Обязательно закрываем фигуру, чтобы освободить память

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

    for col in combined.columns:
        if col != 'role':
            combined[col] = pd.to_numeric(combined[col], errors='coerce')

    role_counts = combined['role'].value_counts()

    numeric_cols = combined.select_dtypes(include=[np.number]).columns

    radar_df = combined.copy()

    for col in numeric_cols:
        v_min = radar_df[col].min()
        v_max = radar_df[col].max()

        if pd.notna(v_min) and pd.notna(v_max) and v_max > v_min:
            radar_df[col] = (radar_df[col] - v_min) / (v_max - v_min)
        else:
            radar_df[col] = 0.5

    radar_df = radar_df.fillna(0)

    role_profiles = radar_df.groupby('role').mean(numeric_only=True)
    
    print(f"\n>>> Найдено ролей: {len(role_profiles)}")
    print(role_counts.sort_index())

    print("\n>>> Шаг 3: Генерация графиков в 'output_charts'...")
    for zone in ZONE_METRICS.keys():
        plot_radar(role_profiles, zone, role_counts)

    print("\n✅ Проверь папку 'output_charts'. Теперь там должны быть цветные радары!")

if __name__ == "__main__":
    inspect_results()