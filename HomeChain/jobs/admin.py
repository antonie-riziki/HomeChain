from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Job, JobApplication, JobSaved, JobView

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'employer_link', 'worker_link', 'budget', 
        'status', 'applications_count', 'is_urgent', 'created_at'
    ]
    list_filter = ['status', 'payment_type', 'category', 'is_urgent', 'is_remote', 'experience_level']
    search_fields = ['title', 'description', 'employer__full_name', 'worker__full_name', 'location']
    readonly_fields = ['views_count', 'applications_count', 'shortlisted_count', 'created_at', 'updated_at']
    list_editable = ['status', 'is_urgent']
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('employer', 'worker', 'title', 'description', 'category')
        }),
        ('Requirements', {
            'fields': ('skills_required', 'experience_level', 'location', 'is_remote')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'estimated_duration')
        }),
        ('Payment', {
            'fields': ('payment_type', 'budget', 'hourly_rate_min', 'hourly_rate_max')
        }),
        ('Status', {
            'fields': ('status', 'is_urgent', 'is_featured')
        }),
        ('Tracking', {
            'fields': ('views_count', 'applications_count', 'shortlisted_count')
        }),
        ('Blockchain', {
            'fields': ('escrow_id', 'contract_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def employer_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.employer.id])
        return format_html('<a href="{}">{}</a>', url, obj.employer.full_name)
    employer_link.short_description = 'Employer'
    
    def worker_link(self, obj):
        if obj.worker:
            url = reverse('admin:accounts_user_change', args=[obj.worker.id])
            return format_html('<a href="{}">{}</a>', url, obj.worker.full_name)
        return '-'
    worker_link.short_description = 'Worker'
    
    actions = ['make_featured', 'mark_as_urgent', 'publish_jobs']
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} jobs marked as featured.")
    make_featured.short_description = "Mark selected jobs as featured"
    
    def mark_as_urgent(self, request, queryset):
        queryset.update(is_urgent=True)
        self.message_user(request, f"{queryset.count()} jobs marked as urgent.")
    mark_as_urgent.short_description = "Mark selected jobs as urgent"
    
    def publish_jobs(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='OPEN', published_at=timezone.now())
        self.message_user(request, f"{queryset.count()} jobs published.")
    publish_jobs.short_description = "Publish selected jobs"


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'job_link', 'worker_link', 'proposed_rate', 
        'estimated_days', 'status', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['job__title', 'worker__full_name', 'cover_letter']
    readonly_fields = ['created_at', 'updated_at', 'worker_rating', 'worker_completed_jobs']
    list_editable = ['status']
    list_per_page = 25
    
    fieldsets = (
        ('Application Details', {
            'fields': ('job', 'worker', 'cover_letter', 'proposed_rate', 'estimated_days')
        }),
        ('Worker Snapshot', {
            'fields': ('worker_rating', 'worker_completed_jobs', 'worker_hourly_rate'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'employer_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def job_link(self, obj):
        url = reverse('admin:jobs_job_change', args=[obj.job.id])
        return format_html('<a href="{}">{}</a>', url, obj.job.title)
    job_link.short_description = 'Job'
    
    def worker_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.worker.id])
        return format_html('<a href="{}">{}</a>', url, obj.worker.full_name)
    worker_link.short_description = 'Worker'
    
    actions = ['approve_applications', 'reject_applications', 'shortlist_applications']
    
    def approve_applications(self, request, queryset):
        queryset.update(status='ACCEPTED')
        self.message_user(request, f"{queryset.count()} applications approved.")
    approve_applications.short_description = "Accept selected applications"
    
    def reject_applications(self, request, queryset):
        queryset.update(status='REJECTED')
        self.message_user(request, f"{queryset.count()} applications rejected.")
    reject_applications.short_description = "Reject selected applications"
    
    def shortlist_applications(self, request, queryset):
        queryset.update(status='SHORTLISTED')
        self.message_user(request, f"{queryset.count()} applications shortlisted.")
    shortlist_applications.short_description = "Shortlist selected applications"


@admin.register(JobSaved)
class JobSavedAdmin(admin.ModelAdmin):
    list_display = ['worker_link', 'job_link', 'created_at']
    list_filter = ['created_at']
    search_fields = ['worker__full_name', 'job__title']
    readonly_fields = ['created_at']
    
    def worker_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.worker.id])
        return format_html('<a href="{}">{}</a>', url, obj.worker.full_name)
    worker_link.short_description = 'Worker'
    
    def job_link(self, obj):
        url = reverse('admin:jobs_job_change', args=[obj.job.id])
        return format_html('<a href="{}">{}</a>', url, obj.job.title)
    job_link.short_description = 'Job'


@admin.register(JobView)
class JobViewAdmin(admin.ModelAdmin):
    list_display = ['job_link', 'user_link', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['job__title', 'user__full_name', 'ip_address']
    readonly_fields = ['viewed_at']
    
    def job_link(self, obj):
        url = reverse('admin:jobs_job_change', args=[obj.job.id])
        return format_html('<a href="{}">{}</a>', url, obj.job.title)
    job_link.short_description = 'Job'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.full_name)
        return '-'
    user_link.short_description = 'User'