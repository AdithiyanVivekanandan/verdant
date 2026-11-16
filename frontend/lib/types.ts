export type Language = "en" | "hi" | "kn" | "ta"

export interface Profile {
  id: string
  supabase_user_id: string
  full_name: string
  email: string
  preferred_language: Language | string
  theme_preference: "light" | "dark" | "system" | string
  created_at: string
  updated_at: string
}

export interface Field {
  id: number
  user_id: string
  field_name: string
  farmer_name: string
  location: string
  village: string | null
  district: string | null
  state: string | null
  latitude: number | null
  longitude: number | null
  area_acres: number
  crop_type: string
  soil_type: string
  growth_stage: string
  sowing_date: string | null
  created_at: string
  updated_at: string
}

export type FieldStatus =
  | "healthy"
  | "needs_review"
  | "critical"
  | "stale"
  | "no_data"
  | "sensor_unavailable"

export type Freshness = "fresh" | "delayed" | "stale" | "missing"

export interface FieldSummary {
  id: number
  field_name: string
  crop_type: string
  area_acres: number
  latest_moisture: number | null
  moisture_condition: string
  last_updated: string | null
  has_sensor: boolean
  sensor_identifier: string | null
  sensor_id: number | null
  source: string | null
  validation_status: string | null
  ingested_at: string | null
  freshness: Freshness
  age_hours: number | null
  status: FieldStatus
  status_reason: string
  requires_attention: boolean
  threshold_low: number | null
  threshold_high: number | null
  crop_band: boolean
  soil_adjusted: boolean
}

export interface Sensor {
  id: number
  field_id: number
  sensor_identifier: string
  sensor_type: string
  installation_date: string | null
}

export interface Reading {
  id: number
  field_id: number
  sensor_id: number | null
  sensor_identifier: string | null
  field_name: string | null
  growth_stage: string
  moisture_percentage: number
  soil_temperature: number | null
  source: string
  recorded_at: string
  ingested_at: string
  validation_status: string
}

export interface DashboardSummary {
  total_fields: number
  average_moisture: number
  fields_requiring_attention: number
  fields_with_no_data: number
  latest_sensor_update: string | null
  status_counts: Record<string, number>
}

export interface Alert {
  field_id: number
  field_name: string
  type: string
  message: string
  severity: "info" | "warning" | "critical" | string
  moisture: number | null
  reason?: string | null
  action?: string | null
  freshness?: string | null
  last_updated?: string | null
  threshold_low?: number | null
  threshold_high?: number | null
}

export interface WeatherCurrent {
  field_id: number
  available: boolean
  source: "openweathermap" | "unavailable" | string
  reason: string
  message?: string
  temperature?: number | null
  conditions?: string | null
  humidity?: number | null
  rainfall_probability?: number | null
  rainfall?: number | null
  wind_speed?: number | null
  recorded_at?: string | null
  cached?: boolean
}

export interface WeatherForecastDay {
  date: string
  temperature: number
  min_temperature: number | null
  max_temperature: number | null
  conditions: string
  humidity: number
  rainfall_probability: number
  wind_speed: number
}

export interface WeatherForecast {
  field_id: number
  available: boolean
  source: string
  reason: string
  message?: string
  forecast: WeatherForecastDay[]
}

export interface Guidance {
  field_id: number
  field_name: string
  generated_at: string
  recommendation: string
  urgency: string
  headline: string
  explanation: string
  actions: string[]
  confidence: "high" | "medium" | "low" | string
  status: FieldStatus
  reason: string
  thresholds: {
    low: number
    high: number
    crop_specific: boolean
    soil_adjusted: boolean
  }
  inputs: {
    moisture_percentage: number | null
    recorded_at: string | null
    freshness: Freshness
    age_hours: number | null
    source: string | null
    sensor_identifier: string | null
    has_sensor: boolean
    sensor_identifiers: string[]
    crop_type: string
    soil_type: string
    growth_stage: string
    weather: {
      temperature: number
      rainfall_probability: number
      rainfall_mm: number
      retrieved_at: string
      provider: string
      rain_expected: boolean
    } | null
  }
  limitations: string[]
  review_required: boolean
  review_note: string
}

