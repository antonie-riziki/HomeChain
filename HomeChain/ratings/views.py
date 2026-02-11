from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Rating, RatingSummary, RatingComment, RatingFlag
from .serializers import *
from .permissions import *
from contracts.models import Contract
from accounts.models import User

class RatingViewSet(viewsets.ModelViewSet):
    """Rating management viewset"""
    
    queryset = Rating.objects.filter(is_public=True, is_flagged=False)
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rating_type', 'overall_rating', 'would_recommend']
    search_fields = ['review_text', 'reviewer__full_name', 'reviewee__full_name']
    ordering_fields = ['created_at', 'overall_rating']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'ADMIN' or user.is_staff:
            # Admins see all ratings including flagged
            return Rating.objects.all()
        else:
            # Regular users see public, non-flagged ratings
            return Rating.objects.filter(is_public=True, is_flagged=False)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RatingDetailSerializer
        return RatingSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'respond':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['post'])
    def rate_contract(self, request):
        """Rate a completed contract"""
        contract_id = request.data.get('contract_id')
        
        try:
            contract = Contract.objects.get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if request.user not in [contract.employer, contract.worker]:
            return Response(
                {'error': 'You are not a party to this contract'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if contract.status != 'COMPLETED':
            return Response(
                {'error': 'You can only rate completed contracts'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already rated
        if Rating.objects.filter(contract=contract, reviewer=request.user).exists():
            return Response(
                {'error': 'You have already rated this contract'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create rating
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(contract=contract)
        
        # Update rating summary
        summary, _ = RatingSummary.objects.get_or_create(user=serializer.data['reviewee'])
        summary.update()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Respond to a rating"""
        rating = self.get_object()
        
        # Check if user is the reviewee
        if rating.reviewee != request.user:
            return Response(
                {'error': 'Only the person being rated can respond'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already responded
        if rating.response_text:
            return Response(
                {'error': 'You have already responded to this rating'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RatingResponseSerializer(
            data=request.data,
            context={'request': request, 'rating': rating}
        )
        serializer.is_valid(raise_exception=True)
        
        rating.response_text = serializer.validated_data['response_text']
        rating.responded_at = timezone.now()
        rating.save()
        
        return Response({
            'message': 'Response submitted successfully',
            'response_text': rating.response_text,
            'responded_at': rating.responded_at
        })
    
    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        """Flag a rating as inappropriate"""
        rating = self.get_object()
        
        # Can't flag your own rating
        if rating.reviewer == request.user:
            return Response(
                {'error': 'You cannot flag your own rating'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already flagged by this user
        if RatingFlag.objects.filter(rating=rating, flagged_by=request.user).exists():
            return Response(
                {'error': 'You have already flagged this rating'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create flag
        flag_serializer = RatingFlagSerializer(
            data=request.data,
            context={'request': request}
        )
        flag_serializer.is_valid(raise_exception=True)
        flag_serializer.save(rating=rating)
        
        return Response(flag_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add comment to rating"""
        rating = self.get_object()
        
        comment_serializer = RatingCommentSerializer(
            data=request.data,
            context={'request': request}
        )
        comment_serializer.is_valid(raise_exception=True)
        comment_serializer.save(rating=rating)
        
        return Response(comment_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def my_ratings(self, request):
        """Get ratings received by current user"""
        ratings = Rating.objects.filter(reviewee=request.user, is_public=True)
        
        # Filter by type
        rating_type = request.query_params.get('rating_type')
        if rating_type:
            ratings = ratings.filter(rating_type=rating_type)
        
        page = self.paginate_queryset(ratings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get reviews written by current user"""
        reviews = Rating.objects.filter(reviewer=request.user)
        
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get contracts pending rating by current user"""
        from contracts.models import Contract
        
        completed_contracts = Contract.objects.filter(
            status='COMPLETED'
        ).filter(
            Q(employer=request.user) | Q(worker=request.user)
        )
        
        # Filter out already rated contracts
        rated_contract_ids = Rating.objects.filter(
            reviewer=request.user
        ).values_list('contract_id', flat=True)
        
        pending = completed_contracts.exclude(id__in=rated_contract_ids)
        
        from contracts.serializers import ContractSerializer
        serializer = ContractSerializer(pending, many=True, context={'request': request})
        
        return Response({
            'count': pending.count(),
            'contracts': serializer.data
        })


class RatingSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """Rating summary viewset"""
    
    queryset = RatingSummary.objects.all()
    serializer_class = RatingSummarySerializer
    permission_classes = [permissions.AllowAny]
    
    def get_object(self):
        """Get summary for a specific user"""
        if self.kwargs.get('pk') == 'me':
            user = self.request.user
            if not user.is_authenticated:
                from rest_framework.exceptions import NotAuthenticated
                raise NotAuthenticated('Authentication required')
        else:
            user = get_object_or_404(User, id=self.kwargs.get('pk'))
        
        summary, created = RatingSummary.objects.get_or_create(user=user)
        if not created:
            summary.update()  # Refresh data
        return summary
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def public(self, request):
        """Get public rating summary for a worker"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = get_object_or_404(User, id=user_id, user_type='WORKER')
        summary, created = RatingSummary.objects.get_or_create(user=user)
        if not created:
            summary.update()
        
        serializer = self.get_serializer(summary)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def top_workers(self, request):
        """Get top rated workers"""
        limit = int(request.query_params.get('limit', 10))
        
        summaries = RatingSummary.objects.filter(
            user__user_type='WORKER',
            total_ratings__gte=3  # Minimum 3 ratings
        ).order_by('-average_rating')[:limit]
        
        serializer = self.get_serializer(summaries, many=True)
        return Response(serializer.data)


class RatingCommentViewSet(viewsets.ModelViewSet):
    """Rating comment management"""
    
    serializer_class = RatingCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RatingComment.objects.filter(rating__is_public=True)
    
    def perform_update(self, serializer):
        serializer.save(is_edited=True, edited_at=timezone.now())
    
    def perform_destroy(self, instance):
        # Only comment owner or admin can delete
        if instance.user == self.request.user or self.request.user.user_type == 'ADMIN':
            instance.delete()
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not have permission to delete this comment')


class RatingFlagViewSet(viewsets.ModelViewSet):
    """Rating flag management (admin only)"""
    
    queryset = RatingFlag.objects.all()
    serializer_class = RatingFlagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reason', 'reviewed_by']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'ADMIN' or user.is_staff:
            return RatingFlag.objects.all()
        return RatingFlag.objects.filter(flagged_by=user)
    
    def get_permissions(self):
        if self.action in ['resolve', 'list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a flag (admin only)"""
        flag = self.get_object()
        
        serializer = RatingFlagResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        
        action_text = {
            'dismiss': 'Flag dismissed - no action taken',
            'warn': 'User warned',
            'remove': 'Rating removed from public view'
        }
        
        flag.resolve(
            admin_user=request.user,
            action=f"{action_text[action]}. {notes}".strip()
        )
        
        return Response({
            'message': f'Flag resolved with action: {action}',
            'action_taken': flag.action_taken
        })
