from django.urls import path

from . import views

app_name = 'sqds'
urlpatterns = [
    # path('players/', views.players, name='players')
    path('players/', views.FilteredPlayerListView.as_view(), name='players'),
    path('units/', views.AllPlayerUnitsListView.as_view(), name='units'),
    path('player/<int:ally_code>/',
         views.SinglePlayerView.as_view(),
         name='player')
]
