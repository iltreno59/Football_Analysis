import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from .clusterer import compute_clusters
from .data_preparator import get_prepared_data

ZONE_METRICS = {
    'GK': ['saves', 'high claims', 'sweeper clearances', 'goal kicks', 'accurate long balls'],
    'CB': ['tackles', 'interceptions', 'aerial battles won', 'clearances', 'headed clearance'],
    'FB': ['crosses', 'dribbles', 'tackles', 'interceptions', 'key passes'],
    'CM': ['passes', 'through balls', 'big chances created', 'tackles', 'interceptions'],
    'WG': ['dribbles', 'crosses', 'shots', 'big chances created', 'key passes'],
    'ST': ['shots on target', 'goals', 'shots', 'assists', 'aerial battles won']
}

def run_inspection():
    print(">>> Шаг 1: Кластеризация и расчет уверенности...")
    labels, confidence_data = compute_clusters()
    
    if not labels:
        print("Ошибка: Данные не получены.")
        return

    print(">>> Шаг 2: Подготовка отчета...")
    raw_data = get_prepared_data()
    if raw_data is None: return
    
    df = raw_data.reset_index()
    df.columns = [c.lower() for c in df.columns]
    
    # Мапим результаты
    df['role'] = df['player_name'].map(labels)
    df = df.dropna(subset=['role'])

    print("\n>>> ДЕТАЛЬНЫЙ СОСТАВ КЛАСТЕРОВ (С УВЕРЕННОСТЬЮ):")
    
    for role in sorted(df['role'].unique()):
        role_players = df[df['role'] == role]['player_name'].tolist()
        print(f"\n🔹 {role} ({len(role_players)} чел.):")
        
        # Сортируем игроков внутри кластера по убыванию уверенности
        players_with_conf = []
        for p in role_players:
            conf = confidence_data[p]['confidence']
            players_with_conf.append((p, conf))
        
        players_with_conf.sort(key=lambda x: x[1], reverse=True)
        
        # Выводим строку с именами и уверенностью (в скобках)
        formatted_list = [f"{name} ({c})" for name, c in players_with_conf]
        print(", ".join(formatted_list))

    # Генерация графиков
    os.makedirs('output_charts', exist_ok=True)
    for zone, metrics in ZONE_METRICS.items():
        metrics_low = [m.lower() for m in metrics]
        zone_df = df[df['role'].str.startswith(zone)].copy()
        if zone_df.empty: continue

        available_metrics = [m for m in metrics_low if m in zone_df.columns]
        if not available_metrics: continue

        # Нормализация
        for m in available_metrics:
            v_min, v_max = zone_df[m].min(), zone_df[m].max()
            zone_df[m] = (zone_df[m] - v_min) / (v_max - v_min) if v_max > v_min else 0.5

        role_profiles = zone_df.groupby('role')[available_metrics].mean()
        angles = np.linspace(0, 2 * np.pi, len(available_metrics), endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        for role, row in role_profiles.iterrows():
            values = row.values.flatten().tolist()
            values += values[:1]
            ax.plot(angles, values, linewidth=2, label=role)
            ax.fill(angles, values, alpha=0.1)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(available_metrics)
        ax.set_ylim(0, 1.1) 
        
        plt.title(f"Сравнение ролей: {zone}")
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        plt.savefig(f"output_charts/radar_{zone}.png", bbox_inches='tight')
        plt.close()

    print("\n✅ Инспекция завершена. Графики обновлены в 'output_charts'.")

if __name__ == "__main__":
    run_inspection()