-- После применения этого файла выполните также (для входа API под football_app):
--   app/scripts/rls_lookup_user_for_login.sql
--
-- =============================================================================
-- Роли PostgreSQL, права и Row Level Security для Football_Analysis
--
-- Выполнять от суперпользователя или роли с правом CREATE ROLE / владельца БД.
-- Перед продакшеном:
--   1) Замените пароль для football_app.
--   2) Убедитесь, что владелец таблиц — НЕ football_app (иначе владелец обходит
--      RLS). Ниже — вариант с ролью football_owner.
--   3) Приложение в начале каждой транзакции/запроса должно выставлять контекст:
--        SELECT set_config('app.user_id', '<id>', true);
--        SELECT set_config('app.team_id', '<id>', true);
--        SELECT set_config('app.app_role', 'coach', true);  -- или 'admin'
--      Третий аргумент true = LOCAL для текущей транзакции (аналог SET LOCAL).
--
-- Значения app.app_role: 'coach' | 'admin' (как в user.user_role в приложении).
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. Служебные роли
-- -----------------------------------------------------------------------------

CREATE ROLE football_owner NOLOGIN;
COMMENT ON ROLE football_owner IS 'Владелец объектов схемы; не используется приложением.';

CREATE ROLE football_app LOGIN PASSWORD 'CHANGE_ME_STRONG_PASSWORD';
COMMENT ON ROLE football_app IS 'Роль пула соединений приложения; RLS применяется к ней.';

-- Опционально: только чтение (дашборды, BI)
-- CREATE ROLE football_readonly LOGIN PASSWORD 'CHANGE_ME_TOO';
-- GRANT football_readonly TO postgres; -- не делайте так в проде; выдайте только нужные GRANT


-- -----------------------------------------------------------------------------
-- 2. Владение объектами (один раз, после миграций Alembic)
--    Замените <schema> при необходимости (обычно public).
--    Если таблицы уже принадлежат football_owner — шаг пропустите.
-- -----------------------------------------------------------------------------

-- ALTER SCHEMA public OWNER TO football_owner;
-- ALTER TABLE league              OWNER TO football_owner;
-- ALTER TABLE team                OWNER TO football_owner;
-- ALTER TABLE "user"              OWNER TO football_owner;
-- ALTER TABLE player              OWNER TO football_owner;
-- ALTER TABLE metric              OWNER TO football_owner;
-- ALTER TABLE season_metric       OWNER TO football_owner;
-- ALTER TABLE roles               OWNER TO football_owner;
-- ALTER TABLE cluster_analysis    OWNER TO football_owner;
-- ALTER TABLE benchmark           OWNER TO football_owner;
-- ALTER TABLE exercise            OWNER TO football_owner;
-- ALTER TABLE exercise_for_metric OWNER TO football_owner;
-- ALTER TABLE report              OWNER TO football_owner;
-- ALTER TABLE exercise_in_report  OWNER TO football_owner;
-- ... все SEQUENCE, принадлежащие этим таблицам:
-- ALTER SEQUENCE ... OWNER TO football_owner;


-- -----------------------------------------------------------------------------
-- 3. Базовые права для приложения (без наследования прав владельца)
-- -----------------------------------------------------------------------------

-- Имя БД подставьте своё (как в .env DB_NAME):
-- GRANT CONNECT ON DATABASE football_analysis TO football_app;
GRANT USAGE ON SCHEMA public TO football_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO football_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO football_app;

-- Выдайте default privileges той роли, которая реально создаёт таблицы при миграциях
-- (часто postgres, а не football_owner):
ALTER DEFAULT PRIVILEGES FOR ROLE football_owner IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO football_app;
ALTER DEFAULT PRIVILEGES FOR ROLE football_owner IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO football_app;
-- ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ... (при необходимости)

-- Приложение не должно править справочники напрямую — отзываем лишнее (RLS всё
-- равно ограничит; REVOKE усиливает «явный минимум прав»).
REVOKE INSERT, UPDATE, DELETE ON TABLE league FROM football_app;
REVOKE INSERT, UPDATE, DELETE ON TABLE roles FROM football_app;
REVOKE INSERT, UPDATE, DELETE ON TABLE metric FROM football_app;
REVOKE INSERT, UPDATE, DELETE ON TABLE benchmark FROM football_app;
REVOKE INSERT, UPDATE, DELETE ON TABLE season_metric FROM football_app;
REVOKE INSERT, UPDATE, DELETE ON TABLE cluster_analysis FROM football_app;
REVOKE INSERT, UPDATE, DELETE ON TABLE exercise FROM football_app;
REVOKE INSERT, UPDATE, DELETE ON TABLE exercise_for_metric FROM football_app;

