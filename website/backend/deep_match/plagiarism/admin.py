# admin.py
from django.contrib import admin
from .models import PlagiarismReport, PlagiarismSession

admin.site.register(PlagiarismReport)
admin.site.register(PlagiarismSession)