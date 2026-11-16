"""supabase auth + profiles + alerts + reading provenance

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-03 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    # Add idempotency_key index (column already exists from 0001)
    op.create_index(op.f("ix_sensor_readings_idempotency_key"), "sensor_readings", ["idempotency_key"], unique=True)

    # Create alerts table
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=True),
        sa.Column("alert_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("message_key", sa.String(), nullable=False),
        sa.Column("trigger_value", sa.Float(), nullable=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_user_id"), "alerts", ["user_id"], unique=False)
    op.create_index(op.f("ix_alerts_field_id"), "alerts", ["field_id"], unique=False)
    op.create_index(op.f("ix_alerts_triggered_at"), "alerts", ["triggered_at"], unique=False)

    # Update fields.user_id FK to reference profiles instead of users
    op.create_foreign_key(
        "fields_user_id_fkey", "fields", "profiles",
        ["user_id"], ["id"], ondelete="CASCADE"
    )


def downgrade():
    # Drop alerts table
    op.drop_index(op.f("ix_alerts_triggered_at"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_field_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_user_id"), table_name="alerts")
    op.drop_table("alerts")

    # Remove forecast_for and provider from weather_records (added in 0003, but actually in 0001 - no-op in downgrade)

    # Remove idempotency_key index from sensor_readings
    op.drop_index(op.f("ix_sensor_readings_idempotency_key"), table_name="sensor_readings")

    # Drop fields FK to profiles
    op.drop_constraint("fields_user_id_fkey", "fields", type_="foreignkey")
