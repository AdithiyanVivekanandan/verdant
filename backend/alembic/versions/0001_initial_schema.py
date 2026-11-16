"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("supabase_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("preferred_language", sa.String(), server_default="en", nullable=False),
        sa.Column("theme_preference", sa.String(), server_default="system", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supabase_user_id", name="uq_profile_supabase_user_id"),
        sa.UniqueConstraint("email", name="uq_profile_email"),
    )
    op.create_index(op.f("ix_profiles_email"), "profiles", ["email"], unique=False)
    op.create_index(op.f("ix_profiles_supabase_user_id"), "profiles", ["supabase_user_id"], unique=False)

    op.create_table(
        "fields",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(), nullable=False),
        sa.Column("farmer_name", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("village", sa.String(), nullable=True),
        sa.Column("district", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("area_acres", sa.Float(), nullable=False),
        sa.Column("crop_type", sa.String(), nullable=False),
        sa.Column("soil_type", sa.String(), nullable=False),
        sa.Column("growth_stage", sa.String(), nullable=False),
        sa.Column("sowing_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fields_id"), "fields", ["id"], unique=False)
    op.create_index(op.f("ix_fields_user_id"), "fields", ["user_id"], unique=False)

    op.create_table(
        "sensors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("sensor_identifier", sa.String(), nullable=False),
        sa.Column("sensor_type", sa.String(), nullable=False),
        sa.Column("installation_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("field_id", "sensor_identifier", name="uq_field_sensor_identifier"),
    )
    op.create_index(op.f("ix_sensors_id"), "sensors", ["id"], unique=False)
    op.create_index(op.f("ix_sensors_field_id"), "sensors", ["field_id"], unique=False)
    op.create_index(op.f("ix_sensors_sensor_identifier"), "sensors", ["sensor_identifier"], unique=False)

    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("sensor_id", sa.Integer(), nullable=True),
        sa.Column("moisture_percentage", sa.Float(), nullable=False),
        sa.Column("soil_temperature", sa.Float(), nullable=True),
        sa.Column("growth_stage", sa.String(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("source", sa.String(), server_default="manual", nullable=False),
        sa.Column("validation_status", sa.String(), server_default="valid", nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "moisture_percentage >= 0 AND moisture_percentage <= 100",
            name="chk_moisture_range",
        ),
    )
    op.create_index(op.f("ix_sensor_readings_field_recorded"), "sensor_readings", ["field_id", "recorded_at"], unique=False)
    op.create_index(op.f("ix_sensor_readings_id"), "sensor_readings", ["id"], unique=False)
    op.create_index(op.f("ix_sensor_readings_recorded_at"), "sensor_readings", ["recorded_at"], unique=False)
    op.create_index(op.f("ix_sensor_readings_sensor_id"), "sensor_readings", ["sensor_id"], unique=False)

    op.create_table(
        "weather_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("humidity", sa.Float(), nullable=False),
        sa.Column("rainfall_probability", sa.Float(), nullable=True),
        sa.Column("rainfall", sa.Float(), nullable=True),
        sa.Column("wind_speed", sa.Float(), nullable=False),
        sa.Column("provider", sa.String(), server_default="demo", nullable=False),
        sa.Column("forecast_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_weather_records_field_id"), "weather_records", ["field_id"], unique=False)
    op.create_index(op.f("ix_weather_records_id"), "weather_records", ["id"], unique=False)
    op.create_index(op.f("ix_weather_records_recorded_at"), "weather_records", ["recorded_at"], unique=False)


def downgrade():
    op.drop_table("weather_records")
    op.drop_table("sensor_readings")
    op.drop_table("sensors")
    op.drop_table("fields")
    op.drop_table("profiles")
