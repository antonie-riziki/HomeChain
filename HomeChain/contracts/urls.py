from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'milestones', ContractMilestoneViewSet, basename='milestone')
router.register(r'amendments', ContractAmendmentViewSet, basename='amendment')
router.register(r'templates', ContractTemplateViewSet, basename='template')

urlpatterns = [
    path('', include(router.urls)),
]