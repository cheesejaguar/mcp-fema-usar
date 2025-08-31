"""Constants and configuration values for FEMA USAR operations."""

# Safety thresholds for structural monitoring
STRUCTURAL_SAFETY_THRESHOLDS = {
    "movement_alarm_mm": 10,
    "vibration_alarm_hz": 5.0,
    "stress_alarm_percent": 80,
    "automatic_evacuation_trigger": 90,
}

# Rescue operation parameters
RESCUE_OPERATION_PARAMETERS = {
    "manual": {"time": 1.0, "personnel": 4, "equipment": 3},
    "mechanical": {"time": 2.0, "personnel": 6, "equipment": 6},
    "technical": {"time": 3.0, "personnel": 8, "equipment": 10},
    "complex": {"time": 5.0, "personnel": 12, "equipment": 15},
    "vertical_lift": {"time": 2.5, "personnel": 8, "equipment": 8},
}

# Search pattern optimization parameters
SEARCH_OPTIMIZATION_PARAMS = {
    "grid_spacing_meters": 1.5,
    "overlap_percentage": 15,
    "time_per_grid_minutes": 10,
    "personnel_per_team": 3,
}

# Medical triage parameters
MEDICAL_TRIAGE_PARAMS = {
    "red_priority_max_delay_minutes": 15,
    "yellow_priority_max_delay_minutes": 60,
    "green_priority_max_delay_minutes": 240,
    "black_category_determination_time_minutes": 5,
}

# Equipment maintenance thresholds
EQUIPMENT_MAINTENANCE_THRESHOLDS = {
    "inspection_interval_hours": 72,
    "preventive_maintenance_hours": 168,
    "critical_maintenance_hours": 336,
    "replacement_threshold_hours": 2000,
}

# Communication system parameters
COMMUNICATION_PARAMS = {
    "primary_frequency_mhz": 155.1750,
    "backup_frequency_mhz": 155.2125,
    "satellite_check_interval_minutes": 30,
    "radio_battery_low_threshold_percent": 20,
}

# Personnel limits and requirements
PERSONNEL_LIMITS = {
    "max_continuous_work_hours": 12,
    "mandatory_rest_hours": 8,
    "max_team_size": 8,
    "min_team_size": 2,
    "leadership_span_of_control": 7,
}

# Environmental monitoring limits
ENVIRONMENTAL_LIMITS = {
    "max_temperature_celsius": 40,
    "min_temperature_celsius": -10,
    "max_wind_speed_mph": 25,
    "min_visibility_meters": 50,
    "max_air_quality_index": 150,
}

# Deterministic test data (replaces random generation for testing)
DETERMINISTIC_TEST_DATA = {
    "victim_detection_confidence_scores": [0.85, 0.92, 0.78, 0.96],
    "detection_count_range": [2, 3, 4],  # Instead of random.randint(1, 4)
    "efficiency_scores": [0.75, 0.89, 0.82, 0.94],
    "building_sectors": ["A1", "B2", "C3", "A4"],
    "access_routes": ["main_entrance", "emergency_access", "roof_access"],
    "sensor_types": ["acoustic", "thermal", "seismic", "chemical"],
}
