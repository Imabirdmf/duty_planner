from datetime import date

from django.core.management.base import BaseCommand
from planner.services.planner import create_plan


class Command(BaseCommand):
    help = "Generate duty plan"

    def handle(self, *args, **options):
        print(create_plan(date(2026, 2, day=1), date(2026, 2, day=5)))


# class Command(BaseCommand):
#     help = "make_assignment"
#
#     def handle(self, *args, **kwargs):
#         print(make_assignment(5, datetime(2026, 2, 2), 4))

# class Command(BaseCommand):
#     help = "Generate duty plan"
#
#     def handle(self, *args, **options):
#         print(get_assignments(date(2026, 2, day=1), date(2026, 2, day=5)))


# class Command(BaseCommand):
#     help = "make_assignment"
#
#     def handle(self, *args, **kwargs):
#         print(get_duty_days(datetime(2026, 2, 2), datetime(2026, 2, 2)))
