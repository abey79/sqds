from django.urls import path

from . import views

app_name = 'sqds_ga'
urlpatterns = [
    path('<int:ally_code>/create/', views.create_ga_pool, name='create'),
    path('view/<int:pk>/', views.GAPoolView.as_view(), name='view'),
]