-- Команда/игроки: INSERT игроков — только офлайн/миграции; приложение — чтение
-- + UPDATE player для admin (RLS ниже). Coach — без UPDATE (только RLS).
REVOKE INSERT, DELETE ON TABLE player FROM football_app;

-- Пользователи приложения создаются скриптом/админом БД, не пулом API
REVOKE INSERT, UPDATE, DELETE ON TABLE "user" FROM football_app;

-- team: изменение состава идёт через player.team_id; прямой UPDATE team не нужен
REVOKE INSERT, UPDATE, DELETE ON TABLE team FROM football_app;


-- -----------------------------------------------------------------------------
-- 4. Вспомогательные выражения (документация; в политиках дублируем явно)
-- -----------------------------------------------------------------------------
-- app_user_id()   := NULLIF(current_setting('app.user_id', true), '')::int
-- app_team_id()   := NULLIF(current_setting('app.team_id', true), '')::int
-- app_role()      := lower(nullif(trim(current_setting('app.app_role', true)), ''))


-- =============================================================================
-- 5. ROW LEVEL SECURITY и политики
-- =============================================================================

-- ----- Справочники и аналитика: только чтение для football_app -----
ALTER TABLE league ENABLE ROW LEVEL SECURITY;
ALTER TABLE league FORCE ROW LEVEL SECURITY;
CREATE POLICY league_select_all
  ON league FOR SELECT
  TO football_app
  USING (true);

ALTER TABLE team ENABLE ROW LEVEL SECURITY;
ALTER TABLE team FORCE ROW LEVEL SECURITY;
CREATE POLICY team_select_all
  ON team FOR SELECT
  TO football_app
  USING (true);

ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles FORCE ROW LEVEL SECURITY;
CREATE POLICY roles_select_all
  ON roles FOR SELECT
  TO football_app
  USING (true);

ALTER TABLE metric ENABLE ROW LEVEL SECURITY;
ALTER TABLE metric FORCE ROW LEVEL SECURITY;
CREATE POLICY metric_select_all
  ON metric FOR SELECT
  TO football_app
  USING (true);

ALTER TABLE benchmark ENABLE ROW LEVEL SECURITY;
ALTER TABLE benchmark FORCE ROW LEVEL SECURITY;
CREATE POLICY benchmark_select_all
  ON benchmark FOR SELECT
  TO football_app
  USING (true);

ALTER TABLE season_metric ENABLE ROW LEVEL SECURITY;
ALTER TABLE season_metric FORCE ROW LEVEL SECURITY;
CREATE POLICY season_metric_select_all
  ON season_metric FOR SELECT
  TO football_app
  USING (true);

ALTER TABLE cluster_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE cluster_analysis FORCE ROW LEVEL SECURITY;
CREATE POLICY cluster_analysis_select_all
  ON cluster_analysis FOR SELECT
  TO football_app
  USING (true);

ALTER TABLE exercise ENABLE ROW LEVEL SECURITY;
ALTER TABLE exercise FORCE ROW LEVEL SECURITY;
CREATE POLICY exercise_select_all
  ON exercise FOR SELECT
  TO football_app
  USING (true);

ALTER TABLE exercise_for_metric ENABLE ROW LEVEL SECURITY;
ALTER TABLE exercise_for_metric FORCE ROW LEVEL SECURITY;
CREATE POLICY exercise_for_metric_select_all
  ON exercise_for_metric FOR SELECT
  TO football_app
  USING (true);


-- ----- Игроки: все видят; UPDATE только admin; итог — игрок в команде admin -----
ALTER TABLE player ENABLE ROW LEVEL SECURITY;
ALTER TABLE player FORCE ROW LEVEL SECURITY;

CREATE POLICY player_select_all
  ON player FOR SELECT
  TO football_app
  USING (true);

CREATE POLICY player_update_admin_assign_to_own_team
  ON player FOR UPDATE
  TO football_app
  USING (
    lower(nullif(trim(current_setting('app.app_role', true)), '')) = 'admin'
    AND current_setting('app.team_id', true) IS NOT NULL
    AND btrim(current_setting('app.team_id', true)) <> ''
  )
  WITH CHECK (
    team_id = NULLIF(current_setting('app.team_id', true), '')::integer
  );

-- Ограничение: после UPDATE игрок обязан оказаться в team_id администратора
-- (перевод «из чужой команды в свою» разрешён; вывод из состава в другую команду
-- этой политикой не покрыт — добавьте вторую политику при необходимости).

-- Coach не получает политики UPDATE → изменение состава только у admin.


