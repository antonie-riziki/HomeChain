import { useParams, useNavigate, Link } from 'react-router-dom';
import { MapPin, Clock, DollarSign, Briefcase, User, ArrowLeft, Loader2, Bookmark, BookmarkCheck } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobService } from '@/services';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import StatusBadge from '@/components/common/StatusBadge';
import SkillBadge from '@/components/common/SkillBadge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import DashboardLayout from '@/components/common/DashboardLayout';
import Navbar from '@/components/common/Navbar';
import Footer from '@/components/common/Footer';
import { useState } from 'react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';

export default function JobDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const queryClient = useQueryClient();
  const [coverLetter, setCoverLetter] = useState('');
  const [proposedRate, setProposedRate] = useState('');
  const [estimatedDays, setEstimatedDays] = useState('');

  const { data: job, isLoading } = useQuery({
    queryKey: ['job', id],
    queryFn: () => jobService.getJob(id!).then(res => res.data),
    enabled: !!id,
  });

  const { data: isSaved } = useQuery({
    queryKey: ['saved-jobs-check', id],
    queryFn: () => jobService.getSavedJobs().then(res => {
      const saved = res.data || [];
      return saved.some((s: any) => s.job === parseInt(id!) || s.id === parseInt(id!));
    }),
    enabled: !!id && isAuthenticated && user?.user_type === 'worker',
  });

  const applyMutation = useMutation({
    mutationFn: (data: any) => jobService.applyForJob(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', id] });
      toast.success('Application submitted successfully!');
      navigate('/worker/jobs/applied');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to submit application');
    },
  });

  const saveMutation = useMutation({
    mutationFn: () => jobService.saveJob(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-jobs-check', id] });
      toast.success('Job saved!');
    },
  });

  const unsaveMutation = useMutation({
    mutationFn: () => jobService.unsaveJob(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-jobs-check', id] });
      toast.success('Job removed from saved');
    },
  });

  const isWorker = user?.user_type === 'worker';
  const isEmployer = user?.user_type === 'employer';
  const isOwner = isEmployer && job?.employer === user?.id;

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    if (!coverLetter.trim() || !proposedRate || !estimatedDays) {
      toast.error('Please fill in all required fields');
      return;
    }
    applyMutation.mutate({
      cover_letter: coverLetter,
      proposed_rate: parseFloat(proposedRate),
      estimated_days: parseInt(estimatedDays),
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        {isAuthenticated ? <DashboardLayout><div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div></DashboardLayout> : <><Navbar /><div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div><Footer /></>}
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-background">
        {isAuthenticated ? <DashboardLayout><div className="text-center py-12"><h2 className="text-xl font-bold mb-2">Job not found</h2><Button asChild><Link to="/browse-jobs">Browse Jobs</Link></Button></div></DashboardLayout> : <><Navbar /><div className="text-center py-12"><h2 className="text-xl font-bold mb-2">Job not found</h2><Button asChild><Link to="/browse-jobs">Browse Jobs</Link></Button></div><Footer /></>}
      </div>
    );
  }

  const content = (
    <div className="max-w-4xl mx-auto space-y-6">
      <Button variant="ghost" onClick={() => navigate(-1)} className="mb-4">
        <ArrowLeft className="mr-2 h-4 w-4" /> Back
      </Button>

      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="font-heading text-2xl md:text-3xl font-bold">{job.title}</h1>
            <StatusBadge status={job.status?.toLowerCase() || 'open'} />
          </div>
          <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-4">
            <span className="flex items-center gap-1"><MapPin className="h-4 w-4" />{job.location}</span>
            <span className="flex items-center gap-1"><Clock className="h-4 w-4" />{job.created_at ? formatDistanceToNow(new Date(job.created_at), { addSuffix: true }) : 'Recent'}</span>
            <span className="flex items-center gap-1"><DollarSign className="h-4 w-4" />{job.budget_display || `$${job.budget}`} {job.payment_type === 'HOURLY' ? '/hr' : 'fixed'}</span>
          </div>
        </div>
        {isWorker && (
          <Button
            variant="outline"
            onClick={() => isSaved ? unsaveMutation.mutate() : saveMutation.mutate()}
            disabled={saveMutation.isPending || unsaveMutation.isPending}
          >
            {isSaved ? <BookmarkCheck className="mr-2 h-4 w-4" /> : <Bookmark className="mr-2 h-4 w-4" />}
            {isSaved ? 'Saved' : 'Save'}
          </Button>
        )}
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Card className="shadow-card">
            <CardContent className="p-6">
              <h2 className="font-heading text-lg font-semibold mb-4">Job Description</h2>
              <p className="text-muted-foreground whitespace-pre-wrap">{job.description}</p>
            </CardContent>
          </Card>

          <Card className="shadow-card">
            <CardContent className="p-6">
              <h2 className="font-heading text-lg font-semibold mb-4">Required Skills</h2>
              <div className="flex flex-wrap gap-2">
                {(job.skills_required || []).map(skill => (
                  <SkillBadge key={skill} name={skill} />
                ))}
              </div>
            </CardContent>
          </Card>

          {isWorker && job.status === 'OPEN' && (
            <Card className="shadow-card">
              <CardContent className="p-6">
                <h2 className="font-heading text-lg font-semibold mb-4">Apply for this Job</h2>
                <form onSubmit={handleApply} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="coverLetter">Cover Letter *</Label>
                    <Textarea
                      id="coverLetter"
                      rows={5}
                      value={coverLetter}
                      onChange={(e) => setCoverLetter(e.target.value)}
                      placeholder="Tell the employer why you're a good fit..."
                      required
                    />
                  </div>
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="proposedRate">Proposed Rate ($) *</Label>
                      <Input
                        id="proposedRate"
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={proposedRate}
                        onChange={(e) => setProposedRate(e.target.value)}
                        placeholder={job.payment_type === 'HOURLY' ? 'e.g. 25' : 'e.g. 500'}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="estimatedDays">Estimated Days *</Label>
                      <Input
                        id="estimatedDays"
                        type="number"
                        min="1"
                        value={estimatedDays}
                        onChange={(e) => setEstimatedDays(e.target.value)}
                        placeholder="e.g. 7"
                        required
                      />
                    </div>
                  </div>
                  <Button type="submit" className="w-full" disabled={applyMutation.isPending}>
                    {applyMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Submit Application
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          <Card className="shadow-card">
            <CardContent className="p-6">
              <h3 className="font-heading font-semibold mb-4">Job Details</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Category:</span>
                  <span className="font-medium">{job.category}</span>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Budget:</span>
                  <span className="font-medium">{job.budget_display || `$${job.budget}`}</span>
                </div>
                {job.start_date && (
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Start:</span>
                    <span className="font-medium">{new Date(job.start_date).toLocaleDateString()}</span>
                  </div>
                )}
                {job.employer_name && (
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Employer:</span>
                    <span className="font-medium">{job.employer_name}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
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
