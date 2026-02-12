from rest_framework import permissions

class IsContractEmployer(permissions.BasePermission):
    """Allow access only to contract employer"""
    
    def has_object_permission(self, request, view, obj):
        return obj.employer == request.user


class IsContractWorker(permissions.BasePermission):
    """Allow access only to contract worker"""
    
    def has_object_permission(self, request, view, obj):
        return obj.worker == request.user


class IsContractParty(permissions.BasePermission):
    """Allow access to both employer and worker"""
    
    def has_object_permission(self, request, view, obj):
        return obj.employer == request.user or obj.worker == request.user


class CanSignContract(permissions.BasePermission):
    """Check if user can sign contract"""
    
    def has_object_permission(self, request, view, obj):
        if obj.status != 'PENDING':
            return False
        return obj.employer == request.user or obj.worker == request.user


class CanAmendContract(permissions.BasePermission):
    """Check if user can propose amendment"""
    
    def has_object_permission(self, request, view, obj):
        if obj.status not in ['ACTIVE', 'PENDING']:
            return False
        return obj.employer == request.user or obj.worker == request.user