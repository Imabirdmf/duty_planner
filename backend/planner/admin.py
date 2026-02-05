from django.contrib import admin

from .models import DutyAssignment, Staff, Duty, DaysOff


admin.site.register(DutyAssignment)
admin.site.register(Staff)
admin.site.register(Duty)
admin.site.register(DaysOff)