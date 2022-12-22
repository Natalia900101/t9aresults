from django.urls import path

from . import views

app_name = 't9a'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('results/', views.ResultView.as_view(), name='results'),
    path('lists/<int:pk>', views.ListsView.as_view(), name='lists'),
    path('lists/', views.ListsView.as_view(), name='lists'),





]
