from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import User, Skill, WorkerSkill, WorkerDocument, VerificationRequest
from .serializers import *

# ============ AUTH VIEWS ============

class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User login endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Successfully logged out"},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============ USER VIEWS ============

class UserViewSet(viewsets.ModelViewSet):
    """User management viewset"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_type', 'is_verified', 'is_available']
    search_fields = ['full_name', 'email', 'username', 'location']
    ordering_fields = ['created_at', 'average_rating', 'completed_jobs']
    
    def get_queryset(self):
        user = self.request.user
        
        # Employers see all verified workers
        if user.user_type == 'EMPLOYER':
            return User.objects.filter(
                user_type='WORKER',
                is_verified=True,
                is_active=True
            )
        
        # Workers see their own profile only
        elif user.user_type == 'WORKER':
            return User.objects.filter(id=user.id)
        
        # Admins see all users
        elif user.user_type == 'ADMIN' or user.is_staff:
            return User.objects.all()
        
        return User.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'list' and self.request.user.user_type == 'EMPLOYER':
            return WorkerPublicSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def workers(self, request):
        """Public endpoint to list all available workers"""
        workers = User.objects.filter(
            user_type='WORKER',
            is_verified=True,
            is_available=True,
            is_active=True
        )
        
        # Filter by skill
        skill = request.query_params.get('skill')
        if skill:
            workers = workers.filter(skills__contains=[skill])
        
        # Filter by multiple skills
        skills = request.query_params.getlist('skills')
        if skills:
            for skill in skills:
                workers = workers.filter(skills__contains=[skill])
        
        # Filter by location
        location = request.query_params.get('location')
        if location:
            workers = workers.filter(location__icontains=location)
        
        # Filter by min rating
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            workers = workers.filter(average_rating__gte=float(min_rating))
        
        # Filter by max hourly rate
        max_rate = request.query_params.get('max_rate')
        if max_rate:
            workers = workers.filter(hourly_rate__lte=float(max_rate))
        
        # Search by name
        search = request.query_params.get('search')
        if search:
            workers = workers.filter(full_name__icontains=search)
        
        # Pagination
        page = self.paginate_queryset(workers)
        if page is not None:
            serializer = WorkerPublicSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = WorkerPublicSerializer(workers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update current user's profile"""
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(UserSerializer(user).data)
    
    @action(detail=False, methods=['patch'])
    def toggle_availability(self, request):
        """Toggle worker availability"""
        if request.user.user_type != 'WORKER':
            return Response(
                {'error': 'Only workers can toggle availability'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        request.user.is_available = not request.user.is_available
        request.user.save()
        
        return Response({
            'is_available': request.user.is_available,
            'message': f"You are now {'available' if request.user.is_available else 'unavailable'} for work"
        })
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def public_profile(self, request, pk=None):
        """Get public profile of a worker"""
        worker = get_object_or_404(
            User,
            id=pk,
            user_type='WORKER',
            is_verified=True,
            is_active=True
        )
        serializer = WorkerPublicSerializer(worker)
        
        # Add additional data
        data = serializer.data
        data['skills_list'] = WorkerSkillSerializer(
            worker.worker_skills.filter(is_verified=True),
            many=True
        ).data
        
        return Response(data)


# ============ SKILL VIEWS ============

class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    """View all available skills"""
    queryset = Skill.objects.filter(is_active=True)
    serializer_class = SkillSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'category']
    ordering_fields = ['name', 'category']
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all skill categories"""
        categories = Skill.objects.filter(
            is_active=True
        ).values_list(
            'category', flat=True
        ).distinct().order_by('category')
        
        return Response(list(categories))
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get skills grouped by category"""
        category = request.query_params.get('category')
        if category:
            skills = self.get_queryset().filter(category=category)
        else:
            skills = self.get_queryset()
        
        serializer = self.get_serializer(skills, many=True)
        return Response(serializer.data)


# ============ WORKER SKILL VIEWS ============

class WorkerSkillViewSet(viewsets.ModelViewSet):
    """Manage worker skills"""
    serializer_class = WorkerSkillSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'WORKER':
            return WorkerSkill.objects.filter(worker=self.request.user)
        return WorkerSkill.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(worker=self.request.user)
    
    def perform_update(self, serializer):
        if self.request.user.user_type == 'WORKER':
            serializer.save()
    
    def perform_destroy(self, instance):
        if self.request.user.user_type == 'WORKER':
            instance.delete()


# ============ WORKER DOCUMENT VIEWS ============

class WorkerDocumentViewSet(viewsets.ModelViewSet):
    """Manage worker documents"""
    serializer_class = WorkerDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'WORKER':
            return WorkerDocument.objects.filter(worker=self.request.user)
        return WorkerDocument.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(worker=self.request.user)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download document file"""
        document = self.get_object()
        
        if not document.document_file:
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return file URL
        return Response({
            'file_url': document.document_file.url,
            'file_name': document.file_name,
            'mime_type': document.mime_type
        })


# ============ VERIFICATION VIEWS ============

class VerificationRequestViewSet(viewsets.ModelViewSet):
    """Verification request management"""
    serializer_class = VerificationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'WORKER':
            return VerificationRequest.objects.filter(worker=user)
        elif user.user_type == 'ADMIN' or user.is_staff:
            return VerificationRequest.objects.all()
        
        return VerificationRequest.objects.none()
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """Approve verification request (admin only)"""
        verification_request = self.get_object()
        
        if verification_request.status != 'PENDING':
            return Response(
                {'error': 'This request has already been processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update request status
        verification_request.status = 'APPROVED'
        verification_request.reviewed_by = request.user
        verification_request.reviewed_at = timezone.now()
        verification_request.admin_notes = request.data.get('admin_notes', '')
        verification_request.save()
        
        # Verify all documents
        verification_request.documents.update(
            is_verified=True,
            verified_by=request.user,
            verified_at=timezone.now()
        )
        
        # Verify worker
        worker = verification_request.worker
        worker.is_verified = True
        worker.save()
        
        return Response({'message': 'Verification request approved'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        """Reject verification request (admin only)"""
        verification_request = self.get_object()
        
        if verification_request.status != 'PENDING':
            return Response(
                {'error': 'This request has already been processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        
        # Update request status
        verification_request.status = 'REJECTED'
        verification_request.reviewed_by = request.user
        verification_request.reviewed_at = timezone.now()
        verification_request.admin_notes = rejection_reason
        verification_request.save()
        
        return Response({'message': 'Verification request rejected'})


# ============ PROFILE VIEW ============

class ProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def patch(self, request, *args, **kwargs):
        """Partial update of user profile"""
        return self.partial_update(request, *args, **kwargs)
