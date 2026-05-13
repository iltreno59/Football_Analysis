import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import text
from .data_preparator import get_prepared_data
from app.core.db_conn import SessionLocal
from app.models import Player, Roles, ClusterAnalysis

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

def calculate_soft_probabilities(distances):
    # Используем инверсию расстояний для более высокой чувствительности.
    # Добавляем epsilon (1e-5), чтобы избежать деления на ноль.
    inv_distances = 1.0 / (distances + 1e-5)
    return inv_distances / np.sum(inv_distances, axis=1, keepdims=True)

def save_clusters_to_db(confidence_scores, confidence_threshold=0.3):
    """
    Сохраняет результаты кластеризации в БД с фильтром по уверенности.
    Перед добавлением новой записи удаляет все старые записи по игроку (избегает засорения БД).
    
    Args:
        confidence_scores: Dict с результатами (player_name -> {role, confidence, ...})
        confidence_threshold: Минимальный уровень уверенности (по умолчанию 0.3)
    
    Returns:
        (successful_count, skipped_count)
    """
    db = SessionLocal()
    successful = 0
    skipped = 0
    deleted_old = 0
    
    try:
        for player_name, result in confidence_scores.items():
            confidence = result.get('confidence', 0)
            
            # Пропускаем если уверенность ниже порога
            if confidence < confidence_threshold:
                skipped += 1
                continue
            
            role_name = result.get('role')
            if not role_name:
                skipped += 1
                continue
            
            # Получаем игрока по имени
            player = db.query(Player).filter(Player.player_name == player_name).first()
            if not player:
                print(f"  ⚠ Игрок '{player_name}' не найден в БД")
                skipped += 1
                continue
            
            # Удаляем ВСЕ старые записи о кластеризации для этого игрока
            old_records = db.query(ClusterAnalysis).filter(
                ClusterAnalysis.player_id == player.player_id
            ).delete()
            deleted_old += old_records
            
            # Извлекаем зону из имени роли (например, 'CM_1' -> 'CM')
            zone = role_name.split('_')[0]
            
            # Получаем или создаём роль в БД
            role = db.query(Roles).filter(
                Roles.role_name == role_name,
                Roles.zone == zone
            ).first()
            
            if not role:
                # Создаём новую роль
                role = Roles(
                    role_name=role_name,
                    zone=zone,
                    role_description=f"Автоматически определённая роль {role_name}"
                )
                db.add(role)
                db.flush()  # Чтобы получить role_id
            
            # Создаём новый анализ (старые уже удалены)
            analysis = ClusterAnalysis(
                player_id=player.player_id,
                role_id=role.role_id,
                trust_score=float(confidence)
            )
            db.add(analysis)
            
            successful += 1
        
        # Фиксируем все изменения
        db.commit()
        print(f"\n✅ СОХРАНЕНО В БД:")
        print(f"   Успешно: {successful} новых записей")
        print(f"   Удалено старых записей: {deleted_old}")
        print(f"   Пропущено (confidence < {confidence_threshold}): {skipped} записей")
        
        return successful, skipped
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ОШИБКА при сохранении в БД: {e}")
        import traceback
        traceback.print_exc()
        return 0, len(confidence_scores)
    
    finally:
        db.close()

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
        'GK': {'n': 3, 'prefix': 'GK_'}, 'CB': {'n': 3, 'prefix': 'CB_'}, 
        'FB': {'n': 3, 'prefix': 'FB_'}, 'CM': {'n': 5, 'prefix': 'CM_'},
        'WG': {'n': 3, 'prefix': 'WG_'}, 'ST': {'n': 4, 'prefix': 'ST_'}
    }

    player_zones = {}
    for i, row in df_working.iterrows():
        pos = str(row['position']).upper()
        # Статистические триггеры для уточнения роли
        has_wing_tendency = row.get('crosses', 0) > 1.2 or row.get('dribbles', 0) > 1.0
        
        if pos == 'DF':
            # Защитники: фланговые (FB) или центральные (CB)
            target = 'FB' if has_wing_tendency else 'CB'
        elif pos == 'MF':
            # Полузащитники: теперь ВСЕ MF идут в CM. 
            # Бруну и созидатели просто сформируют свой кластер внутри CM (например, CM_1)
            target = 'CM'
        elif pos == 'FW':
            # Нападающие: если много дриблинга/кроссов — вингер (WG), иначе — форвард (ST)
            target = 'WG' if has_wing_tendency else 'ST'
        else:
            target = pos if pos in zones_config else 'CM'
            
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
            
            # Добавляем Jitter (микро-шум), чтобы разлепить идентичные точки
            features_scaled += np.random.normal(0, 1e-6, features_scaled.shape)

            kmeans = KMeans(n_clusters=config['n'], random_state=42, n_init=30)
            labels = kmeans.fit_predict(features_scaled)
            
            # Получаем матрицу расстояний до всех центроидов
            distances = kmeans.transform(features_scaled)
            
            # Вычисляем вероятности через инверсию (вместо Softmax)
            probs = calculate_soft_probabilities(distances)
            
            for i, p_name in enumerate(zone_df['player_name']):
                c_idx = labels[i]
                role_name = f"{config['prefix']}{c_idx + 1}"
                final_labels[p_name] = role_name
                
                # Сохраняем результаты с высокой точностью
                confidence_scores[p_name] = {
                    'role': role_name,
                    'confidence': round(float(probs[i][c_idx]), 4),
                    'probabilities': {f"{config['prefix']}{j+1}": round(float(p), 4) for j, p in enumerate(probs[i])}
                }
        except Exception as e:
            print(f"Error in clustering {zone}: {e}")
            continue

    # ===== СОХРАНЕНИЕ РЕЗУЛЬТАТОВ В БД =====
    print("\n" + "=" * 80)
    print(">>> Сохранение результатов кластеризации в БД...")
    save_clusters_to_db(confidence_scores, confidence_threshold=0.3)
    print("=" * 80)
    
    return final_labels, confidence_scores