import pandas as pd
from app.core.db_conn import SessionLocal
from app.models import League, Team, Player
import traceback

def fill_base_from_kaggle(csv_path=r"D:\\Football_Analysis\\app\\data_loaders\\dataset.csv"):
    db = SessionLocal()
    
    try:
        # Читаем файл
        print(f">>> Чтение файла: {csv_path}")
        df = pd.read_csv(csv_path)

        # 1. СОЗДАЕМ ЛИГУ
        # В датасете нет колонки с лигой, поэтому создаем её вручную
        league_name = 'English Premier League'
        db_league = db.query(League).filter_by(league_name=league_name).first()
        if not db_league:
            print(f">>> Регистрация лиги: {league_name}")
            db_league = League(league_name=league_name, country="England")
            db.add(db_league)
            db.flush() # Получаем ID лиги для команд

        # 2. СОЗДАЕМ КОМАНДЫ (Колонка 'Club')
        unique_clubs = df['Club'].unique()
        team_map = {}
        
        print(f">>> Обработка клубов ({len(unique_clubs)} шт.)...")
        for c_name in unique_clubs:
            db_team = db.query(Team).filter_by(team_name=c_name).first()
            if not db_team:
                db_team = Team(team_name=c_name, league_id=db_league.league_id)
                db.add(db_team)
                db.flush()
            team_map[c_name] = db_team.team_id

        # 3. СОЗДАЕМ ИГРОКОВ (Колонки 'Name', 'Club', 'Position')
        print(">>> Регистрация игроков...")
        new_players_count = 0
        
        for _, row in df.iterrows():
            p_name = row['Name']
            club_name = row['Club']
            raw_pos = str(row['Position'])

            # Маппинг позиций под твой формат (GK, DF, MF, FW)
            if "Goalkeeper" in raw_pos:
                p_pos = "GK"
            elif "Defender" in raw_pos:
                p_pos = "DF"
            elif "Midfielder" in raw_pos:
                p_pos = "MF"
            elif "Forward" in raw_pos:
                p_pos = "FW"
            else:
                p_pos = "MF" # Заглушка по умолчанию

            # Берем ID команды из нашего маппинга
            t_id = team_map.get(club_name)
            
            if t_id:
                # Проверяем, нет ли уже такого игрока в этом клубе
                exists = db.query(Player).filter_by(player_name=p_name, team_id=t_id).first()
                if not exists:
                    db.add(Player(
                        player_name=p_name,
                        team_id=t_id,
                        position=p_pos
                    ))
                    new_players_count += 1
        
        db.commit()
        print(f" УСПЕХ: База готова. Добавлено {len(team_map)} клубов и {new_players_count} игроков.")

    except Exception as e:
        db.rollback()
        print(f"[ОШИБКА]: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fill_base_from_kaggle()