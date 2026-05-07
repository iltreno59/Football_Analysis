import soccerdata as sd
import pandas as pd
from app.core.db_conn import SessionLocal
from app.models import League, Team, Player
import traceback

def fill_base_tables(leagues=['ENG-Premier League'], seasons='2324'):
    db = SessionLocal()
    
    # Преобразование года
    try:
        start_year_for_db = int("20" + str(seasons)[:2])
    except:
        start_year_for_db = 2023

    fbref = sd.FBref(leagues=leagues, seasons=seasons)
    
    try:
        for league_name in leagues:
            # --- 1. ЛИГА ---
            db_league = db.query(League).filter(League.league_name == league_name).first()
            if not db_league:
                db_league = League(league_name=league_name, country="England")
                db.add(db_league)
                db.flush() 
            
            print(f"\n>>> Работа с лигой: {league_name}")

            # --- 2. КОМАНДЫ (TEAM) ---
            team_stats = fbref.read_team_season_stats(stat_type="standard")
            
            if 'squad' in team_stats.index.names:
                current_league_teams = team_stats.index.get_level_values('squad').unique()
            else:
                df_flat = team_stats.reset_index()
                team_col = next((c for c in ['squad', 'team'] if c in df_flat.columns), None)
                current_league_teams = df_flat[team_col].unique() if team_col else []

            team_map = {} 
            for squad_name in current_league_teams:
                db_team = db.query(Team).filter(
                    Team.team_name == squad_name, 
                    Team.league_id == db_league.league_id
                ).first()
                
                if not db_team:
                    db_team = Team(team_name=squad_name, league_id=db_league.league_id)
                    db.add(db_team)
                    db.flush()
                team_map[squad_name] = db_team.team_id
            
            print(f"Успешно обработано команд: {len(team_map)}")

           # --- 3. ИГРОКИ (PLAYER) ---
            player_stats = fbref.read_player_season_stats(stat_type="standard")
            
            # 1. Принудительный сброс индекса, чтобы всё стало колонками
            df_players = player_stats.reset_index()
            
            # 2. Очистка названия колонок. 
            # Если это кортеж (MultiIndex) -> последний элемент.
            # Если это просто строка -> её.
            new_cols = []
            for col in df_players.columns:
                if isinstance(col, tuple):
                    # Последний непустой элемент кортежа
                    clean_col = [c for c in col if c and not c.startswith('level_')][-1]
                    new_cols.append(clean_col)
                else:
                    new_cols.append(str(col))
            
            df_players.columns = new_cols

            # 3. Теперь поиск колонок в чистом списке имен
            p_col = next((c for c in ['player', 'Player'] if c in df_players.columns), None)
            t_col = next((c for c in ['squad', 'team', 'Squad', 'Team'] if c in df_players.columns), None)

            if not p_col or not t_col:
                print(f"Доступные колонки после очистки: {df_players.columns.tolist()}")
                raise KeyError(f"Не найдены критические колонки: player={p_col}, team={t_col}")

            new_players_count = 0
            for _, row in df_players.iterrows():
                squad_name = row[t_col]
                p_name = row[p_col]
                
                if squad_name in team_map:
                    db_player = db.query(Player).filter(
                        Player.player_name == p_name,
                        Player.team_id == team_map[squad_name]
                    ).first()
                    
                    if not db_player:
                        # Взятие позиции безопасно
                        pos = str(row['pos']).strip() if 'pos' in row and pd.notna(row['pos']) else None
                        
                        db_player = Player(
                            player_name=p_name,
                            position=pos,
                            team_id=team_map[squad_name]
                        )
                        db.add(db_player)
                        new_players_count += 1
            
            print(f"Игроков добавлено: {new_players_count}")

        db.commit()
        print("\n[FINISH] Все базовые данные в базе.")
        
    except Exception as e:
        db.rollback()
        print(f"\n[CRITICAL ERROR]: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fill_base_tables()