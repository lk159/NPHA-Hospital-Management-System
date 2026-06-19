

from django.contrib import admin
from .models import *

admin.site.register(Patients)
admin.site.register(Visits)
admin.site.register(Admissions)
admin.site.register(Beds)
admin.site.register(Wards)