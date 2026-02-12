import { Link } from 'react-router-dom';
import { Briefcase, Wallet, Star, Send, ArrowRight, TrendingUp, Clock, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/common/DashboardLayout';
import StatusBadge from '@/components/common/StatusBadge';
import RatingStars from '@/components/common/RatingStars';
import { useQuery } from '@tanstack/react-query';
import { jobService, ratingService, paymentService } from '@/services';

export default function WorkerDashboard() {
  const { data: activeJobs, isLoading: jobsLoading } = useQuery({
    queryKey: ['my-active-jobs'],
    queryFn: () => jobService.getMyJobs().then(res => res.data),
  });

  const { data: applications, isLoading: appsLoading } = useQuery({
    queryKey: ['my-applications'],
    queryFn: () => jobService.getMyApplications().then(res => res.data),
  });

  const { data: recommendedJobs, isLoading: browseLoading } = useQuery({
    queryKey: ['browse-jobs-dashboard'],
    queryFn: () => jobService.browse().then(res => res.data.results || res.data),
  });

  const { data: wallet, isLoading: walletLoading } = useQuery({
    queryKey: ['my-wallet-worker'],
    queryFn: () => paymentService.getWallet().then(res => res.data),
  });

  const { data: ratings, isLoading: ratingsLoading } = useQuery({
    queryKey: ['my-ratings'],
    queryFn: () => ratingService.getMyRatings().then(res => res.data),
  });

  const isLoading = jobsLoading || appsLoading || browseLoading || walletLoading || ratingsLoading;

  const walletBalance = wallet?.balance
    ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(wallet.balance)
    : '$0.00';

  const avgRating = ratings?.average_rating || 0;
  const reviewCount = ratings?.total_count || 0;

  const statCards = [
    { label: 'Wallet Balance', value: walletBalance, icon: Wallet, change: 'Stellar USDC' },
    { label: 'Active Jobs', value: (activeJobs?.length || 0).toString(), icon: Briefcase, change: 'Ongoing tasks' },
    { label: 'Applications', value: (applications?.length || 0).toString(), icon: Send, change: `${applications?.filter((a: any) => a.status === 'PENDING').length || 0} pending` },
    { label: 'My Rating', value: avgRating.toFixed(1), icon: Star, change: `${reviewCount} reviews` },
  ];

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Welcome */}
        <div>
          <h1 className="font-heading text-2xl font-bold">Worker Dashboard</h1>
          <p className="text-sm text-muted-foreground">Track your jobs, earnings, and applications.</p>
        </div>

        {/* Stats */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {statCards.map(stat => (
            <Card key={stat.label} className="shadow-card">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-muted-foreground font-medium">{stat.label}</p>
                    <p className="font-heading text-2xl font-bold mt-1">{stat.value}</p>
                    <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1"><TrendingUp className="h-3 w-3" />{stat.change}</p>
                  </div>
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10">
                    <stat.icon className="h-5 w-5 text-primary" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Active Jobs */}
          <Card className="shadow-card">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="font-heading text-base font-semibold">Active Jobs</CardTitle>
              <Button variant="ghost" size="sm" asChild><Link to="/worker/contracts">View all <ArrowRight className="ml-1 h-3 w-3" /></Link></Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {activeJobs?.slice(0, 3).map((job: any) => (
                <div key={job.id} className="rounded-lg border border-border p-3">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium">{job.title}</p>
                    <StatusBadge status={job.status.toLowerCase()} />
                  </div>
                  <p className="text-xs text-muted-foreground">Employer: {job.employer_name || 'HomeChain'}</p>
                  <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1"><Clock className="h-3 w-3" /> {job.location || 'Remote'}</p>
                </div>
              ))}
              {(!activeJobs || activeJobs.length === 0) && (
                <p className="text-sm text-muted-foreground text-center py-4">No active jobs found.</p>
              )}
            </CardContent>
          </Card>

          {/* Recommended Jobs */}
          <Card className="shadow-card">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="font-heading text-base font-semibold">Recommended Jobs</CardTitle>
              <Button variant="ghost" size="sm" asChild><Link to="/worker/jobs/browse">Browse all <ArrowRight className="ml-1 h-3 w-3" /></Link></Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {recommendedJobs?.slice(0, 3).map((job: any) => (
                <div key={job.id} className="flex items-center justify-between rounded-lg border border-border p-3">
                  <div>
                    <p className="text-sm font-medium">{job.title}</p>
                    <p className="text-xs text-muted-foreground">{job.location} · {job.budget_display || `$${job.budget}`}</p>
                  </div>
                  <span className="text-xs text-muted-foreground">Open</span>
                </div>
              ))}
              {(!recommendedJobs || recommendedJobs.length === 0) && (
                <p className="text-sm text-muted-foreground text-center py-4">No recommended jobs yet.</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Rating Summary */}
        <Card className="shadow-card">
          <CardContent className="p-5">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-secondary/10">
                <Star className="h-7 w-7 text-secondary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Your Rating</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-heading text-2xl font-bold">{avgRating.toFixed(1)}</span>
                  <RatingStars rating={avgRating} />
                </div>
                <p className="text-xs text-muted-foreground mt-1">Based on {reviewCount} reviews</p>
              </div>
              <div className="ml-auto hidden sm:block">
                <Button variant="outline" size="sm" asChild><Link to="/worker/ratings">View Reviews</Link></Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

