from rest_framework import permissions

class CanRateContract(permissions.BasePermission):
    """Check if user can rate a contract"""
    
    def has_object_permission(self, request, view, obj):
        # User must be party to contract
        if request.user not in [obj.employer, obj.worker]:
            return False
        
        # Contract must be completed
        if obj.status != 'COMPLETED':
            return False
        
        # Check if already rated
        from .models import Rating
        return not Rating.objects.filter(
            contract=obj,
            reviewer=request.user
        ).exists()


class IsRatingReviewer(permissions.BasePermission):
    """Allow access only to rating reviewer"""
    
    def has_object_permission(self, request, view, obj):
        return obj.reviewer == request.user


class IsRatingReviewee(permissions.BasePermission):
    """Allow access only to rating reviewee"""
    
    def has_object_permission(self, request, view, obj):
        return obj.reviewee == request.user


class IsRatingParty(permissions.BasePermission):
    """Allow access to both reviewer and reviewee"""
    
    def has_object_permission(self, request, view, obj):
        return request.user in [obj.reviewer, obj.reviewee]


class CanRespondToRating(permissions.BasePermission):
    """Check if user can respond to rating"""
    
    def has_object_permission(self, request, view, obj):
        # Only reviewee can respond
        if obj.reviewee != request.user:
            return False
        
        # Can't respond twice
        if obj.response_text:
            return False
        
        return True


class IsCommentOwner(permissions.BasePermission):
    """Allow access only to comment owner"""
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsFlagOwner(permissions.BasePermission):
    """Allow access only to flag owner"""
    
    def has_object_permission(self, request, view, obj):
        return obj.flagged_by == request.user