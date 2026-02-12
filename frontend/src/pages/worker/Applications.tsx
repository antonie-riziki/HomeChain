import { Link } from 'react-router-dom';
import { Briefcase, Clock, ArrowRight, Loader2, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/common/DashboardLayout';
import StatusBadge from '@/components/common/StatusBadge';
import { useQuery } from '@tanstack/react-query';
import { jobService } from '@/services';
import { formatDistanceToNow } from 'date-fns';

export default function WorkerApplications() {
    const { data: applications, isLoading } = useQuery({
        queryKey: ['my-applications-page'],
        queryFn: () => jobService.getMyApplications().then(res => res.data),
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
                <div>
                    <h1 className="font-heading text-2xl font-bold">My Applications</h1>
                    <p className="text-sm text-muted-foreground">Track jobs you've applied for.</p>
                </div>

                <Card className="shadow-card">
                    <CardHeader>
                        <CardTitle className="font-heading text-lg">Sent Applications</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {applications?.map((app: any) => (
                                <div key={app.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-border p-4 transition-colors hover:bg-muted/50">
                                    <div className="flex items-start gap-3">
                                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                                            <Briefcase className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="font-medium">{app.job_title}</h3>
                                            <p className="text-sm text-muted-foreground">{app.employer_name}</p>
                                            <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                                                <span className="flex items-center gap-1 font-medium text-foreground">
                                                    ${app.bid_amount || app.hourly_rate} bid
                                                </span>
                                                <span className="flex items-center gap-1">
                                                    <Clock className="h-3 w-3" />
                                                    Applied {formatDistanceToNow(new Date(app.created_at), { addSuffix: true })}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center justify-between sm:justify-end gap-3">
                                        <StatusBadge status={app.status.toLowerCase()} />
                                        <Button variant="ghost" size="sm" asChild>
                                            <Link to={`/browse-jobs`}>
                                                <ArrowRight className="h-4 w-4" />
                                            </Link>
                                        </Button>
                                    </div>
                                </div>
                            ))}

                            {(!applications || applications.length === 0) && (
                                <div className="py-12 text-center">
                                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                                        <Send className="h-8 w-8 text-muted-foreground" />
                                    </div>
                                    <h3 className="font-medium text-lg">No applications yet</h3>
                                    <p className="text-muted-foreground mt-1 max-w-sm mx-auto">
                                        You haven't applied for any jobs yet. Browse available jobs and start earning.
                                    </p>
                                    <Button className="mt-6" asChild>
                                        <Link to="/browse-jobs">Browse Jobs</Link>
                                    </Button>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}
