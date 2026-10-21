"""Tablas base del paso 1: usuario, cliente, contribuyente, asignacion, impuesto, estado y auditoria.

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

AREAS = "('impuestos','secretaria','laboral','contabilidad_auditoria')"
ROLES = "('admin_socio','responsable_area','empleado_impuestos','secretaria')"


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("correo", sa.String(254), nullable=False),
        sa.Column("hash_contrasena", sa.String(255), nullable=False),
        sa.Column("area", sa.String(40), nullable=False),
        sa.Column("rol", sa.String(40), nullable=False),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("intentos_fallidos", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True)),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(f"area IN {AREAS}", name="ck_usuario_area"),
        sa.CheckConstraint(f"rol IN {ROLES}", name="ck_usuario_rol"),
    )
    op.execute("CREATE UNIQUE INDEX uq_usuario_correo ON usuario (lower(correo))")

    op.create_table(
        "cliente",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("area", sa.String(40), nullable=False),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(f"area IN {AREAS}", name="ck_cliente_area"),
    )

    op.create_table(
        "contribuyente",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cuit", sa.String(11), nullable=False, unique=True),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("condicion", sa.String(30), nullable=False),
        sa.Column("cliente_id", sa.Integer, sa.ForeignKey("cliente.id"), nullable=False),
        sa.CheckConstraint("cuit ~ '^[0-9]{11}$'", name="ck_contribuyente_cuit"),
        sa.CheckConstraint("tipo IN ('humana','juridica')", name="ck_contribuyente_tipo"),
        sa.CheckConstraint(
            "condicion IN ('responsable_inscripto','monotributista','otro')",
            name="ck_contribuyente_condicion",
        ),
    )
    op.create_index("ix_contribuyente_cliente", "contribuyente", ["cliente_id"])

    op.create_table(
        "asignacion",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cliente_id", sa.Integer, sa.ForeignKey("cliente.id"), nullable=False),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_fin", sa.DateTime(timezone=True)),
        sa.CheckConstraint("fecha_fin IS NULL OR fecha_fin >= fecha_inicio", name="ck_asignacion_fechas"),
    )
    op.create_index("ix_asignacion_usuario", "asignacion", ["usuario_id"])
    # Un cliente tiene un solo responsable actual: la fila sin fecha de fin.
    op.execute("CREATE UNIQUE INDEX uq_asignacion_actual ON asignacion (cliente_id) WHERE fecha_fin IS NULL")

    op.create_table(
        "impuesto",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nombre", sa.String(80), nullable=False, unique=True),
        sa.Column("orden", sa.Integer, nullable=False, server_default=sa.text("0")),
    )

    op.create_table(
        "estado",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("impuesto_id", sa.Integer, sa.ForeignKey("impuesto.id"), nullable=False),
        sa.Column("nombre", sa.String(80), nullable=False),
        sa.Column("orden", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("color", sa.String(20), nullable=False),
        sa.UniqueConstraint("impuesto_id", "nombre", name="uq_estado_impuesto_nombre"),
        sa.CheckConstraint("color IN ('correcto','atencion','error','neutro')", name="ck_estado_color"),
    )

    op.create_table(
        "auditoria",
        sa.Column("id", sa.BigInteger, sa.Identity(always=False), primary_key=True),
        sa.Column("usuario_id", sa.Integer),
        sa.Column("accion", sa.String(60), nullable=False),
        sa.Column("entidad", sa.String(40)),
        sa.Column("entidad_id", sa.Integer),
        sa.Column("cliente_id", sa.Integer),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detalle", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("hash_anterior", sa.String(64), nullable=False),
        sa.Column("hash_propio", sa.String(64), nullable=False, unique=True),
    )
    op.create_index("ix_auditoria_cliente", "auditoria", ["cliente_id"])
    op.create_index("ix_auditoria_usuario", "auditoria", ["usuario_id"])


def downgrade() -> None:
    for tabla in ("auditoria", "estado", "impuesto", "asignacion", "contribuyente", "cliente", "usuario"):
        op.drop_table(tabla)
