from rest_framework import permissions

class IsEmployer(permissions.BasePermission):
    """Allow access only to employers"""
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'EMPLOYER'
        )


class IsWorker(permissions.BasePermission):
    """Allow access only to workers"""
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'WORKER'
        )


class IsJobOwner(permissions.BasePermission):
    """Allow access only to job owner (employer who posted)"""
    
    def has_object_permission(self, request, view, obj):
        return obj.employer == request.user


class IsAssignedWorker(permissions.BasePermission):
    """Allow access only to assigned worker"""
    
    def has_object_permission(self, request, view, obj):
        return obj.worker == request.user


class IsJobOwnerOrAssignedWorker(permissions.BasePermission):
    """Allow access to job owner or assigned worker"""
    
    def has_object_permission(self, request, view, obj):
        return obj.employer == request.user or obj.worker == request.user


class IsApplicationOwner(permissions.BasePermission):
    """Allow access only to application owner (worker who applied)"""
    
    def has_object_permission(self, request, view, obj):
        return obj.worker == request.user