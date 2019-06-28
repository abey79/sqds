from django.contrib import admin

from .models import Unit, Skill, Gear, Guild, Category


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class ReadOnlyMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SkillInline(ReadOnlyMixin, admin.TabularInline):
    model = Skill
    extra = 0


@admin.register(Unit)
class UnitAdmin(ReadOnlyMixin, admin.ModelAdmin):
    inlines = [SkillInline]


@admin.register(Gear)
class GearAdmin(ReadOnlyMixin, admin.ModelAdmin):
    pass


@admin.register(Skill)
class SkillAdmin(ReadOnlyMixin, admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(ReadOnlyMixin, admin.ModelAdmin):
    pass


@admin.register(Guild)
class GuildAdmin(ReadOnlyMixin, admin.ModelAdmin):
    pass
