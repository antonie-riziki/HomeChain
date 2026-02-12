import { useState } from 'react';
import { Search, Loader2, Briefcase } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { jobService } from '@/services';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Navbar from '@/components/common/Navbar';
import Footer from '@/components/common/Footer';
import JobCard from '@/components/common/JobCard';
import DashboardLayout from '@/components/common/DashboardLayout';
import { useAuth } from '@/context/AuthContext';
import { formatDistanceToNow } from 'date-fns';

export default function BrowseJobs() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [sortBy, setSortBy] = useState('newest');
  const { isAuthenticated } = useAuth();

  const { data: jobsResponse, isLoading } = useQuery({
    queryKey: ['browse-jobs', search, category, sortBy],
    queryFn: () => jobService.browseJobs({
      search,
      category: category !== 'all' ? category : undefined,
      ordering: sortBy === 'newest' ? '-created_at' : sortBy === 'budget_high' ? '-budget' : 'budget'
    }).then(res => res.data),
  });

  // Handle paginated response
  const jobs = jobsResponse?.results || jobsResponse || [];

  const content = (
    <div className="space-y-8">
      <div>
        <h1 className="font-heading text-3xl font-bold text-foreground">Browse Jobs</h1>
        <p className="mt-1 text-muted-foreground">Find domestic work opportunities near you.</p>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search jobs..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Select value={category} onValueChange={setCategory}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              <SelectItem value="Cleaning">Cleaning</SelectItem>
              <SelectItem value="Childcare">Childcare</SelectItem>
              <SelectItem value="Cooking">Cooking</SelectItem>
              <SelectItem value="Caregiving">Caregiving</SelectItem>
            </SelectContent>
          </Select>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest</SelectItem>
              <SelectItem value="budget_high">Budget: High</SelectItem>
              <SelectItem value="budget_low">Budget: Low</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : jobs && jobs.length > 0 ? (
        <>
          <p className="text-sm text-muted-foreground mb-4">{jobs.length} jobs found</p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {jobs.map((job: any) => (
              <JobCard
                key={job.id}
                id={job.id}
                title={job.title}
                description={job.description}
                location={job.location}
                budget={job.budget || job.hourly_rate_min}
                budgetType={job.payment_type?.toLowerCase() === 'hourly' ? 'hourly' : 'fixed'}
                category={job.category}
                skills={job.skills_required || []}
                status={job.status?.toLowerCase() || 'open'}
                createdAt={job.created_at ? formatDistanceToNow(new Date(job.created_at), { addSuffix: true }) : 'Recent'}
                employerName={job.employer_name}
              />
            ))}
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16 text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <Briefcase className="h-6 w-6" />
          </div>
          <h3 className="font-heading text-lg font-semibold text-foreground">No jobs found</h3>
          <p className="mx-auto max-w-[300px] text-sm text-muted-foreground">
            Try adjusting your search or filters to find new opportunities.
          </p>
        </div>
      )}
    </div>
  );

  if (isAuthenticated) {
    return <DashboardLayout>{content}</DashboardLayout>;
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        {content}
      </div>
      <Footer />
    </div>
  );
}
