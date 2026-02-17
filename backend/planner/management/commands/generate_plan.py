from datetime import date

from django.core.management.base import BaseCommand
from planner.services.duty_calendar import save_duty_days
from planner.services.planner import create_plan


class Command(BaseCommand):
    help = "Generate duty plan"

    def handle(self, *args, **options):
        print(save_duty_days(dates))
        print(create_plan(date(2026, 2, day=1), date(2026, 2, day=28)))


dates = [
    "2026-02-01",
    "2026-02-08",
    "2026-02-15",
    "2026-02-22",
    "2026-02-02",
    "2026-02-09",
    "2026-02-16",
    "2026-02-23",
    "2026-02-03",
    "2026-02-10",
    "2026-02-17",
    "2026-02-24",
    "2026-02-04",
    "2026-02-11",
    "2026-02-18",
    "2026-02-25",
    "2026-02-05",
    "2026-02-12",
    "2026-02-19",
    "2026-02-26",
    "2026-02-06",
    "2026-02-13",
    "2026-02-20",
    "2026-02-27",
    "2026-02-07",
    "2026-02-14",
    "2026-02-21",
    "2026-02-28",
]
