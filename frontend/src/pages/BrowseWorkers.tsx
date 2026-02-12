import { useState } from 'react';
import { Search, Loader2, Users } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { userService } from '@/services';
import { useAuth } from '@/context/AuthContext';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Navbar from '@/components/common/Navbar';
import Footer from '@/components/common/Footer';
import WorkerCard from '@/components/common/WorkerCard';
import DashboardLayout from '@/components/common/DashboardLayout';

export default function BrowseWorkers() {
  const { isAuthenticated, user } = useAuth();
  const [search, setSearch] = useState('');
  const [skill, setSkill] = useState('all');
  const [sortBy, setSortBy] = useState('rating');

  const { data: workers, isLoading } = useQuery({
    queryKey: ['workers', search, skill, sortBy],
    queryFn: () => userService.listWorkers({
      search,
      skill: skill !== 'all' ? skill : undefined,
      ordering: sortBy === 'rating' ? '-average_rating' : sortBy === 'jobs' ? '-completed_jobs' : sortBy === 'rate_low' ? 'hourly_rate' : '-hourly_rate'
    }).then(res => res.data),
  });

  const isEmployer = user?.user_type?.toLowerCase() === 'employer';

  const content = (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="font-heading text-3xl font-bold text-foreground">Find Workers</h1>
        <p className="mt-1 text-muted-foreground">Browse verified domestic professionals ready to help.</p>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by name..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Select value={skill} onValueChange={setSkill}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Skill" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Skills</SelectItem>
              <SelectItem value="Cleaning">Cleaning</SelectItem>
              <SelectItem value="Cooking">Cooking</SelectItem>
              <SelectItem value="Childcare">Childcare</SelectItem>
              <SelectItem value="Caregiving">Caregiving</SelectItem>
            </SelectContent>
          </Select>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="rating">Highest Rated</SelectItem>
              <SelectItem value="jobs">Most Jobs</SelectItem>
              <SelectItem value="rate_low">Rate: Low</SelectItem>
              <SelectItem value="rate_high">Rate: High</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : workers && workers.length > 0 ? (
        <>
          <p className="text-sm text-muted-foreground mb-4">{workers.length} workers found</p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {workers.map((w: any) => (
              <WorkerCard
                key={w.id}
                id={w.id}
                name={w.full_name}
                avatar={w.profile_picture}
                location={w.location || 'Not specified'}
                hourlyRate={w.hourly_rate || '0'}
                rating={w.average_rating || 0}
                completedJobs={w.completed_jobs || 0}
                skills={w.skills || []}
                isVerified={w.is_verified}
              />
            ))}
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Users className="h-6 w-6" />
          </div>
          <h3 className="font-heading text-lg font-semibold text-foreground">No workers found</h3>
          <p className="mx-auto max-w-[300px] text-sm text-muted-foreground">
            Try adjusting your search or filters to find what you're looking for.
          </p>
        </div>
      )}
    </div>
  );

  if (isAuthenticated && isEmployer) {
    return <DashboardLayout>{content}</DashboardLayout>;
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="py-8">{content}</main>
      <Footer />
    </div>
  );
}
