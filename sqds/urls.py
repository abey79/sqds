from django.urls import path

from . import views

app_name = 'sqds'
urlpatterns = [
    # path('players/', views.players, name='players')
    path('', views.index, name='index'),
    path('players/', views.FilteredPlayerListView.as_view(), name='players'),
    path('unit/<int:pk>/', views.UnitView.as_view(), name='unit'),
    path('guild/<str:api_id>/', views.GuildView.as_view(), name='guild'),
    path('guild/<str:api_id>/units/', views.GuildUnitsView.as_view(), name='guild_units'),
    path('guild/<str:api_id1>/c/<str:api_id2>/units/',
         views.GuildComparisonUnitsView.as_view(), name='guild_compare_units'),
    path('units/', views.AllPlayerUnitsListView.as_view(), name='units'),
    path('player/<int:ally_code>/',
         views.SinglePlayerView.as_view(), name='player'),
    path('player/<int:ally_code>/me',
         views.player_register_me, name='player_register'),
    path('me/clear', views.player_unregister_me, name='player_unregister'),
    path('player/<int:ally_code1>/c/<int:ally_code2>/',
         views.PlayerCompareView.as_view(), name='player_compare'),
    path('player/<int:ally_code1>/c/<int:ally_code2>/units/',
         views.PlayerCompareUnitsView.as_view(), name='player_compare_units'),
    path('player/<int:ally_code>/refresh/',
         views.player_refresh, name='player_refresh')
]
