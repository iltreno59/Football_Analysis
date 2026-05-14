"""
Создание пользователя в БД: логин, пароль, команда, роль (admin | coach).

Роли (поле user.user_role):
  admin  — администратор: в приложении может менять состав своей команды (игроков).
  coach  — тренер: создаёт отчёты; смотрит свои и коллег по team_id; удаляет только свои.

Обе роли: просмотр лиг, клубов, игроков, ролей — задаётся в API (не в БД).

Использование (из корня репозитория Football_Analysis):
  python -m app.scripts.create_user --login ivan --password secret --team "Manchester City" --role coach
  python -m app.scripts.create_user ... --role admin --create-team --league-id 1

Требуется: pip install bcrypt python-dotenv sqlalchemy psycopg2-binary
Переменные окружения: как в app/core/db_conn.py (.env).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.db_conn import SessionLocal
from app.models import User, Team, League


def _hash_password(plain: str) -> str:
    try:
        import bcrypt
    except ImportError as e:
        raise SystemExit(
            "Установите bcrypt: pip install bcrypt"
        ) from e
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "utf-8"
    )


def _normalize_role(raw: str) -> str:
    r = raw.strip().lower()
    aliases = {
        "admin": "admin",
        "administrator": "admin",
        "администратор": "admin",
        "coach": "coach",
        "trainer": "coach",
        "тренер": "coach",
    }
    if r not in aliases:
        raise SystemExit(
            f"Неизвестная роль «{raw}». Допустимо: admin, coach "
            "(или: администратор, тренер)"
        )
    return aliases[r]


def main() -> None:
    p = argparse.ArgumentParser(description="Создать пользователя в БД")
    p.add_argument("--login", required=True, help="Уникальный логин")
    p.add_argument("--password", required=True, help="Пароль (будет сохранён как bcrypt-хеш)")
    p.add_argument("--team", required=True, dest="team_name", help="Название команды")
    p.add_argument(
        "--role",
        required=True,
        help="admin | coach (или: администратор | тренер)",
    )
    p.add_argument(
        "--create-team",
        action="store_true",
        help="Создать команду, если с таким названием нет записи",
    )
    p.add_argument(
        "--league-id",
        type=int,
        default=None,
        help="Лига для новой команды (если не указана — первая лига по league_id)",
    )
    args = p.parse_args()

    role = _normalize_role(args.role)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.user_login == args.login).first():
            raise SystemExit(f"Пользователь с логином «{args.login}» уже существует")

        name = args.team_name.strip()
        team = db.query(Team).filter(Team.team_name.ilike(name)).first()

        if not team:
            if not args.create_team:
                raise SystemExit(
                    f"Команда «{args.team_name}» не найдена. "
                    "Укажите точное имя из БД или добавьте флаг --create-team"
                )
            league_id = args.league_id
            if league_id is None:
                first = db.query(League).order_by(League.league_id).first()
                if not first:
                    raise SystemExit("В БД нет лиг — нельзя создать команду без league_id")
                league_id = first.league_id
            else:
                if not db.query(League).filter(League.league_id == league_id).first():
                    raise SystemExit(f"Лига league_id={league_id} не найдена")

            team = Team(team_name=args.team_name.strip(), league_id=league_id)
            db.add(team)
            db.flush()

        user = User(
            user_login=args.login.strip(),
            hashed_password=_hash_password(args.password),
            user_role=role,
            team_id=team.team_id,
        )
        db.add(user)
        db.commit()
        print(
            f"OK: user_id={user.user_id} login={user.user_login!r} "
            f"role={user.user_role!r} team_id={team.team_id} ({team.team_name!r})"
        )
    except SystemExit:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
