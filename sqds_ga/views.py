from django.db import transaction
from django.http import HttpResponseNotFound, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView
from meta.views import MetadataMixin

from sqds.models import Player
from utils import extract_all_ally_codes
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


def view_ga_pool(request, pk):
    ga_pool = get_object_or_404(GAPool, pk=pk)

    response_string = f"""
    Focus player: {ga_pool.focus_player.name} <br/>
    Players: {[p.player.name for p in GAPoolPlayer.objects.filter(ga_pool=ga_pool)]}
    """
    return HttpResponse(response_string)


class GAPoolView(MetadataMixin, DetailView):
    model = GAPool
    template_name = 'sqds_ga/ga_pool_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['focus_player'] = (Player.objects
                                   .filter(pk=self.object.focus_player.pk)
                                   .annotate_stats()
                                   .select_related('guild')
                                   .first())
        context['players'] = list(Player.objects
                                  .filter(ga_pool_player_set__ga_pool=self.object)
                                  .select_related('guild')
                                  .annotate_stats())
        context['all_players'] = [context['focus_player'], *context['players']]
        return context

    def get_meta_title(self, **kwargs):
        pass

    def get_meta_description(self, context=None):
        pass
