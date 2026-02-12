import { Link } from 'react-router-dom';
import { Plus, Briefcase, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import DashboardLayout from '@/components/common/DashboardLayout';
import JobCard from '@/components/common/JobCard';
import EmptyState from '@/components/common/EmptyState';
import { useQuery } from '@tanstack/react-query';
import { jobService } from '@/services';

export default function EmployerJobs() {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ['my-jobs-list'],
    queryFn: () => jobService.getMyJobs().then(res => res.data),
  });

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
        <div className="flex items-center justify-between">
          <h1 className="font-heading text-2xl font-bold">My Jobs</h1>
          <Button asChild><Link to="/employer/jobs/create"><Plus className="mr-2 h-4 w-4" /> Post Job</Link></Button>
        </div>

        {!jobs || jobs.length === 0 ? (
          <EmptyState
            icon={<Briefcase className="h-12 w-12" />}
            title="No jobs yet"
            description="Post your first job to find qualified domestic workers."
            action={<Button asChild><Link to="/employer/jobs/create">Post a Job</Link></Button>}
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {jobs.map((job: any) => <JobCard key={job.id} {...job} />)}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

