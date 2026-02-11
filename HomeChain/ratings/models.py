from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import User
from contracts.models import Contract

class Rating(models.Model):
    """Ratings and reviews between employers and workers"""
    
    RATING_TYPES = (
        ('EMPLOYER_TO_WORKER', 'Employer Rating Worker'),
        ('WORKER_TO_EMPLOYER', 'Worker Rating Employer'),
    )
    
    # Relations
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='ratings_given'
    )
    reviewee = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='ratings_received'
    )
    
    # Rating type
    rating_type = models.CharField(max_length=30, choices=RATING_TYPES)
    
    # Ratings (1-5)
    communication_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Communication skills"
    )
    professionalism_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Professionalism and reliability"
    )
    quality_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Quality of work"
    )
    punctuality_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Punctuality and timeliness"
    )
    
    # Overall rating (auto-calculated)
    overall_rating = models.FloatField(default=0.0)
    
    # Review
    review_text = models.TextField(max_length=1000, blank=True)
    pros = models.TextField(max_length=500, blank=True, help_text="What went well")
    cons = models.TextField(max_length=500, blank=True, help_text="What could be improved")
    
    # Would recommend / hire again
    would_recommend = models.BooleanField(default=True)
    
    # Response from reviewee
    response_text = models.TextField(max_length=1000, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_public = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ratings'
        ordering = ['-created_at']
        unique_together = ['contract', 'reviewer']  # One rating per contract per user
        indexes = [
            models.Index(fields=['reviewee', 'overall_rating']),
            models.Index(fields=['contract', 'rating_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Rating by {self.reviewer.full_name} for {self.reviewee.full_name} - {self.overall_rating}⭐"
    
    def save(self, *args, **kwargs):
        # Calculate overall rating
        ratings = [
            self.communication_rating,
            self.professionalism_rating,
            self.quality_rating,
            self.punctuality_rating
        ]
        self.overall_rating = sum(ratings) / len(ratings)
        super().save(*args, **kwargs)
    
    @property
    def average_rating(self):
        return self.overall_rating


class RatingSummary(models.Model):
    """Cached rating summaries for users"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='rating_summary'
    )
    
    # As reviewee (worker or employer)
    total_ratings = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    
    # Breakdown
    communication_avg = models.FloatField(default=0.0)
    professionalism_avg = models.FloatField(default=0.0)
    quality_avg = models.FloatField(default=0.0)
    punctuality_avg = models.FloatField(default=0.0)
    
    # Recommendation rate
    recommendation_rate = models.FloatField(default=0.0)  # Percentage
    
    # Rating distribution
    rating_5_count = models.IntegerField(default=0)
    rating_4_count = models.IntegerField(default=0)
    rating_3_count = models.IntegerField(default=0)
    rating_2_count = models.IntegerField(default=0)
    rating_1_count = models.IntegerField(default=0)
    
    # As reviewer
    total_reviews_given = models.IntegerField(default=0)
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rating_summaries'
    
    def __str__(self):
        return f"Rating summary for {self.user.full_name} - {self.average_rating}⭐ ({self.total_ratings} ratings)"
    
    def update(self):
        """Update rating summary from all ratings"""
        ratings = Rating.objects.filter(
            reviewee=self.user,
            is_public=True,
            is_flagged=False
        )
        
        self.total_ratings = ratings.count()
        
        if self.total_ratings > 0:
            # Overall average
            self.average_rating = ratings.aggregate(
                avg=models.Avg('overall_rating')
            )['avg'] or 0.0
            
            # Category averages
            self.communication_avg = ratings.aggregate(
                avg=models.Avg('communication_rating')
            )['avg'] or 0.0
            
            self.professionalism_avg = ratings.aggregate(
                avg=models.Avg('professionalism_rating')
            )['avg'] or 0.0
            
            self.quality_avg = ratings.aggregate(
                avg=models.Avg('quality_rating')
            )['avg'] or 0.0
            
            self.punctuality_avg = ratings.aggregate(
                avg=models.Avg('punctuality_rating')
            )['avg'] or 0.0
            
            # Recommendation rate
            recommend_count = ratings.filter(would_recommend=True).count()
            self.recommendation_rate = (recommend_count / self.total_ratings) * 100
            
            # Rating distribution
            self.rating_5_count = ratings.filter(overall_rating__gte=4.5).count()
            self.rating_4_count = ratings.filter(overall_rating__gte=3.5, overall_rating__lt=4.5).count()
            self.rating_3_count = ratings.filter(overall_rating__gte=2.5, overall_rating__lt=3.5).count()
            self.rating_2_count = ratings.filter(overall_rating__gte=1.5, overall_rating__lt=2.5).count()
            self.rating_1_count = ratings.filter(overall_rating__lt=1.5).count()
        
        # Reviews given
        self.total_reviews_given = Rating.objects.filter(reviewer=self.user).count()
        
        self.save()


class RatingComment(models.Model):
    """Comments on ratings (public discussions)"""
    
    rating = models.ForeignKey(
        Rating, 
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='rating_comments'
    )
    
    comment = models.TextField(max_length=500)
    
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rating_comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.full_name} on rating {self.rating.id}"


class RatingFlag(models.Model):
    """Flag inappropriate ratings"""
    
    FLAG_REASONS = (
        ('INAPPROPRIATE', 'Inappropriate content'),
        ('FAKE', 'Fake review'),
        ('OFFENSIVE', 'Offensive language'),
        ('IRRELEVANT', 'Irrelevant content'),
        ('OTHER', 'Other'),
    )
    
    rating = models.ForeignKey(
        Rating, 
        on_delete=models.CASCADE,
        related_name='flags'
    )
    flagged_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='rating_flags'
    )
    
    reason = models.CharField(max_length=20, choices=FLAG_REASONS)
    description = models.TextField(max_length=500)
    
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='reviewed_flags'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rating_flags'
        unique_together = ['rating', 'flagged_by']  # One flag per user per rating
    
    def __str__(self):
        return f"Flag on rating {self.rating.id} by {self.flagged_by.full_name}"
    
    def resolve(self, admin_user, action):
        """Resolve flag"""
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.action_taken = action
        self.save()
        
        # If action is to remove rating
        if 'remove' in action.lower():
            self.rating.is_flagged = True
            self.rating.flag_reason = self.description
            self.rating.is_public = False
            self.rating.save()