from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Skill, WorkerSkill, WorkerDocument, VerificationRequest

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    
    list_display = ['username', 'email', 'full_name', 'user_type', 'phone', 'is_verified', 'is_active']
    list_filter = ['user_type', 'is_verified', 'is_available', 'is_active']
    search_fields = ['username', 'email', 'full_name', 'phone']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal Info'), {'fields': ('full_name', 'phone', 'location', 'profile_picture', 'bio')}),
        (_('User Type'), {'fields': ('user_type',)}),
        (_('Worker Details'), {'fields': ('skills', 'experience_years', 'hourly_rate', 'is_verified', 'is_available')}),
        (_('Employer Details'), {'fields': ('company_name', 'company_registration')}),
        (_('Stellar'), {'fields': ('stellar_public_key', 'stellar_secret_key')}),
        (_('Stats'), {'fields': ('completed_jobs', 'average_rating', 'total_earned', 'total_spent')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'user_type', 'password1', 'password2'),
        }),
    )

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'category']
    list_editable = ['is_active']

@admin.register(WorkerSkill)
class WorkerSkillAdmin(admin.ModelAdmin):
    list_display = ['worker', 'skill', 'proficiency', 'years_experience', 'is_verified']
    list_filter = ['proficiency', 'is_verified', 'skill']
    search_fields = ['worker__full_name', 'skill__name']
    list_editable = ['is_verified']

@admin.register(WorkerDocument)
class WorkerDocumentAdmin(admin.ModelAdmin):
    list_display = ['worker', 'document_type', 'title', 'is_verified', 'uploaded_at']
    list_filter = ['document_type', 'is_verified']
    search_fields = ['worker__full_name', 'title', 'document_number']
    list_editable = ['is_verified']

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ['worker', 'status', 'submitted_at', 'reviewed_at']
    list_filter = ['status']
    search_fields = ['worker__full_name']
    list_editable = ['status']