from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Rating, RatingSummary, RatingComment, RatingFlag

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'contract_link', 'reviewer_link', 'reviewee_link',
        'overall_rating', 'would_recommend', 'is_public', 'created_at'
    ]
    list_filter = ['rating_type', 'overall_rating', 'would_recommend', 'is_public', 'is_flagged']
    search_fields = ['review_text', 'reviewer__full_name', 'reviewee__full_name']
    list_editable = ['is_public', 'would_recommend']
    readonly_fields = ['overall_rating', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Contract', {
            'fields': ('contract',)
        }),
        ('Parties', {
            'fields': ('reviewer', 'reviewee', 'rating_type')
        }),
        ('Ratings', {
            'fields': ('communication_rating', 'professionalism_rating',
                      'quality_rating', 'punctuality_rating', 'overall_rating')
        }),
        ('Review', {
            'fields': ('review_text', 'pros', 'cons', 'would_recommend')
        }),
        ('Response', {
            'fields': ('response_text', 'responded_at'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_public', 'is_flagged', 'flag_reason')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def contract_link(self, obj):
        url = reverse('admin:contracts_contract_change', args=[obj.contract.id])
        return format_html('<a href="{}">{}</a>', url, obj.contract.job.title)
    contract_link.short_description = 'Contract'
    
    def reviewer_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.reviewer.id])
        return format_html('<a href="{}">{}</a>', url, obj.reviewer.full_name)
    reviewer_link.short_description = 'Reviewer'
    
    def reviewee_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.reviewee.id])
        return format_html('<a href="{}">{}</a>', url, obj.reviewee.full_name)
    reviewee_link.short_description = 'Reviewee'
    
    actions = ['make_public', 'make_private', 'flag_ratings']
    
    def make_public(self, request, queryset):
        queryset.update(is_public=True)
        self.message_user(request, f"{queryset.count()} ratings made public.")
    make_public.short_description = "Make selected ratings public"
    
    def make_private(self, request, queryset):
        queryset.update(is_public=False)
        self.message_user(request, f"{queryset.count()} ratings made private.")
    make_private.short_description = "Make selected ratings private"
    
    def flag_ratings(self, request, queryset):
        queryset.update(is_flagged=True, is_public=False)
        self.message_user(request, f"{queryset.count()} ratings flagged.")
    flag_ratings.short_description = "Flag selected ratings"


@admin.register(RatingSummary)
class RatingSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'total_ratings', 'average_rating',
        'communication_avg', 'professionalism_avg', 'quality_avg',
        'recommendation_rate', 'updated_at'
    ]
    search_fields = ['user__full_name', 'user__email']
    readonly_fields = ['updated_at']
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.full_name)
    user_link.short_description = 'User'
    
    actions = ['refresh_summaries']
    
    def refresh_summaries(self, request, queryset):
        for summary in queryset:
            summary.update()
        self.message_user(request, f"{queryset.count()} summaries refreshed.")
    refresh_summaries.short_description = "Refresh selected summaries"


@admin.register(RatingComment)
class RatingCommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'rating_link', 'user_link', 'comment_short', 'created_at']
    list_filter = ['created_at', 'is_edited']
    search_fields = ['comment', 'user__full_name']
    
    def rating_link(self, obj):
        url = reverse('admin:ratings_rating_change', args=[obj.rating.id])
        return format_html('<a href="{}">Rating #{}</a>', url, obj.rating.id)
    rating_link.short_description = 'Rating'
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.full_name)
    user_link.short_description = 'User'
    
    def comment_short(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_short.short_description = 'Comment'


@admin.register(RatingFlag)
class RatingFlagAdmin(admin.ModelAdmin):
    list_display = ['id', 'rating_link', 'flagged_by_link', 'reason', 'reviewed_by', 'created_at']
    list_filter = ['reason', 'reviewed_by']
    search_fields = ['rating__review_text', 'flagged_by__full_name']
    
    def rating_link(self, obj):
        url = reverse('admin:ratings_rating_change', args=[obj.rating.id])
        return format_html('<a href="{}">Rating #{}</a>', url, obj.rating.id)
    rating_link.short_description = 'Rating'
    
    def flagged_by_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.flagged_by.id])
        return format_html('<a href="{}">{}</a>', url, obj.flagged_by.full_name)
    flagged_by_link.short_description = 'Flagged By'
    
    actions = ['resolve_flags']
    
    def resolve_flags(self, request, queryset):
        for flag in queryset:
            if not flag.reviewed_by:
                flag.resolve(request.user, "Bulk resolved via admin")
        self.message_user(request, f"{queryset.count()} flags resolved.")
    resolve_flags.short_description = "Resolve selected flags"