// ---------------------------------------------------------------------------
// Irrigation intelligence
// ---------------------------------------------------------------------------

export interface IrrigationEvent {
  id: number
  field_id: number
  field_name: string | null
  start_time: string
  end_time: string | null
  duration_minutes: number | null
  water_volume_litres: number | null
  volume_measured: boolean
  application_method: string | null
  water_source: string | null
  recorded_by: string
  notes: string | null
  created_at: string
}

export interface IrrigationEventList {
  items: IrrigationEvent[]
  total: number
  limit: number
  offset: number
}

export type SchedulePriority = "low" | "medium" | "high" | "critical" | "uncertain"

export interface IrrigationSchedule {
  id: number
  field_id: number
  field_name: string | null
  scheduled_date: string
  recommended_start_time: string | null
  recommended_window_end: string | null
  estimated_volume_litres: number | null
  estimated_duration_minutes: number | null
  estimated_depth_mm: number | null
  priority: SchedulePriority
  reason: string | null
  reason_code: string | null
  model_version: string | null
  confidence: number | null
  uncertainty_litres: number | null
  status: "pending" | "accepted" | "completed" | "skipped" | "cancelled" | string
  actual_volume_litres: number | null
  actual_duration_minutes: number | null
  completed_at: string | null
  created_at: string | null
  prediction_id: number | null
  is_decision_support: boolean
}

export interface TodaySchedule {
  date: string
  timezone: string
  entries: IrrigationSchedule[]
  total_estimated_litres: number
  decision_support_notice: string
  generated_at: string
}

export interface WaterRequirement {
  current_moisture: number | null
  field_capacity: number | null
  wilting_point: number | null
  root_depth_mm: number | null
  root_depth_m: number | null
  kc: number | null
  et0_mm: number | null
  et0_source: string | null
  crop_water_use_mm: number | null
  depletion_mm: number | null
  effective_rainfall_mm: number | null
  net_requirement_mm: number | null
  gross_requirement_mm: number | null
  application_efficiency: number | null
  area_ha: number | null
  net_volume_litres: number | null
  gross_volume_litres: number | null
  assumptions: string[]
  missing_inputs: string[]
  confidence: string
  calculation_version: string
}

export interface Prediction {
  field_id: number
  field_name: string | null
  predicted_at: string
  target_time: string | null
  current_moisture: number | null
  predicted_moisture: number | null
  moisture_trend_pp_per_day: number | null
  irrigation_requirement_mm: number | null
  estimated_volume_litres: number | null
  estimated_volume_unit: string
  recommended_date: string | null
  model_name: string
  model_version: string | null
  model_status: string
  confidence: number
  uncertainty: number | null
  provisional: boolean
  reason: string
  data_freshness: Freshness
  calculation_version: string | null
  requirement: WaterRequirement | null
  input_refs: Record<string, unknown> | null
  limitations: string[]
  prediction_id: number | null
}

export interface PredictionHistory {
  id: number
  field_id: number
  predicted_at: string
  target_time: string | null
  current_moisture: number | null
  predicted_moisture: number | null
  irrigation_requirement_mm: number | null
  estimated_volume_litres: number | null
  model_name: string | null
  model_version: string | null
  confidence: number | null
  status: string
  data_freshness: string | null
}

export interface FieldIrrigationSettings {
  field_id: number
  application_method: string | null
  application_rate_litres_per_hour: number | null
  application_efficiency: number | null
  water_source: string | null
  notes: string | null
}

export interface FarmerIrrigationPreference {
  preferred_start_time: string | null
  preferred_end_time: string | null
  max_daily_volume_litres: number | null
  irrigation_days: string
  notes: string | null
}

export interface WaterUsageByField {
  field_id: number
  field_name: string | null
  crop_type: string | null
  area_acres: number | null
  total_litres: number
  events: number
  litres_per_acre: number | null
  average_per_event_litres: number | null
}

export interface WaterUsageByCrop {
  crop_type: string
  total_litres: number
  events: number
  fields: number[]
  average_per_event_litres: number | null
}

export interface WaterSeriesPoint {
  bucket: string
  litres: number
  events: number
}

export interface WaterDayPoint {
  date: string
  total_litres: number
  events: number
}

