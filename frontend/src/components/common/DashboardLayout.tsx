import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import Navbar from './Navbar';
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  CreditCard,
  Star,
  User,
  Wallet,
  BookmarkCheck,
  Search,
  Send,
  Plus,
  Users,
} from 'lucide-react';

interface DashboardLayoutProps {
  children: ReactNode;
}

const employerLinks = [
  { to: '/employer/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/employer/jobs', icon: Briefcase, label: 'My Jobs' },
  { to: '/employer/jobs/create', icon: Plus, label: 'Post Job' },
  { to: '/browse-jobs', icon: Search, label: 'Browse Jobs' },
  { to: '/employer/contracts', icon: FileText, label: 'Contracts' },
  { to: '/workers', icon: Users, label: 'Find Workers' },
  { to: '/employer/payments', icon: CreditCard, label: 'Payments' },
  { to: '/employer/profile', icon: User, label: 'Profile' },
];

const workerLinks = [
  { to: '/worker/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/worker/jobs/browse', icon: Briefcase, label: 'Browse Jobs' },
  { to: '/worker/jobs/applied', icon: Send, label: 'Applications' },
  { to: '/worker/jobs/saved', icon: BookmarkCheck, label: 'Saved Jobs' },
  { to: '/worker/contracts', icon: FileText, label: 'Contracts' },
  { to: '/worker/wallet', icon: Wallet, label: 'Wallet' },
  { to: '/worker/ratings', icon: Star, label: 'Ratings' },
  { to: '/worker/profile', icon: User, label: 'Profile' },
];

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user } = useAuth();
  const location = useLocation();
  const links = user?.user_type?.toLowerCase() === 'employer' ? employerLinks : workerLinks;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container mx-auto flex gap-6 px-4 py-6">
        {/* Sidebar */}
        <aside className="hidden w-56 shrink-0 lg:block">
          <nav className="sticky top-20 flex flex-col gap-1">
            {links.map(link => {
              const active = location.pathname === link.to;
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${active
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                >
                  <link.icon className="h-4 w-4" />
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
