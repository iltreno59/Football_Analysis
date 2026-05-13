import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from .clusterer import compute_clusters
from .data_preparator import get_prepared_data

ZONE_METRICS = {
    'GK': [
        'Saves', 'Penalties saved', 'Punches', 'High Claims', 'Accurate long balls', 'Passes', 
        'Crosses stopped', 'Defensive actions outside box'
    ],
    'CB': [
        'Tackles', 'Interceptions', 'Clearances', 'Aerial battles won', 
        'Blocked shots', 'Accurate long balls', 'Headed Clearance', 
    ],
    'FB': [
        'Tackles', 'Interceptions', 'Crosses', 'Dribbles', 
        'Big chances created', 'Successful 50/50s', 'Clearances', 'Key passes'
    ],
    'CM': [
        'Passes', 'Through balls', 'Recoveries', 'Tackles', 
        'Shots', 'Big chances created', 'Interceptions', 'Accurate long balls', 'Touches in box'
    ],
    'WG': [
        'Dribbles', 'Crosses', 'Shots', 'Key passes', 
        'Assists', 'Big chances created', 'Goals', 'Shots on target', 'Passes'
    ],
    'ST': [
        'Goals', 'Shots on target', 'Touches in box', 'Passes', 'Key passes',
        'Big chances missed','Interceptions'
    ]
}

def plot_radar(profiles, zone_name):
    # Ищем роли этой зоны
    zone_roles = [r for r in profiles.index if str(r).startswith(zone_name)]
    if not zone_roles: return

    rows = profiles.loc[zone_roles]
    metrics = [m for m in ZONE_METRICS[zone_name] if m in rows.columns]
    
    if not metrics: return

    # Данные уже подготовлены в inspect_results (Z-score + clip + offset)
    df_plot = rows[metrics]

    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    
    # Настройка сетки: 0.5 — это среднее (центр), 0 — минимум, 1 — максимум
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75])
    ax.set_yticklabels(["Ниже ср.", "Среднее", "Топ"], color="grey", size=8)

    for role, values in df_plot.iterrows():
        data = values.tolist()
        data += data[:1]
        ax.plot(angles, data, label=role, linewidth=2.5, linestyle='solid')
        ax.fill(angles, data, alpha=0.15)

    ax.set_thetagrids(np.degrees(angles[:-1]), metrics)
    
    plt.title(f"Тактический профиль ролей: {zone_name}\n(Центр круга = среднее по позиции)", size=14, y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    plt.tight_layout()
    #plt.show()
    #Сохраняем вместо отображения
    import os
    os.makedirs('output_charts', exist_ok=True)
    filename = f'output_charts/radar_{zone_name}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"    💾 График сохранен: {filename}")
    plt.close()

def inspect_results():
    print(">>> Сбор данных и запуск кластеризации (метод: ratio_kmeans)...")
    clusters = compute_clusters(method='ratio_kmeans')
    stats = get_prepared_data()
    
    if not clusters or stats is None:
        print("!!! Данные не найдены.")
        return

    res_df = pd.DataFrame.from_dict(clusters, orient='index')
    combined = stats.join(res_df, how='inner')
    
    if 'role' not in combined.columns:
        print("!!! Ошибка: Роли не назначены.")
        return

    # Конвертируем все числовые колонки
    cols_to_convert = combined.columns.drop(['role', 'position'], errors='ignore')
    for col in cols_to_convert:
        combined[col] = pd.to_numeric(combined[col], errors='coerce')

    # ============= АНАЛИЗ RATIO-BASED МЕТРИК ПО КЛАСТЕРАМ =============
    print("\n" + "=" * 80)
    print("АНАЛИЗ КЛАСТЕРИЗАЦИИ ПО СТИЛИСТИКЕ ИГРЫ")
    print("=" * 80)
    
    # Для каждой позиции показываем, чем отличаются кластеры
    zone_analysis = {
        'CM': [
            ('defense', 'Tackles', 'Passes', 'защитность (перехваты/передачи)'),
            ('attack', 'Shots', 'Passes', 'атакованность (удары/передачи)'),
            ('creation', 'Big chances created', 'Passes', 'креативность (шансы/передачи)'),
        ],
        'FB': [
            ('crossing', 'Crosses', 'Passes', 'фланговость (кроссы/передачи)'),
            ('defense', 'Tackles', 'Passes', 'защитность (перехваты/передачи)'),
        ],
        'CB': [
            ('aerial', 'Aerial battles won', 'Tackles', 'воздушное мастерство (дуэли/перехваты)'),
            ('passing', 'Passes', 'Clearances', 'игра с мячом (передачи/отборы)'),
        ],
        'WG': [
            ('finishing', 'Shots', 'Big chances created', 'финишность (удары/шансы)'),
        ],
        'ST': [
            ('box_efficiency', 'Shots on target', 'Shots', 'точность удара (на цель/всего)'),
        ]
    }
    
    for zone, ratios_list in zone_analysis.items():
        zone_roles = sorted(combined[combined['role'].str.startswith(zone)]['role'].unique())
        if len(zone_roles) < 2:
            continue
            
        print(f"\n>>> {zone} (Найдено кластеров: {len(zone_roles)})")
        
        for ratio_name, metric_a, metric_b, desc in ratios_list:
            # Проверяем, есть ли метрики в датасете
            col_a = metric_a if metric_a in combined.columns else None
            col_b = metric_b if metric_b in combined.columns else None
            
            if col_a is None or col_b is None:
                print(f"    ⚠ {desc}: метрика '{metric_a}' или '{metric_b}' не найдена")
                continue
            
            print(f"\n    📊 {desc.upper()}:")
            
            for role in zone_roles:
                role_data = combined[combined['role'] == role]
                val_a = pd.to_numeric(role_data[col_a], errors='coerce').sum()
                val_b = pd.to_numeric(role_data[col_b], errors='coerce').sum()
                
                if val_b > 0:
                    ratio_val = val_a / val_b
                    n_players = len(role_data)
                    print(f"      {role:10s}: {ratio_val:7.4f}  (n={n_players})")
    
    # ============= ВИЗУАЛИЗАЦИЯ ПРОФИЛЕЙ =============
    print(f"\n" + "=" * 80)
    print(">>> Построение тактических профилей...")
    print("=" * 80)
    
    numeric_cols = combined.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        val_min = combined[col].min()
        val_max = combined[col].max()
        if val_max > val_min:
            combined[col] = (combined[col] - val_min) / (val_max - val_min)
        else:
            combined[col] = 0.5

    role_profiles = combined.groupby('role').mean(numeric_only=True)
    
    print(f">>> Всего ролей: {len(role_profiles)}\n")

    for zone in ZONE_METRICS.keys():
        plot_radar(role_profiles, zone)
    
    print("\n" + "=" * 80)
    print("✅ КЛАСТЕРИЗАЦИЯ ЗАВЕРШЕНА")
    print("=" * 80)
    print(f"📊 Графики сохранены в папке: output_charts/")
    print(f"📈 Всего найдено уникальных ролей: {len(role_profiles)}")
    print(f"\n📋 Итоговое распределение ролей:")
    role_dist = combined['role'].value_counts().sort_index()
    for role, count in role_dist.items():
        print(f"   {role:10s}: {count:3d} игроков")

if __name__ == "__main__":
    inspect_results()