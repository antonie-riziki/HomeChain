import django_filters
from django.db.models import Q
from .models import Job

class JobFilter(django_filters.FilterSet):
    """Filter set for jobs"""
    
    min_budget = django_filters.NumberFilter(field_name='budget', lookup_expr='gte')
    max_budget = django_filters.NumberFilter(field_name='budget', lookup_expr='lte')
    
    skills = django_filters.CharFilter(method='filter_skills')
    location = django_filters.CharFilter(lookup_expr='icontains')
    
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    is_remote = django_filters.BooleanFilter()
    is_urgent = django_filters.BooleanFilter()
    
    class Meta:
        model = Job
        fields = [
            'category', 'experience_level', 'payment_type',
            'status', 'is_remote', 'is_urgent'
        ]
    
    def filter_skills(self, queryset, name, value):
        """Filter jobs that require specific skills"""
        skills = value.split(',')
        for skill in skills:
            queryset = queryset.filter(skills_required__contains=[skill.strip()])
        return queryset