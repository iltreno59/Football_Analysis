import soccerdata as sd
import pandas as pd
from app.core.db_conn import SessionLocal
from app.models import League, Team, Player
import traceback

def fill_base_tables(leagues=['ENG-Premier League'], seasons='2324'):
    db = SessionLocal()
    fbref = sd.FBref(leagues=leagues, seasons=seasons)
    
    try:
        for league_name in leagues:
            # 1. ЛИГА
            db_league = db.query(League).filter(League.league_name == league_name).first()
            if not db_league:
                db_league = League(league_name=league_name, country="England")
                db.add(db_league)
                db.flush() 
            
            print(f"\n>>> Лига: {league_name}")

            # 2. КОМАНДЫ
            # Используем стандартную статистику, но сразу сбрасываем индексы
            team_df = fbref.read_team_season_stats(stat_type="standard").reset_index()
            
            # Чистим колонки (берем только название, если это кортеж)
            team_df.columns = [c[-1] if isinstance(c, tuple) and c[-1] != '' else (c[0] if isinstance(c, tuple) else str(c)) for c in team_df.columns]
            
            # Ищем колонку команды среди возможных вариантов
            t_col = next((c for c in ['team', 'squad'] if c in team_df.columns), None)
            
            if not t_col:
                print(f"Колонки команд: {team_df.columns.tolist()}")
                continue

            squads = team_df[t_col].unique()
            team_map = {} 
            for s_name in squads:
                db_team = db.query(Team).filter(Team.team_name == s_name).first()
                if not db_team:
                    db_team = Team(team_name=s_name, league_id=db_league.league_id)
                    db.add(db_team)
                    db.flush()
                team_map[s_name] = db_team.team_id
            
            print(f"Зарегистрировано команд: {len(team_map)}")

            # 3. ИГРОКИ
            print(f">>> Загрузка состава...")
            player_df = fbref.read_player_season_stats(stat_type="standard").reset_index()

            # Чистим колонки для игроков
            player_df.columns = [c[-1] if isinstance(c, tuple) and c[-1] != '' else (c[0] if isinstance(c, tuple) else str(c)) for c in player_df.columns]

            # Ищем нужные колонки
            p_col = next((c for c in ['player', 'Player'] if c in player_df.columns), None)
            sq_col = next((c for c in ['squad', 'team'] if c in player_df.columns), None)
            pos_col = next((c for c in ['pos', 'Pos'] if c in player_df.columns), None)

            if not p_col or not sq_col:
                continue

            new_players_count = 0
            for _, row in player_df.iterrows():
                p_name = row[p_col]
                t_name = row[sq_col]
                # Берем первую позицию для соблюдения 1НФ
                p_pos = str(row.get(pos_col, 'MF')).split(',')[0].strip()

                if t_name in team_map:
                    existing = db.query(Player).filter(
                        Player.player_name == p_name,
                        Player.team_id == team_map[t_name]
                    ).first()
                    
                    if not existing:
                        db.add(Player(
                            player_name=p_name,
                            team_id=team_map[t_name],
                            position=p_pos # Пишем в текстовый атрибут position
                        ))
                        new_players_count += 1
            
            db.commit()
            print(f"Добавлено игроков: {new_players_count}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR]: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fill_base_tables()