from django.core.management.base import BaseCommand
from planner.services.planner import create_plan


class Command(BaseCommand):
    help = "Generate duty plan"

    def handle(self, *args, **options):
        print(create_plan())
