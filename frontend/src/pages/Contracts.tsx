import { FileText, Loader2, Download, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import DashboardLayout from '@/components/common/DashboardLayout';
import StatusBadge from '@/components/common/StatusBadge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contractService } from '@/services';
import { useAuth } from '@/context/AuthContext';
import { format } from 'date-fns';
import { toast } from 'sonner';

export default function ContractsPage() {
    const { user } = useAuth();
    const queryClient = useQueryClient();
    const isEmployer = user?.user_type === 'employer';

    const { data: contracts, isLoading, error } = useQuery({
        queryKey: ['contracts'],
        queryFn: () => contractService.getContracts().then(res => res.data),
        retry: 2,
        onError: (err: any) => {
            console.error('Failed to load contracts:', err);
        },
    });

    const signMutation = useMutation({
        mutationFn: (id: string) => contractService.signContract(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['contracts'] });
            toast.success('Contract signed successfully');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Failed to sign contract');
        },
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

    if (error) {
        return (
            <DashboardLayout>
                <div className="py-12 text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
                        <FileText className="h-8 w-8 text-destructive" />
                    </div>
                    <h3 className="font-medium text-lg">Failed to load contracts</h3>
                    <p className="text-muted-foreground mt-1">
                        Please try refreshing the page.
                    </p>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h1 className="font-heading text-2xl font-bold">Contracts</h1>
                    <p className="text-sm text-muted-foreground">
                        {isEmployer ? 'Manage agreements with your workers.' : 'Manage your service agreements.'}
                    </p>
                </div>

                <div className="space-y-4">
                    {contracts?.map((c: any) => {
                        const needsSignature = isEmployer ? !c.employer_signed : !c.worker_signed;
                        const otherParty = isEmployer ? c.worker_name : c.employer_name;

                        return (
                            <Card key={c.id} className="shadow-card">
                                <CardContent className="p-5">
                                    <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
                                        <div className="flex items-start gap-4">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                                <FileText className="h-5 w-5 text-primary" />
                                            </div>
                                            <div>
                                                <h3 className="font-heading text-sm font-semibold">{c.title || `Contract #${c.id}`}</h3>
                                                <p className="text-xs text-muted-foreground mt-0.5">
                                                    {isEmployer ? 'Worker' : 'Employer'}: {otherParty} · {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(c.payment_amount)}
                                                </p>
                                                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                                                    <Clock className="h-3 w-3" />
                                                    Started: {c.start_date ? format(new Date(c.start_date), 'MMM dd, yyyy') : 'TBD'}
                                                </p>
                                                {c.escrow_id && (
                                                    <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                                                        <span className="material-icons-round text-xs">verified_user</span>
                                                        Escrow: {c.escrow_id.substring(0, 8)}...
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3 self-end sm:self-center">
                                            <StatusBadge status={c.status.toLowerCase()} />
                                            {needsSignature && c.status === 'PENDING' && (
                                                <Button
                                                    size="sm"
                                                    onClick={() => signMutation.mutate(c.id)}
                                                    disabled={signMutation.isPending}
                                                >
                                                    {signMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                                    Sign Contract
                                                </Button>
                                            )}
                                            {c.status === 'ACTIVE' && (
                                                <Button variant="outline" size="sm" asChild>
                                                    <a href="#" onClick={(e) => {
                                                        e.preventDefault();
                                                        contractService.downloadPDF(c.id).then(res => {
                                                            const url = window.URL.createObjectURL(new Blob([res.data]));
                                                            const link = document.createElement('a');
                                                            link.href = url;
                                                            link.setAttribute('download', `contract_${c.id}.pdf`);
                                                            document.body.appendChild(link);
                                                            link.click();
                                                        });
                                                    }}>
                                                        <Download className="mr-2 h-4 w-4" />
                                                        PDF
                                                    </a>
                                                </Button>
                                            )}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })}

                    {(!contracts || contracts.length === 0) && (
                        <div className="py-12 text-center">
                            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                                <FileText className="h-8 w-8 text-muted-foreground" />
                            </div>
                            <h3 className="font-medium text-lg">No contracts found</h3>
                            <p className="text-muted-foreground mt-1">
                                Contracts are created once a job application is accepted.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}
