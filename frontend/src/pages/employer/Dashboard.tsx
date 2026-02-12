import { Link } from 'react-router-dom';
import { Briefcase, Users, FileText, CreditCard, Plus, ArrowRight, TrendingUp, Clock, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/common/DashboardLayout';
import StatusBadge from '@/components/common/StatusBadge';
import { useQuery } from '@tanstack/react-query';
import { jobService, contractService, paymentService } from '@/services';
import { formatDistanceToNow } from 'date-fns';

export default function EmployerDashboard() {
  const { data: jobs, isLoading: jobsLoading } = useQuery({
    queryKey: ['my-jobs'],
    queryFn: () => jobService.getMyJobs().then(res => res.data),
  });

  const { data: applications, isLoading: appsLoading } = useQuery({
    queryKey: ['my-received-applications'],
    queryFn: () => jobService.getMyApplications().then(res => res.data),
  });

  const { data: contracts, isLoading: contractsLoading } = useQuery({
    queryKey: ['my-contracts'],
    queryFn: () => contractService.getContracts().then(res => res.data),
  });

  const { data: wallet, isLoading: walletLoading } = useQuery({
    queryKey: ['my-wallet'],
    queryFn: () => paymentService.getWallet().then(res => res.data),
  });

  const isLoading = jobsLoading || appsLoading || contractsLoading || walletLoading;

  const activeJobsCount = jobs?.filter((j: any) => j.status === 'OPEN' || j.status === 'IN_PROGRESS').length || 0;
  const pendingAppsCount = applications?.filter((a: any) => a.status === 'PENDING').length || 0;
  const activeContractsCount = contracts?.filter((c: any) => c.status === 'ACTIVE').length || 0;
  const totalSpentFormatted = wallet?.total_spent
    ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(wallet.total_spent)
    : '$0.00';

  const statCards = [
    { label: 'Active Jobs', value: activeJobsCount.toString(), icon: Briefcase, change: 'Running now' },
    { label: 'Applications', value: (applications?.length || 0).toString(), icon: Users, change: `${pendingAppsCount} pending` },
    { label: 'Contracts', value: (contracts?.length || 0).toString(), icon: FileText, change: `${activeContractsCount} active` },
    { label: 'Total Spent', value: totalSpentFormatted, icon: CreditCard, change: 'Lifetime total' },
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
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="font-heading text-2xl font-bold">Employee Dashboard</h1>
            <p className="text-sm text-muted-foreground">Manage your jobs, contracts, and payments.</p>
          </div>
          <Button asChild>
            <Link to="/employer/jobs/create"><Plus className="mr-2 h-4 w-4" /> Post New Job</Link>
          </Button>
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
          {/* Recent Jobs */}
          <Card className="shadow-card">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="font-heading text-base font-semibold">My Jobs</CardTitle>
              <Button variant="ghost" size="sm" asChild><Link to="/employer/jobs">View all <ArrowRight className="ml-1 h-3 w-3" /></Link></Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {jobs?.slice(0, 3).map((job: any) => (
                <div key={job.id} className="flex items-center justify-between rounded-lg border border-border p-3">
                  <div>
                    <p className="text-sm font-medium">{job.title}</p>
                    <p className="text-xs text-muted-foreground">{job.applications_count || 0} applications · {job.budget_display || `$${job.budget}`}</p>
                  </div>
                  <StatusBadge status={job.status.toLowerCase()} />
                </div>
              ))}
              {(!jobs || jobs.length === 0) && (
                <p className="text-sm text-muted-foreground text-center py-4">No jobs posted yet.</p>
              )}
            </CardContent>
          </Card>

          {/* Recent Applications */}
          <Card className="shadow-card">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="font-heading text-base font-semibold">Recent Applications</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {applications?.slice(0, 3).map((app: any) => (
                <div key={app.id} className="flex items-center justify-between rounded-lg border border-border p-3">
                  <div>
                    <p className="text-sm font-medium">{app.worker_name}</p>
                    <p className="text-xs text-muted-foreground">{app.job_title} · ${app.bid_amount || app.hourly_rate}</p>
                  </div>
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {formatDistanceToNow(new Date(app.created_at), { addSuffix: true })}
                  </span>
                </div>
              ))}
              {(!applications || applications.length === 0) && (
                <p className="text-sm text-muted-foreground text-center py-4">No applications received yet.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}

