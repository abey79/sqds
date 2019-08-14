from django.db import transaction
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView
from meta.views import MetadataMixin

from sqds.models import Player
from sqds.utils import extract_all_ally_codes
from .models import GAPool, GAPoolPlayer


@require_http_methods(["POST"])
def create_ga_pool(request, ally_code):
    """
    Create a new GA pool with ally_code as focus player. POST parameter ally_codes
    must contain text codes
    """

    if 'ally_codes' in request.POST:
        ally_codes = extract_all_ally_codes(request.POST['ally_codes'])

        with transaction.atomic():
            ga_pool = GAPool(focus_player=get_object_or_404(Player, ally_code=ally_code))
            ga_pool.save()

            Player.objects.ensure_exist(ally_codes, max_days=7)

            for ac in ally_codes:
                ga_pool_player = GAPoolPlayer(ga_pool=ga_pool,
                                              player=Player.objects.get(ally_code=ac))
                ga_pool_player.save()

        return redirect('sqds_ga:view', pk=ga_pool.pk)
    else:
        return HttpResponseNotFound()


class GAPoolView(MetadataMixin, DetailView):
    model = GAPool
    template_name = 'sqds_ga/ga_pool_overview.html'

    # noinspection PyAttributeOutsideInit
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # We load other object as well
        self.focus_player = (Player.objects
                             .filter(pk=obj.focus_player.pk)
                             .annotate_stats()
                             .annotate_faction_gp()
                             .select_related('guild')
                             .first())
        self.players = list(Player.objects
                            .filter(ga_pool_player_set__ga_pool=obj)
                            .select_related('guild')
                            .annotate_faction_gp()
                            .annotate_stats())
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['focus_player'] = self.focus_player
        context['players'] = self.players
        context['all_players'] = [context['focus_player'], *context['players']]
        return context

    def get_meta_title(self, context=None):
        return f"GA Pool ({self.focus_player.name})"

    def get_meta_description(self, context=None):
        return "{} vs. {} ({})".format(
            self.focus_player.name,
            ', '.join([p.name for p in self.players]),
            self.object.created)
