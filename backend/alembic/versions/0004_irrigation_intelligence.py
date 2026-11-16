"""irrigation intelligence tables

Adds the irrigation event/schedule/prediction tables, the per-field
application settings, the farmer preference row, and additive
``weather_records`` columns used by the water-balance calculation.

Existing tables are only extended with nullable columns; no existing row is
rewritten or dropped.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-16 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    # --- additive weather columns (nullable, existing rows untouched) ---
    op.add_column("weather_records", sa.Column("temperature_min", sa.Float(), nullable=True))
    op.add_column("weather_records", sa.Column("temperature_max", sa.Float(), nullable=True))
    op.add_column("weather_records", sa.Column("et0_mm", sa.Float(), nullable=True))

    op.create_table(
        "irrigation_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Float(), nullable=True),
        sa.Column("water_volume_litres", sa.Float(), nullable=True),
        sa.Column("application_method", sa.String(), nullable=True),
        sa.Column("water_source", sa.String(), nullable=True),
        sa.Column("recorded_by", sa.String(), server_default="manual", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "water_volume_litres IS NULL OR water_volume_litres >= 0",
            name="chk_irrigation_event_volume",
        ),
        sa.CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes >= 0",
            name="chk_irrigation_event_duration",
        ),
        sa.CheckConstraint(
            "end_time IS NULL OR end_time >= start_time",
            name="chk_irrigation_event_window",
        ),
    )
    op.create_index(op.f("ix_irrigation_events_id"), "irrigation_events", ["id"], unique=False)
    op.create_index(op.f("ix_irrigation_events_user_id"), "irrigation_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_irrigation_events_field_id"), "irrigation_events", ["field_id"], unique=False)
    op.create_index(op.f("ix_irrigation_events_start_time"), "irrigation_events", ["start_time"], unique=False)
    op.create_index(
        "ix_irrigation_events_user_start", "irrigation_events", ["user_id", "start_time"], unique=False
    )
    op.create_index(
        "ix_irrigation_events_field_start", "irrigation_events", ["field_id", "start_time"], unique=False
    )

    op.create_table(
        "irrigation_predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("predicted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("target_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_moisture", sa.Float(), nullable=True),
        sa.Column("predicted_moisture", sa.Float(), nullable=True),
        sa.Column("moisture_trend", sa.Float(), nullable=True),
        sa.Column("irrigation_requirement_mm", sa.Float(), nullable=True),
        sa.Column("estimated_volume_litres", sa.Float(), nullable=True),
        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("model_version", sa.String(), nullable=True),
        sa.Column("calculation_version", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("uncertainty", sa.Float(), nullable=True),
        sa.Column("status", sa.String(), server_default="provisional", nullable=False),
        sa.Column("data_freshness", sa.String(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("input_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="chk_prediction_confidence",
        ),
    )
    op.create_index(op.f("ix_irrigation_predictions_id"), "irrigation_predictions", ["id"], unique=False)
    op.create_index(op.f("ix_irrigation_predictions_user_id"), "irrigation_predictions", ["user_id"], unique=False)
    op.create_index(op.f("ix_irrigation_predictions_field_id"), "irrigation_predictions", ["field_id"], unique=False)
    op.create_index(op.f("ix_irrigation_predictions_predicted_at"), "irrigation_predictions", ["predicted_at"], unique=False)
    op.create_index(
        "ix_irrigation_predictions_field_predicted",
        "irrigation_predictions",
        ["field_id", "predicted_at"],
        unique=False,
    )

    op.create_table(
        "irrigation_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("recommended_start_time", sa.Time(), nullable=True),
        sa.Column("recommended_window_end", sa.Time(), nullable=True),
        sa.Column("estimated_volume_litres", sa.Float(), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Float(), nullable=True),
        sa.Column("estimated_depth_mm", sa.Float(), nullable=True),
        sa.Column("priority", sa.String(), server_default="medium", nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("reason_code", sa.String(), nullable=True),
        sa.Column("model_version", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("uncertainty_litres", sa.Float(), nullable=True),
        sa.Column("status", sa.String(), server_default="pending", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_volume_litres", sa.Float(), nullable=True),
        sa.Column("actual_duration_minutes", sa.Float(), nullable=True),
        sa.Column("actual_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("prediction_id", sa.Integer(), nullable=True),
        sa.Column("input_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["prediction_id"], ["irrigation_predictions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("field_id", "scheduled_date", name="uq_irrigation_schedule_field_date"),
        sa.CheckConstraint(
            "estimated_volume_litres IS NULL OR estimated_volume_litres >= 0",
            name="chk_schedule_estimated_volume",
        ),
        sa.CheckConstraint(
            "actual_volume_litres IS NULL OR actual_volume_litres >= 0",
            name="chk_schedule_actual_volume",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="chk_schedule_confidence",
        ),
    )
    op.create_index(op.f("ix_irrigation_schedules_id"), "irrigation_schedules", ["id"], unique=False)
    op.create_index(op.f("ix_irrigation_schedules_user_id"), "irrigation_schedules", ["user_id"], unique=False)
    op.create_index(op.f("ix_irrigation_schedules_field_id"), "irrigation_schedules", ["field_id"], unique=False)
    op.create_index(op.f("ix_irrigation_schedules_scheduled_date"), "irrigation_schedules", ["scheduled_date"], unique=False)
    op.create_index(
        "ix_irrigation_schedules_user_date", "irrigation_schedules", ["user_id", "scheduled_date"], unique=False
    )

    op.create_table(
        "field_irrigation_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("application_method", sa.String(), nullable=True),
        sa.Column("application_rate_litres_per_hour", sa.Float(), nullable=True),
        sa.Column("application_efficiency", sa.Float(), nullable=True),
        sa.Column("water_source", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("field_id", name="uq_field_irrigation_settings_field"),
        sa.CheckConstraint(
            "application_efficiency IS NULL OR (application_efficiency > 0 AND application_efficiency <= 1)",
            name="chk_field_irrigation_efficiency",
        ),
        sa.CheckConstraint(
            "application_rate_litres_per_hour IS NULL OR application_rate_litres_per_hour > 0",
            name="chk_field_irrigation_rate",
        ),
    )
    op.create_index(op.f("ix_field_irrigation_settings_id"), "field_irrigation_settings", ["id"], unique=False)
    op.create_index(op.f("ix_field_irrigation_settings_field_id"), "field_irrigation_settings", ["field_id"], unique=False)

    op.create_table(
        "farmer_irrigation_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("preferred_start_time", sa.Time(), nullable=True),
        sa.Column("preferred_end_time", sa.Time(), nullable=True),
        sa.Column("max_daily_volume_litres", sa.Float(), nullable=True),
        sa.Column("irrigation_days", sa.String(), server_default="all", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_farmer_irrigation_preferences_user"),
        sa.CheckConstraint(
            "max_daily_volume_litres IS NULL OR max_daily_volume_litres >= 0",
            name="chk_farmer_irrigation_cap",
        ),
    )
    op.create_index(op.f("ix_farmer_irrigation_preferences_id"), "farmer_irrigation_preferences", ["id"], unique=False)
    op.create_index(op.f("ix_farmer_irrigation_preferences_user_id"), "farmer_irrigation_preferences", ["user_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_farmer_irrigation_preferences_user_id"), table_name="farmer_irrigation_preferences")
    op.drop_index(op.f("ix_farmer_irrigation_preferences_id"), table_name="farmer_irrigation_preferences")
    op.drop_table("farmer_irrigation_preferences")

    op.drop_index(op.f("ix_field_irrigation_settings_field_id"), table_name="field_irrigation_settings")
    op.drop_index(op.f("ix_field_irrigation_settings_id"), table_name="field_irrigation_settings")
    op.drop_table("field_irrigation_settings")

    op.drop_index("ix_irrigation_schedules_user_date", table_name="irrigation_schedules")
    op.drop_index(op.f("ix_irrigation_schedules_scheduled_date"), table_name="irrigation_schedules")
    op.drop_index(op.f("ix_irrigation_schedules_field_id"), table_name="irrigation_schedules")
    op.drop_index(op.f("ix_irrigation_schedules_user_id"), table_name="irrigation_schedules")
    op.drop_index(op.f("ix_irrigation_schedules_id"), table_name="irrigation_schedules")
    op.drop_table("irrigation_schedules")

    op.drop_index("ix_irrigation_predictions_field_predicted", table_name="irrigation_predictions")
    op.drop_index(op.f("ix_irrigation_predictions_predicted_at"), table_name="irrigation_predictions")
    op.drop_index(op.f("ix_irrigation_predictions_field_id"), table_name="irrigation_predictions")
    op.drop_index(op.f("ix_irrigation_predictions_user_id"), table_name="irrigation_predictions")
    op.drop_index(op.f("ix_irrigation_predictions_id"), table_name="irrigation_predictions")
    op.drop_table("irrigation_predictions")

    op.drop_index("ix_irrigation_events_field_start", table_name="irrigation_events")
    op.drop_index("ix_irrigation_events_user_start", table_name="irrigation_events")
    op.drop_index(op.f("ix_irrigation_events_start_time"), table_name="irrigation_events")
    op.drop_index(op.f("ix_irrigation_events_field_id"), table_name="irrigation_events")
    op.drop_index(op.f("ix_irrigation_events_user_id"), table_name="irrigation_events")
    op.drop_index(op.f("ix_irrigation_events_id"), table_name="irrigation_events")
    op.drop_table("irrigation_events")

    op.drop_column("weather_records", "et0_mm")
    op.drop_column("weather_records", "temperature_max")
    op.drop_column("weather_records", "temperature_min")
