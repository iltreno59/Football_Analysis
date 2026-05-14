-- Функция для входа под ролью football_app при включённом RLS на "user".
-- Обычный SELECT по логину без set_config не видит строки (политика same_team).
-- SECURITY DEFINER выполняется от имени владельца функции (суперпользователь / владелец схемы)
-- и обходит RLS для чтения одной строки по логину.
--
-- Выполнить от суперпользователя после rls_and_roles.sql.

CREATE OR REPLACE FUNCTION public.lookup_user_for_login(p_login text)
RETURNS TABLE (
    user_id integer,
    user_login text,
    hashed_password character varying,
    user_role text,
    team_id integer
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $func$
  SELECT
    u.user_id,
    u.user_login::text,
    u.hashed_password::character varying(255),
    u.user_role::text,
    u.team_id
  FROM "user" u
  WHERE u.user_login = p_login
  LIMIT 1;
$func$;

REVOKE ALL ON FUNCTION public.lookup_user_for_login(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.lookup_user_for_login(text) TO football_app;

COMMENT ON FUNCTION public.lookup_user_for_login(text) IS
  'Возвращает данные пользователя по логину для проверки пароля при RLS на таблице "user".';