-- ----- Учётные записи приложения: видят коллег по team_id (и себя) -----
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "user" FORCE ROW LEVEL SECURITY;

CREATE POLICY app_user_select_same_team
  ON "user" FOR SELECT
  TO football_app
  USING (
    current_setting('app.team_id', true) IS NOT NULL
    AND btrim(current_setting('app.team_id', true)) <> ''
    AND team_id = NULLIF(current_setting('app.team_id', true), '')::integer
  );


-- ----- Отчёты: чтение — своя команда; вставка — только от своего user_id;
--       удаление — только автор; обновление — только автор (опционально) -----
ALTER TABLE report ENABLE ROW LEVEL SECURITY;
ALTER TABLE report FORCE ROW LEVEL SECURITY;

CREATE POLICY report_select_same_team_authors
  ON report FOR SELECT
  TO football_app
  USING (
    current_setting('app.team_id', true) IS NOT NULL
    AND btrim(current_setting('app.team_id', true)) <> ''
    AND EXISTS (
      SELECT 1
      FROM "user" u
      WHERE u.user_id = report.user_id
        AND u.team_id = NULLIF(current_setting('app.team_id', true), '')::integer
    )
  );

CREATE POLICY report_insert_self_user
  ON report FOR INSERT
  TO football_app
  WITH CHECK (
    user_id = NULLIF(current_setting('app.user_id', true), '')::integer
    AND EXISTS (
      SELECT 1
      FROM "user" u
      WHERE u.user_id = NULLIF(current_setting('app.user_id', true), '')::integer
        AND u.team_id = NULLIF(current_setting('app.team_id', true), '')::integer
    )
  );

CREATE POLICY report_delete_own
  ON report FOR DELETE
  TO football_app
  USING (
    user_id = NULLIF(current_setting('app.user_id', true), '')::integer
  );

CREATE POLICY report_update_own
  ON report FOR UPDATE
  TO football_app
  USING (
    user_id = NULLIF(current_setting('app.user_id', true), '')::integer
  )
  WITH CHECK (
    user_id = NULLIF(current_setting('app.user_id', true), '')::integer
  );


-- ----- Строки отчёта: как у отчёта (автор/команда) -----
ALTER TABLE exercise_in_report ENABLE ROW LEVEL SECURITY;
ALTER TABLE exercise_in_report FORCE ROW LEVEL SECURITY;

CREATE POLICY eir_select_via_report_team
  ON exercise_in_report FOR SELECT
  TO football_app
  USING (
    EXISTS (
      SELECT 1
      FROM report r
      JOIN "user" u ON u.user_id = r.user_id
      WHERE r.report_id = exercise_in_report.report_id
        AND current_setting('app.team_id', true) IS NOT NULL
        AND btrim(current_setting('app.team_id', true)) <> ''
        AND u.team_id = NULLIF(current_setting('app.team_id', true), '')::integer
    )
  );

CREATE POLICY eir_insert_own_report
  ON exercise_in_report FOR INSERT
  TO football_app
  WITH CHECK (
    EXISTS (
      SELECT 1
      FROM report r
      WHERE r.report_id = exercise_in_report.report_id
        AND r.user_id = NULLIF(current_setting('app.user_id', true), '')::integer
    )
  );

CREATE POLICY eir_delete_own_report
  ON exercise_in_report FOR DELETE
  TO football_app
  USING (
    EXISTS (
      SELECT 1
      FROM report r
      WHERE r.report_id = exercise_in_report.report_id
        AND r.user_id = NULLIF(current_setting('app.user_id', true), '')::integer
    )
  );

CREATE POLICY eir_update_own_report
  ON exercise_in_report FOR UPDATE
  TO football_app
  USING (
    EXISTS (
      SELECT 1
      FROM report r
      WHERE r.report_id = exercise_in_report.report_id
        AND r.user_id = NULLIF(current_setting('app.user_id', true), '')::integer
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1
      FROM report r
      WHERE r.report_id = exercise_in_report.report_id
        AND r.user_id = NULLIF(current_setting('app.user_id', true), '')::integer
    )
  );


-- =============================================================================
-- 6. Откат (вручную, при необходимости)
-- =============================================================================
/*
DROP POLICY IF EXISTS league_select_all ON league;
ALTER TABLE league NO FORCE ROW LEVEL SECURITY;
ALTER TABLE league DISABLE ROW LEVEL SECURITY;
-- ... аналогично для каждой таблицы и политики

DROP OWNED BY football_app;
DROP ROLE IF EXISTS football_app;
DROP ROLE IF EXISTS football_owner;
*/
