from django.urls import path, include
from . import views



urlpatterns = [
    path('', views.home, name="home"),
    path('contract/', views.contract, name='contract'),
    path('employer-dashboard/', views.employer_dashboard, name='employer-dashboard'),
    path('job-post/',views.job_post,name='job-post'),
    path('resolution/',views.resolution,name='resolution'),
    path('role-selection/',views.role_selection,name='role-selection'),
    path('wallet',views.wallet,name='wallet'),
    path('worker-dashboard',views.worker_dashboard,name='worker-dashboard'),


]