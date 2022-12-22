from django.contrib import admin
from . import models

admin.site.register(models.Games)
admin.site.register(models.Lists)
admin.site.register(models.Results)
admin.site.register(models.Army)
admin.site.register(models.Deployments)
admin.site.register(models.Map)
admin.site.register(models.Secondaries)

