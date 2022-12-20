from django.urls import path

from . import views

app_name = 't9a'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),


]
