from __future__ import annotations

import datetime

from analytics.selectors import (
    completed_inspections_daily,
    completed_inspections_monthly,
    completed_inspections_total,
    top_inspected_vehicle_types,
    vehicles_total,
)

DEFAULT_RANGE_DAYS = 30


def default_date_range() -> tuple[datetime.date, datetime.date]:
    date_to = datetime.date.today()
    date_from = date_to - datetime.timedelta(days=DEFAULT_RANGE_DAYS - 1)
    return date_from, date_to


def build_dashboard_stats(*, date_from: datetime.date, date_to: datetime.date) -> dict:
    if date_from > date_to:
        raise ValueError("date_from nie moze byc pozniejsze od date_to.")

    daily_data = [
        {"date": row["day"].isoformat(), "count": row["count"]}
        for row in completed_inspections_daily(date_from=date_from, date_to=date_to)
    ]
    monthly_data = [
        {"month": row["month"].date().strftime("%Y-%m"), "count": row["count"]}
        for row in completed_inspections_monthly(date_from=date_from, date_to=date_to)
    ]
    top_vehicle_types = [
        {
            "vehicle_type": row["appointment__vehicle__vehicle_type"],
            "inspections_count": row["inspections_count"],
        }
        for row in top_inspected_vehicle_types(date_from=date_from, date_to=date_to)
    ]

    return {
        "date_from": date_from,
        "date_to": date_to,
        "metrics": {
            "completed_inspections_total": completed_inspections_total(date_from=date_from, date_to=date_to),
            "vehicles_total": vehicles_total(),
        },
        "completed_inspections_daily": daily_data,
        "completed_inspections_monthly": monthly_data,
        "top_vehicle_types": top_vehicle_types,
    }

