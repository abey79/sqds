from django.urls import path

from . import views

app_name = 'sqds_medals'
urlpatterns = [
    path('list/', views.MedalList.as_view(), name='list'),
]