export interface PlannedVsActualPoint {
  date: string
  planned_litres: number
  actual_litres: number
}

export interface EstimatedVsActualPoint {
  schedule_id: number
  field_id: number
  field_name: string | null
  scheduled_date: string | null
  estimated_litres: number | null
  actual_litres: number | null
  difference_litres: number | null
  difference_percent: number | null
}

export interface WaterUsage {
  total_litres: number
  measured_event_count: number
  unmeasured_event_count: number
  events_without_measurement: Array<Record<string, unknown>>
  period_start: string | null
  period_end: string | null
  by_field: WaterUsageByField[]
  by_crop: WaterUsageByCrop[]
  by_day: WaterDayPoint[]
  daily_series: WaterSeriesPoint[]
  weekly_series: WaterSeriesPoint[]
  monthly_series: WaterSeriesPoint[]
  average_per_event_litres: number | null
  average_per_event_days: number | null
  irrigation_frequency_per_week: number | null
  litres_per_acre: number | null
  planned_vs_actual: PlannedVsActualPoint[]
  estimated_vs_actual: EstimatedVsActualPoint[]
  data_notes: string[]
}

export interface WaterUsageTrends {
  daily: WaterSeriesPoint[]
  weekly: WaterSeriesPoint[]
  monthly: WaterSeriesPoint[]
  by_day: WaterDayPoint[]
  by_crop: WaterUsageByCrop[]
  planned_vs_actual: PlannedVsActualPoint[]
  estimated_vs_actual: EstimatedVsActualPoint[]
  period_comparison: {
    days: number
    current_start: string
    current_end: string
    previous_start: string
    previous_end: string
    current_litres: number
    previous_litres: number
    change_litres: number | null
    change_percent: number | null
  }
  period_totals: {
    today: { litres: number; events: number }
    this_week: { litres: number; events: number }
    this_month: { litres: number; events: number }
    timezone: string
    week_start: string
    month_start: string
  }
  average_per_event_litres: number | null
  average_per_event_days: number | null
  irrigation_frequency_per_week: number | null
  timezone: string
  data_notes: string[]
}

export interface DashboardAnalytics {
  total_fields: number
  fields_healthy: number
  fields_requiring_attention: number
  fields_without_data: number
  sensors_reporting_recently: number
  water_usage_today_litres: number
  water_usage_this_week_litres: number
  water_usage_this_month_litres: number
  scheduled_volume_today_litres: number
  scheduled_fields_today: number
  fields_needing_irrigation_today: number
  moisture_status_distribution: Array<{ status: string; count: number }>
  crop_water_usage: WaterUsageByCrop[]
  field_water_usage: WaterUsageByField[]
  fields_needing_updated_measurements: Array<{
    field_id: number
    field_name: string
    freshness: Freshness
    age_hours: number | null
    last_updated: string | null
    has_sensor: boolean
  }>
  recent_irrigation_events: Array<{
    id: number
    field_id: number
    field_name: string | null
    start_time: string
    duration_minutes: number | null
    water_volume_litres: number | null
    volume_measured: boolean
    application_method: string | null
  }>
  daily_water_series: WaterSeriesPoint[]
  weekly_water_series: WaterSeriesPoint[]
  monthly_water_series: WaterSeriesPoint[]
  planned_vs_actual: PlannedVsActualPoint[]
  data_notes: string[]
  timezone: string
  generated_at: string
}

export interface ModelStatus {
  model_name: string | null
  model_version: string | null
  status: "baseline_only" | "provisional" | "validated" | string
  trained_at: string | null
  training_samples: number | null
  validation_samples: number | null
  training_period_start: string | null
  training_period_end: string | null
  validation_period_start: string | null
  validation_period_end: string | null
  features: string[]
  metrics: Record<string, any>
  baseline_metrics: Record<string, any>
  comparison: Record<string, any>
  data_limitations: string[]
  minimum_production_requirements: {
    min_training_samples: number
    min_fields: number
    min_span_days: number
    actual_training_samples: number
    actual_fields: number
    actual_span_days: number
    meets_requirements: boolean
  }
  active_predictor: string
  provisional: boolean
  note: string
  available_versions: Array<Record<string, any>>
}
