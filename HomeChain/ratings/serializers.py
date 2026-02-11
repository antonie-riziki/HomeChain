from rest_framework import serializers
from django.utils import timezone
from .models import Rating, RatingSummary, RatingComment, RatingFlag
from accounts.serializers import UserSerializer, WorkerPublicSerializer

class RatingSerializer(serializers.ModelSerializer):
    """Main Rating serializer"""
    
    reviewer_name = serializers.ReadOnlyField(source='reviewer.full_name')
    reviewer_profile_pic = serializers.ImageField(
        source='reviewer.profile_picture', 
        read_only=True
    )
    reviewee_name = serializers.ReadOnlyField(source='reviewee.full_name')
    contract_title = serializers.ReadOnlyField(source='contract.job.title')
    contract_completed_at = serializers.ReadOnlyField(source='contract.completed_at')
    
    class Meta:
        model = Rating
        fields = [
            'id', 'contract', 'contract_title', 'contract_completed_at',
            'reviewer', 'reviewer_name', 'reviewer_profile_pic',
            'reviewee', 'reviewee_name',
            'rating_type', 'communication_rating', 'professionalism_rating',
            'quality_rating', 'punctuality_rating', 'overall_rating',
            'review_text', 'pros', 'cons', 'would_recommend',
            'response_text', 'responded_at',
            'is_public', 'is_flagged', 'flag_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'reviewer', 'reviewee', 'overall_rating',
            'response_text', 'responded_at',
            'is_public', 'is_flagged', 'flag_reason',
            'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        contract = data.get('contract')
        user = self.context['request'].user
        
        # Check if contract is completed
        if contract.status != 'COMPLETED':
            raise serializers.ValidationError(
                'You can only rate completed contracts'
            )
        
        # Check if user is part of contract
        if user not in [contract.employer, contract.worker]:
            raise serializers.ValidationError(
                'You are not a party to this contract'
            )
        
        # Set rating type automatically
        if user == contract.employer:
            data['rating_type'] = 'EMPLOYER_TO_WORKER'
            data['reviewee'] = contract.worker
        else:
            data['rating_type'] = 'WORKER_TO_EMPLOYER'
            data['reviewee'] = contract.employer
        
        data['reviewer'] = user
        
        return data
    
    def create(self, validated_data):
        # Check if rating already exists
        if Rating.objects.filter(
            contract=validated_data['contract'],
            reviewer=validated_data['reviewer']
        ).exists():
            raise serializers.ValidationError(
                'You have already rated this contract'
            )
        
        return super().create(validated_data)


class RatingDetailSerializer(serializers.ModelSerializer):
    """Detailed rating serializer with comments"""
    
    reviewer = UserSerializer(read_only=True)
    reviewee = UserSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    
    class Meta:
        model = Rating
        fields = '__all__'
        depth = 1
    
    def get_comments(self, obj):
        comments = obj.comments.all()
        return RatingCommentSerializer(comments, many=True).data


class RatingResponseSerializer(serializers.Serializer):
    """Serializer for responding to a rating"""
    
    response_text = serializers.CharField(max_length=1000, required=True)
    
    def validate(self, data):
        rating = self.context['rating']
        user = self.context['request'].user
        
        # Check if user is the reviewee
        if rating.reviewee != user:
            raise serializers.ValidationError(
                'Only the person being rated can respond'
            )
        
        # Check if already responded
        if rating.response_text:
            raise serializers.ValidationError(
                'You have already responded to this rating'
            )
        
        return data


class RatingSummarySerializer(serializers.ModelSerializer):
    """Rating summary serializer"""
    
    user_name = serializers.ReadOnlyField(source='user.full_name')
    
    class Meta:
        model = RatingSummary
        fields = [
            'user', 'user_name', 'total_ratings', 'average_rating',
            'communication_avg', 'professionalism_avg', 'quality_avg', 'punctuality_avg',
            'recommendation_rate',
            'rating_5_count', 'rating_4_count', 'rating_3_count',
            'rating_2_count', 'rating_1_count',
            'total_reviews_given', 'updated_at'
        ]


class RatingCommentSerializer(serializers.ModelSerializer):
    """Rating comment serializer"""
    
    user_name = serializers.ReadOnlyField(source='user.full_name')
    user_profile_pic = serializers.ImageField(
        source='user.profile_picture', 
        read_only=True
    )
    
    class Meta:
        model = RatingComment
        fields = [
            'id', 'rating', 'user', 'user_name', 'user_profile_pic',
            'comment', 'is_edited', 'edited_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'is_edited', 'edited_at', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RatingFlagSerializer(serializers.ModelSerializer):
    """Rating flag serializer"""
    
    flagged_by_name = serializers.ReadOnlyField(source='flagged_by.full_name')
    
    class Meta:
        model = RatingFlag
        fields = [
            'id', 'rating', 'flagged_by', 'flagged_by_name',
            'reason', 'description', 'reviewed_by', 'reviewed_at',
            'action_taken', 'created_at'
        ]
        read_only_fields = ['flagged_by', 'reviewed_by', 'reviewed_at', 'action_taken', 'created_at']
    
    def create(self, validated_data):
        validated_data['flagged_by'] = self.context['request'].user
        return super().create(validated_data)


class RatingFlagResolveSerializer(serializers.Serializer):
    """Serializer for resolving flags (admin)"""
    
    action = serializers.ChoiceField(
        choices=['dismiss', 'warn', 'remove'],
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)