from django.urls import path

from . import views

app_name = 'sqds_officers'
urlpatterns = [
    path('', views.index, name='index'),
    path('geotb/', views.GeoTBPlayerView.as_view(), name='geo_tb'),
    path('sepfarm/', views.SepFarmProgressView.as_view(), name='sep_farm')
]
