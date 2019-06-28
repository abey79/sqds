from django.urls import path

from . import views

app_name = 'sqds_officers'
urlpatterns = [
    path('geotb/', views.GeoTBPlayerView.as_view(), name='geotb'),
]
