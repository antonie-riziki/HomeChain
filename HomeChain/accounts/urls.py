from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

# Create router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'skills', SkillViewSet, basename='skill')
router.register(r'worker-skills', WorkerSkillViewSet, basename='worker-skill')
router.register(r'documents', WorkerDocumentViewSet, basename='document')
router.register(r'verification-requests', VerificationRequestViewSet, basename='verification-request')

urlpatterns = [
    # Auth endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Include router URLs
    path('', include(router.urls)),
]