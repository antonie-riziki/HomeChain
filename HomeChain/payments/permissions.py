from rest_framework import permissions

class IsWalletOwner(permissions.BasePermission):
    """Allow access only to wallet owner"""
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsEscrowParty(permissions.BasePermission):
    """Allow access to employer or worker of escrow"""
    
    def has_object_permission(self, request, view, obj):
        return request.user in [obj.contract.employer, obj.contract.worker]


class CanWithdraw(permissions.BasePermission):
    """Check if user can withdraw (worker only)"""
    
    def has_permission(self, request, view):
        return request.user.user_type == 'WORKER'


class IsWithdrawalOwner(permissions.BasePermission):
    """Allow access only to withdrawal owner"""
    
    def has_object_permission(self, request, view, obj):
        return obj.worker == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """Admin only for write operations"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.user_type == 'ADMIN'