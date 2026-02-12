import { CreditCard, ArrowUpRight, ArrowDownRight, Loader2 } from 'lucide-react';
import DashboardLayout from '@/components/common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import StatusBadge from '@/components/common/StatusBadge';
import { useQuery } from '@tanstack/react-query';
import { paymentService } from '@/services';
import { format } from 'date-fns';

export default function EmployerPayments() {
  const { data: wallet, isLoading: walletLoading } = useQuery({
    queryKey: ['my-wallet-employer'],
    queryFn: () => paymentService.getWallet().then(res => res.data),
  });

  const { data: escrows, isLoading: escrowsLoading } = useQuery({
    queryKey: ['my-escrows'],
    queryFn: () => paymentService.getEscrows().then(res => res.data),
  });

  const { data: transactions, isLoading: txLoading } = useQuery({
    queryKey: ['my-transactions-employer'],
    queryFn: () => paymentService.getTransactions().then(res => res.data),
  });

  const isLoading = walletLoading || escrowsLoading || txLoading;

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardLayout>
    );
  }

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val || 0);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="font-heading text-2xl font-bold">Payments & Escrows</h1>

        {/* Escrow Overview */}
        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="shadow-card">
            <CardContent className="p-5 text-center">
              <p className="text-xs text-muted-foreground">Total in Escrow</p>
              <p className="font-heading text-2xl font-bold mt-1">
                {formatCurrency(wallet?.escrow_balance)}
              </p>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardContent className="p-5 text-center">
              <p className="text-xs text-muted-foreground">Total Spent</p>
              <p className="font-heading text-2xl font-bold mt-1">
                {formatCurrency(wallet?.total_spent)}
              </p>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardContent className="p-5 text-center">
              <p className="text-xs text-muted-foreground">Platform Fees Paid</p>
              <p className="font-heading text-2xl font-bold mt-1">
                {formatCurrency(wallet?.total_fees_paid)}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Active Escrows */}
        <Card className="shadow-card">
          <CardHeader><CardTitle className="font-heading text-base">Active Escrows</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {escrows?.map((e: any) => (
              <div key={e.id} className="flex items-center justify-between rounded-lg border border-border p-3">
                <div>
                  <p className="text-sm font-medium">{e.job_title || `Escrow #${e.id}`}</p>
                  <p className="text-xs text-muted-foreground">Worker: {e.worker_name}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-heading font-semibold text-sm">{formatCurrency(e.amount)}</span>
                  <StatusBadge status={e.status.toLowerCase()} />
                </div>
              </div>
            ))}
            {(!escrows || escrows.length === 0) && (
              <p className="py-8 text-center text-sm text-muted-foreground">No active escrows found.</p>
            )}
          </CardContent>
        </Card>

        {/* Transaction History */}
        <Card className="shadow-card">
          <CardHeader><CardTitle className="font-heading text-base">Transaction History</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {transactions?.map((t: any) => (
              <div key={t.id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <div className="flex items-center gap-3">
                  <div className={`flex h-8 w-8 items-center justify-center rounded-full ${t.transaction_type === 'DEBIT' ? 'bg-destructive/10' : 'bg-success/10'}`}>
                    {t.transaction_type === 'DEBIT' ? <ArrowUpRight className="h-4 w-4 text-destructive" /> : <ArrowDownRight className="h-4 w-4 text-success" />}
                  </div>
                  <div>
                    <p className="text-sm">{t.description || t.transaction_type}</p>
                    <p className="text-xs text-muted-foreground">
                      {t.created_at ? format(new Date(t.created_at), 'MMM dd, yyyy') : 'Unknown Date'}
                    </p>
                  </div>
                </div>
                <span className={`text-sm font-medium ${t.transaction_type === 'DEBIT' ? 'text-destructive' : 'text-success'}`}>
                  {t.transaction_type === 'DEBIT' ? '-' : '+'}{formatCurrency(t.amount)}
                </span>
              </div>
            ))}
            {(!transactions || transactions.length === 0) && (
              <p className="py-8 text-center text-sm text-muted-foreground">No transactions found.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

