from django.urls import path

from . import views

app_name = 'sqds_officers'
urlpatterns = [
    path('<str:api_id>/geotb/', views.GeoTBPlayerView.as_view(), name='geo_tb'),
    path('<str:api_id>/sepfarm/', views.SepFarmProgressView.as_view(), name='sep_farm')
]
