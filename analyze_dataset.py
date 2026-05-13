import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import seaborn as sns
import matplotlib.pyplot as plt

# Загружаем датасет
df = pd.read_csv('app/data_loaders/dataset.csv')

print("=" * 80)
print("АНАЛИЗ ДАТАСЕТА FOOTBALL")
print("=" * 80)

# 1. БАЗОВАЯ СТАТИСТИКА
print("\n1. РАЗМЕР И ТИПЫ ДАННЫХ")
print(f"   Всего игроков: {len(df)}")
print(f"   Всего колонок: {len(df.columns)}")
print(f"\n   Позиции в датасете:")
print(df['Position'].value_counts())

# 2. ПРОПУСКИ И ПОЛНОТА ДАННЫХ
print("\n2. ПОЛНОТА ДАННЫХ")
print(f"   Всего пустых ячеек: {df.isnull().sum().sum()}")
print(f"\n   Пустые ячейки по колонкам (топ 15):")
null_cols = df.isnull().sum().sort_values(ascending=False).head(15)
for col, count in null_cols.items():
    pct = (count / len(df)) * 100
    print(f"   {col:30s}: {count:3d} ({pct:5.1f}%)")

# 3. ЧИСЛОВЫЕ МЕТРИКИ (исключаем текст и ID)
print("\n3. ЧИСЛОВЫЕ МЕТРИКИ")
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols = [c for c in numeric_cols if c not in ['Jersey Number', 'Age']]
print(f"   Всего числовых метрик: {len(numeric_cols)}")
print(f"\n   Метрики с большим кол-вом нулей (>50% нулей):")

for col in numeric_cols:
    zero_pct = (df[col] == 0).sum() / len(df) * 100
    if zero_pct > 50:
        mean_val = df[df[col] > 0][col].mean()
        print(f"   {col:30s}: {zero_pct:5.1f}% нулей, средн. (>0): {mean_val:7.2f}")

# 4. АНАЛИЗ ПО ПОЗИЦИЯМ - КАКИЕ МЕТРИКИ РЕАЛЬНО РАЗЛИЧАЮТСЯ
print("\n4. ВАРИАТИВНОСТЬ МЕТРИК ПО ПОЗИЦИЯМ")
print("   (CV = Coefficient of Variation - чем выше, тем больше различий между позициями)")

position_cv = {}
for col in numeric_cols:
    col_data = pd.to_numeric(df[col], errors='coerce')
    position_stats = df.groupby('Position')[col].apply(lambda x: pd.to_numeric(x, errors='coerce').mean())
    
    # Coefficient of Variation (std / mean)
    if position_stats.mean() > 0:
        cv = position_stats.std() / position_stats.mean()
        position_cv[col] = cv

# Выбираем метрики с наибольшей вариативностью между позициями
top_varying = sorted(position_cv.items(), key=lambda x: x[1], reverse=True)[:15]
print("\n   Топ-15 метрик с наибольшей вариативностью:")
for col, cv in top_varying:
    print(f"   {col:30s}: CV = {cv:6.3f}")

# 5. КОРРЕЛЯЦИИ МЕЖДУ МЕТРИКАМИ
print("\n5. КОРРЕЛЯЦИИ ДЛЯ ЦЕНТРАЛЬНЫХ ПОЛУЗАЩИТНИКОВ (CM)")
cm_data = df[df['Position'].isin(['MF', 'Midfielder'])]
print(f"   Центральных полузащитников в наборе: {len(cm_data)}")

if len(cm_data) > 5:
    # Выбираем метрики для CM
    cm_metrics = ['Passes', 'Tackles', 'Shots', 'Interceptions', 'Recoveries', 
                  'Through balls', 'Accurate long balls', 'Big chances created']
    
    cm_numeric = cm_data[cm_metrics].apply(pd.to_numeric, errors='coerce')
    
    print(f"\n   Матрица корреляций (для метрик CM):")
    corr_matrix = cm_numeric.corr()
    print(corr_matrix)
    
    # Найдем сильно коррелированные метрики
    print(f"\n   Пары с высокой корреляцией (>0.7):")
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr_val = corr_matrix.iloc[i, j]
            if abs(corr_val) > 0.7:
                print(f"   {corr_matrix.columns[i]:25s} <-> {corr_matrix.columns[j]:25s}: {corr_val:6.3f}")

# 6. РАСПРЕДЕЛЕНИЕ ЗНАЧЕНИЙ (нужна ли логарифмическая шкала?)
print("\n6. РАСПРЕДЕЛЕНИЕ КЛЮЧЕВЫХ МЕТРИК (АСИММЕТРИЯ)")
key_metrics = ['Passes', 'Tackles', 'Shots', 'Assists', 'Goals', 'Dribbles']
print("   (Skewness > 1 означает, что метрика сильно скошена - много нулей/малых значений)")
for col in key_metrics:
    if col in df.columns:
        col_data = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(col_data) > 0:
            skew = col_data.skew()
            print(f"   {col:20s}: skewness = {skew:6.2f}, mean = {col_data.mean():7.2f}, std = {col_data.std():7.2f}")

# 7. ВОЗМОЖНЫЕ СТИЛИСТИЧЕСКИЕ МЕТРИКИ
print("\n7. ПОТЕНЦИАЛЬНЫЕ RATIO-BASED МЕТРИКИ (для выявления стилистики)")
print("   Вместо абсолютных значений, использовать ПРОПОРЦИИ:")
print("   - Passes vs Tackles: техничный vs боевой полузащитник")
print("   - Shots vs Through balls: голеадор vs создатель")
print("   - Long balls vs Short passes: длинная игра vs короткие передачи")
print("   - Aerial battles won vs Ground duels: воздушный vs наземный")

# Проверяем, есть ли эти метрики
required_metrics = ['Passes', 'Tackles', 'Shots', 'Through balls', 'Accurate long balls', 
                   'Dribbles', 'Crosses', 'Assists', 'Goals']
print(f"\n   Доступные метрики из нужных: {sum(m in df.columns for m in required_metrics)}/{len(required_metrics)}")
for m in required_metrics:
    status = "✓" if m in df.columns else "✗"
    print(f"   {status} {m}")

print("\n" + "=" * 80)
