from django.urls import path

from . import views

app_name = 'sqds'
urlpatterns = [
    # path('players/', views.players, name='players')
    path('', views.index, name='index'),
    path('players/', views.FilteredPlayerListView.as_view(), name='players'),
    path('unit/<int:player_unit_id>/', views.unit, name='unit'),
    path('guild/<str:api_id>/', views.GuildView.as_view(), name='guild'),
    path('units/', views.AllPlayerUnitsListView.as_view(), name='units'),
    path('player/<int:ally_code>/',
         views.SinglePlayerView.as_view(), name='player'),
    path('player/<int:ally_code1>/c/<int:ally_code2>/',
         views.PlayerCompareView.as_view(), name='player_compare'),
    path('player/<int:ally_code>/refresh/',
         views.player_refresh, name='player_refresh')
]
