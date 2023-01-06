from django.urls import path

from . import views

app_name = 't9a'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('results/<int:pk>', views.ResultView.as_view(), name='results'),
    path('results/', views.ResultView.as_view(), name='results'),
    path('lists/<int:pk>', views.ListsView.as_view(), name='lists'),
    path('lists/', views.ListsView.as_view(), name='lists'),
    path('add-list/<int:pk>', views.AddListView.as_view(), name='add-list'),
    path('add-list/', views.AddListView.as_view(), name='add-list'),
    path('my-account/', views.ChangeUsernameView.as_view(), name='my-account'),
    path('add-game/', views.GameCreateView.as_view(), name='add-game'),
    path('all-results/', views.AllResultsView.as_view(), name='all-results'),
    path('logout', views.LogoutView.as_view(), name='logout'),
    path('approve/<int:pk>', views.ApproveResultView.as_view(), name='approve-result'),
    path('approve/', views.ApproveResultView.as_view(), name='approve-result'),
    path('csv/', views.CSVView.as_view(), name='csv-all-results'),
    path('add-group/', views.AddGamingGroup.as_view(), name='add-group'),
    path('list-groups/', views.GamingGroupListView.as_view(), name='list-groups'),
    



]
