"""Rol de la aplicación con permisos mínimos y auditoría de solo inserción.

- Crea el rol ks_app (la aplicación se conecta con él, nunca con el dueño de las tablas).
- ks_app solo puede INSERT y SELECT sobre auditoria.
- Un trigger bloquea UPDATE, DELETE y TRUNCATE sobre auditoria, incluso para el dueño.

REGLA PARA MIGRACIONES FUTURAS: cada tabla nueva necesita su GRANT explícito a ks_app.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

from app.config import get_settings

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    clave = get_settings().app_db_password.replace("'", "''")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ks_app') THEN
                CREATE ROLE ks_app LOGIN;
            END IF;
        END $$;
        """
    )
    op.execute(f"ALTER ROLE ks_app WITH LOGIN PASSWORD '{clave}'")
    op.execute(
        """
        DO $$
        BEGIN
            EXECUTE format('GRANT CONNECT ON DATABASE %I TO ks_app', current_database());
        END $$;
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public TO ks_app")

    # Permisos mínimos por tabla (el usuario se da de baja, no se borra).
    op.execute("GRANT SELECT, INSERT, UPDATE ON usuario, cliente, contribuyente, asignacion TO ks_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON impuesto, estado TO ks_app")
    op.execute("GRANT SELECT, INSERT ON auditoria TO ks_app")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ks_app")

    op.execute(
        """
        CREATE FUNCTION auditoria_solo_insercion() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'La tabla auditoria es de solo insercion: no se puede modificar ni borrar'
                USING ERRCODE = 'insufficient_privilege';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER auditoria_no_modificar
        BEFORE UPDATE OR DELETE ON auditoria
        FOR EACH ROW EXECUTE FUNCTION auditoria_solo_insercion();
        """
    )
    op.execute(
        """
        CREATE TRIGGER auditoria_no_truncar
        BEFORE TRUNCATE ON auditoria
        FOR EACH STATEMENT EXECUTE FUNCTION auditoria_solo_insercion();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS auditoria_no_truncar ON auditoria")
    op.execute("DROP TRIGGER IF EXISTS auditoria_no_modificar ON auditoria")
    op.execute("DROP FUNCTION IF EXISTS auditoria_solo_insercion()")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ks_app")
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM ks_app")
