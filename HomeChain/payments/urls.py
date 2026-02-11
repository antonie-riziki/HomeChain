from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'transactions', PaymentTransactionViewSet, basename='transaction')
router.register(r'wallets', PaymentWalletViewSet, basename='wallet')
router.register(r'escrows', PaymentEscrowViewSet, basename='escrow')
router.register(r'withdrawals', WithdrawalRequestViewSet, basename='withdrawal')
router.register(r'fees', PlatformFeeViewSet, basename='fee')
router.register(r'stats', PaymentStatsViewSet, basename='stats')

urlpatterns = [
    path('', include(router.urls)),
]