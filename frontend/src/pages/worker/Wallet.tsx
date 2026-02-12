import { Wallet, ArrowUpRight, ArrowDownRight, RefreshCw, Loader2 } from 'lucide-react';
import DashboardLayout from '@/components/common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { paymentService } from '@/services';
import { format } from 'date-fns';
import { toast } from 'sonner';

export default function WorkerWallet() {
  const queryClient = useQueryClient();

  const { data: wallet, isLoading: walletLoading } = useQuery({
    queryKey: ['my-wallet-detailed'],
    queryFn: () => paymentService.getWallet().then(res => res.data),
  });

  const { data: transactions, isLoading: txLoading } = useQuery({
    queryKey: ['my-transactions'],
    queryFn: () => paymentService.getTransactions().then(res => res.data),
  });

  const syncMutation = useMutation({
    mutationFn: () => paymentService.syncWallet(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-wallet-detailed'] });
      queryClient.invalidateQueries({ queryKey: ['my-transactions'] });
      toast.success('Wallet synced with Stellar network');
    },
  });

  const isLoading = walletLoading || txLoading;

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
        <div className="flex items-center justify-between">
          <h1 className="font-heading text-2xl font-bold">Wallet</h1>
          <Button
            variant="outline"
            size="sm"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            <RefreshCw className={`mr-2 h-3 w-3 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            Sync
          </Button>
        </div>

        {/* Balance Cards */}
        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="shadow-card bg-hero">
            <CardContent className="p-6">
              <p className="text-xs text-primary-foreground/70">Available Balance</p>
              <p className="font-heading text-3xl font-bold text-primary-foreground mt-1">
                {formatCurrency(wallet?.balance)}
              </p>
              <p className="text-xs text-primary-foreground/70 mt-2">Stellar USDC</p>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardContent className="p-6">
              <p className="text-xs text-muted-foreground">In Escrow</p>
              <p className="font-heading text-3xl font-bold mt-1">
                {formatCurrency(wallet?.escrow_balance)}
              </p>
              <p className="text-xs text-muted-foreground mt-2">Pending release</p>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardContent className="p-6">
              <p className="text-xs text-muted-foreground">Total Earned</p>
              <p className="font-heading text-3xl font-bold mt-1">
                {formatCurrency(wallet?.total_earned)}
              </p>
              <p className="text-xs text-muted-foreground mt-2">All time</p>
            </CardContent>
          </Card>
        </div>

        <div className="flex gap-3">
          <Button className="font-heading font-semibold">Withdraw Funds</Button>
        </div>

        {/* Transactions */}
        <Card className="shadow-card">
          <CardHeader><CardTitle className="font-heading text-base">Transaction History</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {transactions?.map((t: any) => (
              <div key={t.id} className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
                <div className="flex items-center gap-3">
                  <div className={`flex h-8 w-8 items-center justify-center rounded-full ${t.transaction_type === 'CREDIT' ? 'bg-success/10' : 'bg-destructive/10'}`}>
                    {t.transaction_type === 'CREDIT' ? <ArrowDownRight className="h-4 w-4 text-success" /> : <ArrowUpRight className="h-4 w-4 text-destructive" />}
                  </div>
                  <div>
                    <p className="text-sm">{t.description || t.transaction_type}</p>
                    <p className="text-xs text-muted-foreground">
                      {t.created_at ? format(new Date(t.created_at), 'MMM dd, yyyy') : 'Unknown Date'}
                    </p>
                  </div>
                </div>
                <span className={`text-sm font-medium ${t.transaction_type === 'CREDIT' ? 'text-success' : 'text-destructive'}`}>
                  {t.transaction_type === 'CREDIT' ? '+' : '-'}{formatCurrency(t.amount)}
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

