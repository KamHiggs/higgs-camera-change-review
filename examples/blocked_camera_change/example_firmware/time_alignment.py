"""Synthetic current firmware FW-1.0: shared offset only."""

def normalize_timestamp(sensor_timestamp_ms, config):
    return sensor_timestamp_ms + config["shared_offset_ms"]
