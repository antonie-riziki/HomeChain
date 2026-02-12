import { useQuery } from '@tanstack/react-query';
import { jobService } from '@/services';
import DashboardLayout from '@/components/common/DashboardLayout';
import JobCard from '@/components/common/JobCard';
import { Loader2, Bookmark } from 'lucide-react';

export default function SavedJobs() {
    const { data: jobs, isLoading, refetch } = useQuery({
        queryKey: ['saved-jobs'],
        queryFn: () => jobService.getSavedJobs().then(res => res.data),
    });

    if (isLoading) {
        return (
            <DashboardLayout>
                <div className="flex h-[400px] items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h1 className="font-heading text-2xl font-bold">Saved Jobs</h1>
                    <p className="text-muted-foreground">Jobs you have saved to apply for later.</p>
                </div>

                {jobs && jobs.length > 0 ? (
                    <div className="grid gap-4 md:grid-cols-2">
                        {jobs.map((job: any) => (
                            <JobCard
                                key={job.id}
                                id={job.id}
                                title={job.title}
                                description={job.description}
                                location={job.location}
                                budget={job.budget || job.hourly_rate_min}
                                budgetType={job.payment_type?.toLowerCase() === 'hourly' ? 'hourly' : 'fixed'}
                                skills={job.skills_required || []}
                                status={job.status?.toLowerCase() || 'open'}
                                createdAt={job.created_at ? new Date(job.created_at).toLocaleDateString() : 'Recent'}
                                employerName={job.employer_name}
                                onSaveToggle={() => refetch()}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center">
                        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                            <Bookmark className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <h3 className="font-heading text-lg font-semibold">No saved jobs</h3>
                        <p className="mx-auto max-w-[250px] text-sm text-muted-foreground">
                            You haven't saved any jobs yet. Browse jobs to find your next opportunity.
                        </p>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
