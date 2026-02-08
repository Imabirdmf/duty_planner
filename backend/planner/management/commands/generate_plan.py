from django.core.management.base import BaseCommand
from planner.services.planner import create_plan
from planner.services.assignments import make_assignment
from datetime import datetime


# class Command(BaseCommand):
#     help = "Generate duty plan"
#
#     def handle(self, *args, **options):
#         print(create_plan())

class Command(BaseCommand):
    help = 'make_assignment'

    def handle(self, *args, **kwargs):
        print(make_assignment(5,datetime(2026,2,2), 4))