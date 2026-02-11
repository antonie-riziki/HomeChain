from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Job, JobApplication, JobSaved
from .serializers import *
from .permissions import *
from .filters import JobFilter

class JobViewSet(viewsets.ModelViewSet):
    """Job posting viewset"""
    
    queryset = Job.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = JobFilter
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['budget', 'created_at', 'estimated_duration']
    
    def get_serializer_class(self):
        """Return different serializers for different actions"""
        if self.action == 'create':
            return JobCreateUpdateSerializer
        elif self.action in ['update', 'partial_update']:
            return JobCreateUpdateSerializer
        elif self.action == 'retrieve':
            return JobDetailSerializer
        elif self.action == 'list' and self.request.user.user_type == 'WORKER':
            return JobPublicSerializer
        return JobSerializer
    
    def get_permissions(self):
        """Set custom permissions for different actions"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsEmployer]
        elif self.action in ['my_jobs', 'applications']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user type"""
        user = self.request.user
        
        if user.user_type == 'EMPLOYER':
            # Employers see their own jobs
            return Job.objects.filter(employer=user)
        
        elif user.user_type == 'WORKER':
            # Workers see OPEN jobs + their assigned jobs
            return Job.objects.filter(
                Q(status='OPEN') |
                Q(worker=user)
            ).distinct()
        
        # Admins see all
        return Job.objects.all()
    
    def perform_create(self, serializer):
        """Set employer on job creation"""
        serializer.save(employer=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish job (make open for applications)"""
        job = self.get_object()
        
        # Check permission
        if job.employer != request.user:
            return Response(
                {'error': 'Only the job owner can publish this job'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already published
        if job.status != 'DRAFT':
            return Response(
                {'error': f'Job is already {job.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.publish()
        
        return Response({
            'message': 'Job published successfully',
            'status': job.status
        })
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply for a job (workers only)"""
        job = self.get_object()
        
        # Check if user is worker
        if request.user.user_type != 'WORKER':
            return Response(
                {'error': 'Only workers can apply for jobs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if job is open
        if job.status != 'OPEN':
            return Response(
                {'error': 'This job is not accepting applications'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already applied
        if JobApplication.objects.filter(job=job, worker=request.user).exists():
            return Response(
                {'error': 'You have already applied for this job'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create application
        serializer = JobApplicationSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(job=job)
        
        # Increment applications count
        job.applications_count += 1
        job.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """Get all applications for a job (employer only)"""
        job = self.get_object()
        
        # Check permission
        if job.employer != request.user and request.user.user_type != 'ADMIN':
            return Response(
                {'error': 'Only the job owner can view applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        applications = job.applications.all()
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            applications = applications.filter(status=status_filter.upper())
        
        # Order by rating and experience
        ordering = request.query_params.get('ordering', '-worker_rating')
        applications = applications.order_by(ordering)
        
        page = self.paginate_queryset(applications)
        if page is not None:
            serializer = JobApplicationDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = JobApplicationDetailSerializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def shortlist(self, request, pk=None):
        """Shortlist an application (employer only)"""
        job = self.get_object()
        
        if job.employer != request.user:
            return Response(
                {'error': 'Only the job owner can shortlist applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        application_id = request.data.get('application_id')
        application = get_object_or_404(JobApplication, id=application_id, job=job)
        
        application.shortlist()
        
        return Response({
            'message': 'Application shortlisted',
            'status': application.status
        })
    
    @action(detail=True, methods=['post'])
    def accept_application(self, request, pk=None):
        """Accept an application and assign worker"""
        job = self.get_object()
        
        if job.employer != request.user:
            return Response(
                {'error': 'Only the job owner can accept applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if job.status != 'OPEN':
            return Response(
                {'error': f'Job is {job.get_status_display()}, cannot accept applications'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application_id = request.data.get('application_id')
        application = get_object_or_404(JobApplication, id=application_id, job=job)
        
        application.accept()
        
        return Response({
            'message': f'Worker {application.worker.full_name} assigned successfully',
            'job_status': job.status,
            'application_status': application.status
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark job as completed"""
        job = self.get_object()
        
        # Only employer or assigned worker can mark complete
        if request.user not in [job.employer, job.worker]:
            return Response(
                {'error': 'Unauthorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if job.status != 'IN_PROGRESS':
            return Response(
                {'error': f'Job is {job.get_status_display()}, cannot complete'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.complete()
        
        return Response({
            'message': 'Job marked as completed',
            'status': job.status
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel job"""
        job = self.get_object()
        
        if job.employer != request.user:
            return Response(
                {'error': 'Only the job owner can cancel this job'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if job.status in ['COMPLETED', 'CANCELLED']:
            return Response(
                {'error': f'Job is already {job.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.cancel()
        
        return Response({
            'message': 'Job cancelled',
            'status': job.status
        })
    
    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        """Save job for later (workers only)"""
        job = self.get_object()
        
        if request.user.user_type != 'WORKER':
            return Response(
                {'error': 'Only workers can save jobs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        saved, created = JobSaved.objects.get_or_create(
            worker=request.user,
            job=job
        )
        
        if created:
            return Response({
                'message': 'Job saved successfully'
            })
        else:
            return Response({
                'message': 'Job already saved'
            })
    
    @action(detail=True, methods=['post'])
    def unsave(self, request, pk=None):
        """Remove saved job"""
        job = self.get_object()
        
        JobSaved.objects.filter(worker=request.user, job=job).delete()
        
        return Response({
            'message': 'Job removed from saved'
        })
    
    @action(detail=False, methods=['get'])
    def my_jobs(self, request):
        """Get jobs based on user type"""
        user = request.user
        
        if user.user_type == 'EMPLOYER':
            jobs = Job.objects.filter(employer=user)
            serializer = JobSerializer(jobs, many=True)
        elif user.user_type == 'WORKER':
            # Jobs assigned to worker
            jobs = Job.objects.filter(worker=user)
            serializer = JobPublicSerializer(jobs, many=True)
        else:
            return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def saved(self, request):
        """Get saved jobs for worker"""
        if request.user.user_type != 'WORKER':
            return Response(
                {'error': 'Only workers have saved jobs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        saved_jobs = JobSaved.objects.filter(worker=request.user)
        jobs = [saved.job for saved in saved_jobs]
        
        serializer = JobPublicSerializer(jobs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def browse(self, request):
        """Browse open jobs (public)"""
        jobs = Job.objects.filter(status='OPEN').order_by('-is_featured', '-created_at')
        
        # Apply filters
        filterset = JobFilter(request.GET, queryset=jobs)
        if filterset.is_valid():
            jobs = filterset.qs
        
        # Pagination
        page = self.paginate_queryset(jobs)
        if page is not None:
            serializer = JobPublicSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = JobPublicSerializer(jobs, many=True)
        return Response(serializer.data)


class JobApplicationViewSet(viewsets.ModelViewSet):
    """Job application viewset"""
    
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'WORKER':
            # Workers see their own applications
            return JobApplication.objects.filter(worker=user)
        elif user.user_type == 'EMPLOYER':
            # Employers see applications for their jobs
            return JobApplication.objects.filter(job__employer=user)
        
        return JobApplication.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return JobApplicationDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return JobApplicationUpdateSerializer
        return JobApplicationSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsJobOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw application (worker only)"""
        application = self.get_object()
        
        if application.worker != request.user:
            return Response(
                {'error': 'You can only withdraw your own applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if application.status not in ['PENDING', 'SHORTLISTED']:
            return Response(
                {'error': f'Cannot withdraw application with status {application.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.withdraw()
        
        # Decrement job applications count
        job = application.job
        job.applications_count -= 1
        job.save()
        
        return Response({
            'message': 'Application withdrawn successfully'
        })
