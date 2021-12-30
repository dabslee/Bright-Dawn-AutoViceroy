from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Player)
admin.site.register(models.Character)
admin.site.register(models.Debt)
admin.site.register(models.LedgerLog)