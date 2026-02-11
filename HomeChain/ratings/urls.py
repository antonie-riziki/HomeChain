from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'summaries', RatingSummaryViewSet, basename='summary')
router.register(r'comments', RatingCommentViewSet, basename='comment')
router.register(r'flags', RatingFlagViewSet, basename='flag')

urlpatterns = [
    path('', include(router.urls)),
]