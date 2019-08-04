from django.contrib import admin

from sqds.admin import ReadOnlyMixin
from .models import GAPool, GAPoolPlayer


class GAPoolPlayerInline(ReadOnlyMixin, admin.TabularInline):
    model = GAPoolPlayer
    extra = 0


@admin.register(GAPool)
class GuildAdmin(ReadOnlyMixin, admin.ModelAdmin):
    readonly_fields = ('id',)
    inlines = [GAPoolPlayerInline]
