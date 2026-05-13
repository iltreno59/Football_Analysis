"""
Тестирование функции рекомендации упражнений
"""
from app.core.db_conn import SessionLocal
from app.models import Player, ClusterAnalysis, SeasonMetric, Benchmark, Metric
from app.ai.analyzer import recommend_exercises_for_player, print_recommendation_report


def find_player_with_deficit():
    """
    Находит игрока с ощутимым дефицитом для тестирования
    """
    db = SessionLocal()
    
    try:
        # Получаем всех игроков с кластеризацией
        players_with_clusters = db.query(Player).join(
            ClusterAnalysis, Player.player_id == ClusterAnalysis.player_id
        ).all()
        
        print(f"\n🔍 Поиск игрока с техническим дефицитом среди {len(players_with_clusters)} игроков...\n")
        
        # Технические метрики для поиска (избегаем Age, Yellow cards и т.д.)
        technical_metrics = {
            'Passes', 'Passes per match', 'Shots', 'Shots on target', 'Tackles', 
            'Interceptions', 'Clearances', 'Big chances created', 'Assists', 'Crosses',
            'Through balls', 'Accurate long balls', 'Recoveries', 'Dribbles'
        }
        
        for player in players_with_clusters[:50]:  # Проверяем первых 50
            # Получаем роль и лигу
            cluster = db.query(ClusterAnalysis).filter(
                ClusterAnalysis.player_id == player.player_id
            ).order_by(ClusterAnalysis.trust_score.desc()).first()
            
            if not cluster or not player.team:
                continue
            
            role = cluster.roles
            league_id = player.team.league_id
            
            # Проверяем дефициты по техническим метрикам
            season_metrics = db.query(SeasonMetric).join(
                Metric, SeasonMetric.metric_id == Metric.metric_id
            ).filter(
                SeasonMetric.player_id == player.player_id,
                Metric.metric_name.in_(technical_metrics)
            ).all()
            
            deficit_count = 0
            for sm in season_metrics:
                actual_value = float(sm.season_metric_value) if sm.season_metric_value else 0
                
                benchmark = db.query(Benchmark).filter(
                    Benchmark.metric_id == sm.metric_id,
                    Benchmark.role_id == role.role_id,
                    Benchmark.league_id == league_id
                ).first()
                
                if benchmark and benchmark.standard_deviation and float(benchmark.standard_deviation) != 0:
                    z_score = (actual_value - float(benchmark.mean)) / float(benchmark.standard_deviation)
                    if z_score <= -1:
                        deficit_count += 1
            
            if deficit_count > 0:
                print(f"✅ Найден игрок: {player.player_name} ({role.role_name}) - {deficit_count} техн. дефицитов")
                return player.player_id
        
        print("⚠️  Игроков с техническими дефицитом не найдено. Ищем любого с дефицитом...")
        # Fallback: ищем любого с дефицитом
        for player in players_with_clusters:
            cluster = db.query(ClusterAnalysis).filter(
                ClusterAnalysis.player_id == player.player_id
            ).order_by(ClusterAnalysis.trust_score.desc()).first()
            
            if not cluster or not player.team:
                continue
            
            role = cluster.roles
            league_id = player.team.league_id
            
            season_metrics = db.query(SeasonMetric).filter(
                SeasonMetric.player_id == player.player_id
            ).all()
            
            deficit_count = 0
            for sm in season_metrics:
                actual_value = float(sm.season_metric_value) if sm.season_metric_value else 0
                
                benchmark = db.query(Benchmark).filter(
                    Benchmark.metric_id == sm.metric_id,
                    Benchmark.role_id == role.role_id,
                    Benchmark.league_id == league_id
                ).first()
                
                if benchmark and benchmark.standard_deviation and float(benchmark.standard_deviation) != 0:
                    z_score = (actual_value - float(benchmark.mean)) / float(benchmark.standard_deviation)
                    if z_score <= -1:
                        deficit_count += 1
            
            if deficit_count > 0:
                print(f"✅ Найден игрок: {player.player_name} ({role.role_name}) - {deficit_count} дефицитов")
                return player.player_id
        
        return None
        
    finally:
        db.close()


if __name__ == "__main__":
    # Находим игрока с дефицитом
    player_id = find_player_with_deficit()
    
    if not player_id:
        print("\n⚠️  Не удалось найти подходящего игрока. Используем первого доступного.")
        db = SessionLocal()
        player = db.query(Player).join(
            ClusterAnalysis, Player.player_id == ClusterAnalysis.player_id
        ).first()
        player_id = player.player_id
        db.close()
    
    # Анализируем игрока
    print("\n" + "=" * 80)
    print(">>> Анализ игрока и рекомендация упражнений...")
    print("=" * 80)
    
    recommendation = recommend_exercises_for_player(
        player_id=player_id, user_id=None, user_login=None
    )
    print_recommendation_report(recommendation)
