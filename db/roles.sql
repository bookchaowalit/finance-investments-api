-- Roles for the investments database. Locally a superuser runs this; on Neon
-- `investments-db provision` creates the same roles through the migrator.
--
-- investments_migrator  owns the schema and runs migrations only.
-- investments_api       the API at runtime: no superuser, no BYPASSRLS, owns nothing.
-- investments_publisher sweeps and marks the outbox across workspaces; nothing else.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'investments_migrator') THEN
        CREATE ROLE investments_migrator LOGIN NOSUPERUSER NOCREATEROLE NOBYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'investments_api') THEN
        CREATE ROLE investments_api LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'investments_publisher') THEN
        CREATE ROLE investments_publisher LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
END
$$;
