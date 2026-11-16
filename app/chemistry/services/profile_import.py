"""Validate uploaded analytical tables before storing any rows."""

import csv
import math
from io import StringIO

MAX_CSV_BYTES = 512 * 1024
MAX_FEATURES = 1000
STATUSES = {"measured", "not_detected", "not_measured"}


def read_measurements(content: bytes, basis: str):
    if len(content) > MAX_CSV_BYTES:
        raise ValueError("The CSV exceeds the 512 KiB limit.")
    try:
        source = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("Save the CSV as UTF-8 and try again.") from error
    reader = csv.DictReader(StringIO(source, newline=""), strict=True)
    required = {"feature", "value", "confidence"}
    try:
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not required.issubset(headers) or set(headers) - required - {"status"}:
            raise ValueError("Use the CSV columns feature,value,confidence and optional status.")
        rows = []
        seen = set()
        for row in reader:
            line = reader.line_num
            if len(rows) >= MAX_FEATURES:
                raise ValueError(f"A profile supports at most {MAX_FEATURES} features.")
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Row {line} has the wrong number of columns.")
            feature = row["feature"].strip()
            confidence = row["confidence"].strip()
            status = row.get("status", "").strip() or "measured"
            if not feature or len(feature) > 160 or feature.casefold() in seen:
                raise ValueError(f"Row {line} needs a unique feature name of up to 160 characters.")
            if not confidence or len(confidence) > 30 or status not in STATUSES:
                raise ValueError(f"Row {line} has an invalid confidence label or measurement status.")
            raw_value = row["value"].strip()
            if status != "measured":
                if raw_value:
                    raise ValueError(f"Leave the value blank for an unmeasured feature on row {line}.")
                value = None
            else:
                try:
                    value = float(raw_value)
                except ValueError as error:
                    raise ValueError(f"Row {line} needs a numeric value.") from error
                if not math.isfinite(value) or value < 0 or (basis == "peak_area_percent" and value > 100):
                    raise ValueError(f"Row {line} has a value outside the allowed range.")
            seen.add(feature.casefold())
            rows.append({"feature": feature, "confidence": confidence, "status": status, "value": value})
    except csv.Error as error:
        raise ValueError(f"Malformed CSV near row {reader.line_num}.") from error
    if not any(row["value"] is not None for row in rows):
        raise ValueError("Include at least one measured feature.")
    if basis == "peak_area_percent" and sum(row["value"] or 0 for row in rows) > 100.5:
        raise ValueError("Peak-area percentages must total at most 100%, allowing minor rounding.")
    return source, rows
