import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from .clusterer import compute_clusters
from .data_preparator import get_prepared_data

# Твои метрики для отрисовки
ZONE_METRICS = {
    'GK': ['saves', 'high claims', 'sweeper clearances', 'goal kicks', 'accurate long balls'],
    'CB': ['tackles', 'interceptions', 'aerial battles won', 'clearances', 'headed clearance'],
    'FB': ['crosses', 'dribbles', 'tackles', 'interceptions', 'key passes'],
    'CM': ['passes', 'through balls', 'big chances created', 'tackles', 'interceptions'],
    'WG': ['dribbles', 'crosses', 'shots', 'big chances created', 'key passes'],
    'ST': ['shots on target', 'goals', 'shots', 'assists', 'aerial battles won']
}

def run_inspection():
    print(">>> Шаг 1: Кластеризация...")
    clusters = compute_clusters()
    if not clusters:
        print("Ошибка: Кластеры не сформированы.")
        return

    print(">>> Шаг 2: Подготовка данных для визуализации...")
    raw_data = get_prepared_data()
    if raw_data is None: return
    
    df = raw_data.reset_index()
    df.columns = [c.lower() for c in df.columns]
    
    # Добавляем результаты кластеризации
    df['role'] = df['player_name'].map(clusters)
    df = df.dropna(subset=['role'])

    # --- НОВОЕ: ВЫВОД СОСТАВА КЛАСТЕРОВ ТЕКСТОМ ---
    print("\n>>> СОСТАВ КЛАСТЕРОВ:")
    for role in sorted(df['role'].unique()):
        players = df[df['role'] == role]['player_name'].tolist()
        print(f"\n🔹 {role} ({len(players)} чел.):")
        print(", ".join(sorted(players)))
    print("\n" + "="*30 + "\n")

    # Создаем папку, если нет
    os.makedirs('output_charts', exist_ok=True)

    # Отрисовка графиков
    for zone, metrics in ZONE_METRICS.items():
        # Приводим метрики в списке к нижнему регистру, чтобы совпало с df.columns
        metrics = [m.lower() for m in metrics]
        
        zone_df = df[df['role'].str.startswith(zone)].copy()
        if zone_df.empty: continue

        # Проверяем, какие из запрошенных метрик реально есть в DF
        available_metrics = [m for m in metrics if m in zone_df.columns]
        missing = set(metrics) - set(available_metrics)
        if missing:
            print(f"⚠️ Внимание: Для зоны {zone} не найдены колонки: {missing}")
        
        if not available_metrics: continue

        # Нормализация (используем только доступные метрики)
        for m in available_metrics:
            v_min, v_max = zone_df[m].min(), zone_df[m].max()
            zone_df[m] = (zone_df[m] - v_min) / (v_max - v_min) if v_max > v_min else 0.5

        # Группировка теперь не упадет
        role_profiles = zone_df.groupby('role')[available_metrics].mean()
        
        # Настройка углов под количество ДОСТУПНЫХ метрик
        angles = np.linspace(0, 2 * np.pi, len(available_metrics), endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        for role, row in role_profiles.iterrows():
            values = row.values.flatten().tolist()
            values += values[:1]
            ax.plot(angles, values, linewidth=2, label=role)
            ax.fill(angles, values, alpha=0.1)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(available_metrics) # Подписи только существующих колонок
        ax.set_ylim(0, 0.8)
        
        plt.title(f"Сравнение ролей в зоне {zone}")
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        path = f"output_charts/radar_{zone}.png"
        plt.savefig(path, bbox_inches='tight')
        plt.close()
        print(f"💾 График сохранен: {path}")

if __name__ == "__main__":
    run_inspection()