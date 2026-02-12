type Status = 'open' | 'in_progress' | 'completed' | 'cancelled' | 'pending' | 'active' | 'funded' | 'released' | 'disputed';

const statusStyles: Record<Status, string> = {
  open: 'bg-info/10 text-info',
  pending: 'bg-warning/10 text-warning',
  in_progress: 'bg-primary/10 text-primary',
  active: 'bg-primary/10 text-primary',
  funded: 'bg-secondary/10 text-secondary',
  completed: 'bg-success/10 text-success',
  released: 'bg-success/10 text-success',
  cancelled: 'bg-destructive/10 text-destructive',
  disputed: 'bg-destructive/10 text-destructive',
};

const labels: Record<Status, string> = {
  open: 'Open',
  pending: 'Pending',
  in_progress: 'In Progress',
  active: 'Active',
  funded: 'Funded',
  completed: 'Completed',
  released: 'Released',
  cancelled: 'Cancelled',
  disputed: 'Disputed',
};

interface StatusBadgeProps {
  status: Status;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusStyles[status] || 'bg-muted text-muted-foreground'}`}>
      {labels[status] || status}
    </span>
  );
}
