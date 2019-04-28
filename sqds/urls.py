from django.urls import path

from . import views

app_name = 'sqds'
urlpatterns = [
    # path('players/', views.players, name='players')
    path('players/', views.FilteredPlayerListView.as_view(), name='players'),
    path('units/', views.AllPlayerUnitsListView.as_view(), name='units'),
    path('player/<int:ally_code>/',
         views.SinglePlayerView.as_view(), name='player'),
    path('player/<int:ally_code1>/c/<int:ally_code2>/',
         views.PlayerCompareView.as_view(), name='player_compare')
]
