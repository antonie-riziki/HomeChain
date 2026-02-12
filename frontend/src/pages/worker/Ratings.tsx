import DashboardLayout from '@/components/common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import RatingStars from '@/components/common/RatingStars';
import { Progress } from '@/components/ui/progress';
import { useQuery } from '@tanstack/react-query';
import { ratingService } from '@/services';
import { Loader2, Star } from 'lucide-react';
import { format } from 'date-fns';

export default function WorkerRatings() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['my-ratings-summary'],
    queryFn: () => ratingService.getMyRatings().then(res => res.data),
  });

  const { data: reviews, isLoading: reviewsLoading } = useQuery({
    queryKey: ['my-reviews-list'],
    queryFn: () => ratingService.getMyReviews().then(res => res.data),
  });

  const isLoading = summaryLoading || reviewsLoading;

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardLayout>
    );
  }

  const avgRating = summary?.average_rating || 0;
  const reviewCount = summary?.total_count || 0;
  const distribution = summary?.distribution || [];
  const criteriaBreakdown = summary?.criteria_breakdown || {};

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="font-heading text-2xl font-bold">My Ratings & Reviews</h1>

        {/* Summary */}
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="shadow-card">
            <CardContent className="p-6 flex items-center gap-6">
              <div className="text-center">
                <p className="font-heading text-5xl font-bold">{avgRating.toFixed(1)}</p>
                <RatingStars rating={avgRating} size="md" />
                <p className="text-xs text-muted-foreground mt-1">{reviewCount} reviews</p>
              </div>
              <div className="flex-1 space-y-2">
                {[5, 4, 3, 2, 1].map(stars => {
                  const d = distribution.find((item: any) => item.stars === stars) || { count: 0, percentage: 0 };
                  return (
                    <div key={stars} className="flex items-center gap-2">
                      <span className="w-8 text-xs text-right text-muted-foreground">{stars}★</span>
                      <Progress value={d.percentage} className="h-2 flex-1" />
                      <span className="w-6 text-xs text-muted-foreground">{d.count}</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-card">
            <CardContent className="p-6">
              <h3 className="font-heading text-sm font-semibold mb-4">Average by Criteria</h3>
              <div className="space-y-3">
                {Object.entries(criteriaBreakdown).map(([key, value]: [string, any]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground capitalize">{key.replace('_', ' ')}</span>
                    <div className="flex items-center gap-2">
                      <Progress value={(value / 5) * 100} className="h-2 w-24" />
                      <span className="text-sm font-medium w-8">{Number(value).toFixed(1)}</span>
                    </div>
                  </div>
                ))}
                {Object.keys(criteriaBreakdown).length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">No criteria data available.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Reviews */}
        <div className="space-y-4">
          <h3 className="font-heading text-sm font-semibold">Recent Reviews</h3>
          {reviews?.map((r: any) => (
            <Card key={r.id} className="shadow-card">
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-heading text-sm font-semibold">{r.reviewer_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {r.contract_title || 'Contract'} · {r.created_at ? format(new Date(r.created_at), 'MMM dd, yyyy') : 'N/A'}
                    </p>
                  </div>
                  <RatingStars rating={r.rating} size="sm" />
                </div>
                <p className="text-sm text-muted-foreground">{r.comment}</p>
              </CardContent>
            </Card>
          ))}
          {(!reviews || reviews.length === 0) && (
            <div className="py-12 text-center bg-muted/20 rounded-xl border border-dashed border-border">
              <Star className="h-8 w-8 text-muted-foreground mx-auto mb-2 opacity-50" />
              <p className="text-sm text-muted-foreground">No reviews yet.</p>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

