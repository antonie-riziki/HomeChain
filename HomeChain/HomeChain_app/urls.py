from django.urls import path, include
from . import views



urlpatterns = [
    path('', views.home, name="home"),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('role-selection/', views.role_selection, name='role-selection'),
    path('browse-jobs/', views.browse_jobs, name='browse-jobs'),
    path('workers/', views.workers, name='workers'),
    path('contract/', views.contract, name='contract'),
    path('employer-dashboard/', views.employer_dashboard, name='employer-dashboard'),
    path('job-post/', views.job_post, name='job-post'),
    path('resolution/', views.resolution, name='resolution'),
    path('wallet/', views.wallet, name='wallet'),
    path('worker-dashboard/', views.worker_dashboard, name='worker-dashboard'),
    path('map-view/', views.map_view, name='map-view'),
    path('about/', views.about, name='about'),
    path('help/', views.help_center, name='help'),
    path('contact/', views.contact, name='contact'),
    path('learn/', views.learn_skills, name='learn-skills'),


]