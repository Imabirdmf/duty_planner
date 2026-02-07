from django.contrib import admin

from .models import DaysOff, Duty, DutyAssignment, Staff

admin.site.register(DutyAssignment)
admin.site.register(Staff)
admin.site.register(Duty)
admin.site.register(DaysOff)
