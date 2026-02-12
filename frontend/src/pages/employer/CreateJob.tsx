import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import DashboardLayout from '@/components/common/DashboardLayout';
import { useMutation } from '@tanstack/react-query';
import { jobService } from '@/services';
import { toast } from 'sonner';

const skillOptions = ['House Cleaning', 'Deep Cleaning', 'Laundry', 'Cooking', 'Childcare', 'Elderly Care', 'Gardening', 'Driving', 'First Aid', 'Meal Prep', 'Organizing', 'Pet Care'];

export default function CreateJob() {
  const [step, setStep] = useState(1);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    title: '',
    category: '',
    description: '',
    location: '',
    start_date: '',
    end_date: '',
    working_hours: '',
    payment_type: 'FIXED',
    budget: '',
    hourly_rate_min: '',
    hourly_rate_max: '',
    estimated_duration: '1',
    experience_level: 'ENTRY',
    is_remote: false,
    is_urgent: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const navigate = useNavigate();

  const toggleSkill = (skill: string) => {
    setSelectedSkills(prev => prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]);
  };

  const updateFormData = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateStep = (stepNum: number): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (stepNum === 1) {
      if (!formData.title.trim()) newErrors.title = 'Job title is required';
      if (!formData.category) newErrors.category = 'Category is required';
      if (!formData.description.trim()) newErrors.description = 'Description is required';
    } else if (stepNum === 2) {
      if (selectedSkills.length === 0) {
        newErrors.skills = 'At least one skill is required';
      }
    } else if (stepNum === 3) {
      if (!formData.location.trim()) newErrors.location = 'Location is required';
      if (formData.start_date && formData.end_date && formData.start_date > formData.end_date) {
        newErrors.dates = 'Start date must be before end date';
      }
    } else if (stepNum === 4) {
      if (formData.payment_type === 'FIXED') {
        if (!formData.budget || parseFloat(formData.budget) <= 0) {
          newErrors.budget = 'Budget must be greater than 0';
        }
      } else {
        if (!formData.hourly_rate_min || parseFloat(formData.hourly_rate_min) <= 0) {
          newErrors.hourly_rate_min = 'Minimum hourly rate is required';
        }
        if (!formData.hourly_rate_max || parseFloat(formData.hourly_rate_max) <= 0) {
          newErrors.hourly_rate_max = 'Maximum hourly rate is required';
        }
        if (formData.hourly_rate_min && formData.hourly_rate_max && 
            parseFloat(formData.hourly_rate_min) >= parseFloat(formData.hourly_rate_max)) {
          newErrors.hourly_rate = 'Minimum rate must be less than maximum rate';
        }
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const createJobMutation = useMutation({
    mutationFn: (data: any) => jobService.createJob(data),
    onSuccess: (response) => {
      const jobId = response.data.id;
      toast.success('Job created successfully!');
      // Publish the job
      jobService.publishJob(jobId).then(() => {
        toast.success('Job published!');
        navigate('/employer/jobs');
      }).catch(() => {
        navigate('/employer/jobs');
      });
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.message || 
                      error.response?.data?.error ||
                      Object.values(error.response?.data || {})[0]?.[0] ||
                      'Failed to create job. Please try again.';
      toast.error(errorMsg);
    },
  });

  const handleNext = () => {
    if (validateStep(step)) {
      setStep(step + 1);
    }
  };

  const handleSubmit = () => {
    if (!validateStep(4)) {
      return;
    }

    const submitData: any = {
      title: formData.title,
      description: formData.description,
      category: formData.category,
      skills_required: selectedSkills,
      location: formData.location,
      payment_type: formData.payment_type,
      experience_level: formData.experience_level,
      estimated_duration: parseInt(formData.estimated_duration) || 1,
      is_remote: formData.is_remote,
      is_urgent: formData.is_urgent,
    };

    if (formData.start_date) submitData.start_date = formData.start_date;
    if (formData.end_date) submitData.end_date = formData.end_date;

    if (formData.payment_type === 'FIXED') {
      submitData.budget = parseFloat(formData.budget);
    } else {
      submitData.hourly_rate_min = parseFloat(formData.hourly_rate_min);
      submitData.hourly_rate_max = parseFloat(formData.hourly_rate_max);
    }

    createJobMutation.mutate(submitData);
  };

  return (
    <DashboardLayout>
      <div className="max-w-2xl">
        <h1 className="font-heading text-2xl font-bold mb-1">Post a New Job</h1>
        <p className="text-sm text-muted-foreground mb-6">Step {step} of 4</p>
        <div className="flex gap-1.5 mb-8">
          {[1, 2, 3, 4].map(s => (
            <div key={s} className={`h-1.5 flex-1 rounded-full transition-colors ${s <= step ? 'bg-primary' : 'bg-muted'}`} />
          ))}
        </div>

        <div className="rounded-xl border border-border bg-card p-6 shadow-card">
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="font-heading text-lg font-semibold">Basic Information</h2>
              <div className="space-y-2">
                <Label>Job Title *</Label>
                <Input 
                  placeholder="e.g. Weekly House Cleaning" 
                  value={formData.title}
                  onChange={(e) => updateFormData('title', e.target.value)}
                  className={errors.title ? 'border-destructive' : ''}
                />
                {errors.title && <p className="text-xs text-destructive">{errors.title}</p>}
              </div>
              <div className="space-y-2">
                <Label>Category *</Label>
                <Select value={formData.category} onValueChange={(value) => updateFormData('category', value)}>
                  <SelectTrigger className={errors.category ? 'border-destructive' : ''}>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Cleaning">Cleaning</SelectItem>
                    <SelectItem value="Cooking">Cooking</SelectItem>
                    <SelectItem value="Childcare">Childcare</SelectItem>
                    <SelectItem value="Caregiving">Caregiving</SelectItem>
                    <SelectItem value="Gardening">Gardening</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
                {errors.category && <p className="text-xs text-destructive">{errors.category}</p>}
              </div>
              <div className="space-y-2">
                <Label>Description *</Label>
                <Textarea 
                  rows={5} 
                  placeholder="Describe the job requirements, schedule, and expectations..." 
                  value={formData.description}
                  onChange={(e) => updateFormData('description', e.target.value)}
                  className={errors.description ? 'border-destructive' : ''}
                />
                {errors.description && <p className="text-xs text-destructive">{errors.description}</p>}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="font-heading text-lg font-semibold">Required Skills</h2>
              <p className="text-sm text-muted-foreground">Select all skills relevant to this job.</p>
              <div className="flex flex-wrap gap-2">
                {skillOptions.map(skill => (
                  <button
                    key={skill}
                    type="button"
                    onClick={() => toggleSkill(skill)}
                    className={`rounded-full px-3 py-1.5 text-sm font-medium border transition-colors ${
                      selectedSkills.includes(skill)
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-card text-muted-foreground border-border hover:border-primary/50'
                    }`}
                  >
                    {skill}
                  </button>
                ))}
              </div>
              {errors.skills && <p className="text-xs text-destructive">{errors.skills}</p>}
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h2 className="font-heading text-lg font-semibold">Location & Schedule</h2>
              <div className="space-y-2">
                <Label>Location *</Label>
                <Input 
                  placeholder="City, Area" 
                  value={formData.location}
                  onChange={(e) => updateFormData('location', e.target.value)}
                  className={errors.location ? 'border-destructive' : ''}
                />
                {errors.location && <p className="text-xs text-destructive">{errors.location}</p>}
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Start Date</Label>
                  <Input 
                    type="date" 
                    value={formData.start_date}
                    onChange={(e) => updateFormData('start_date', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>End Date</Label>
                  <Input 
                    type="date" 
                    value={formData.end_date}
                    onChange={(e) => updateFormData('end_date', e.target.value)}
                  />
                </div>
              </div>
              {errors.dates && <p className="text-xs text-destructive">{errors.dates}</p>}
              <div className="space-y-2">
                <Label>Estimated Duration (days)</Label>
                <Input 
                  type="number" 
                  min="1" 
                  placeholder="e.g. 7" 
                  value={formData.estimated_duration}
                  onChange={(e) => updateFormData('estimated_duration', e.target.value)}
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_remote"
                  checked={formData.is_remote}
                  onChange={(e) => updateFormData('is_remote', e.target.checked)}
                  className="h-4 w-4 rounded border-border"
                />
                <Label htmlFor="is_remote" className="cursor-pointer">Remote work available</Label>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <h2 className="font-heading text-lg font-semibold">Payment</h2>
              <div className="space-y-2">
                <Label>Payment Type *</Label>
                <Select value={formData.payment_type} onValueChange={(value) => updateFormData('payment_type', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="FIXED">Fixed Price</SelectItem>
                    <SelectItem value="HOURLY">Hourly Rate</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {formData.payment_type === 'FIXED' ? (
                <div className="space-y-2">
                  <Label>Budget ($) *</Label>
                  <Input 
                    type="number" 
                    min="0.01" 
                    step="0.01"
                    placeholder="e.g. 150" 
                    value={formData.budget}
                    onChange={(e) => updateFormData('budget', e.target.value)}
                    className={errors.budget ? 'border-destructive' : ''}
                  />
                  {errors.budget && <p className="text-xs text-destructive">{errors.budget}</p>}
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Min Hourly Rate ($) *</Label>
                    <Input 
                      type="number" 
                      min="0.01" 
                      step="0.01"
                      placeholder="e.g. 15" 
                      value={formData.hourly_rate_min}
                      onChange={(e) => updateFormData('hourly_rate_min', e.target.value)}
                      className={errors.hourly_rate_min || errors.hourly_rate ? 'border-destructive' : ''}
                    />
                    {errors.hourly_rate_min && <p className="text-xs text-destructive">{errors.hourly_rate_min}</p>}
                  </div>
                  <div className="space-y-2">
                    <Label>Max Hourly Rate ($) *</Label>
                    <Input 
                      type="number" 
                      min="0.01" 
                      step="0.01"
                      placeholder="e.g. 25" 
                      value={formData.hourly_rate_max}
                      onChange={(e) => updateFormData('hourly_rate_max', e.target.value)}
                      className={errors.hourly_rate_max || errors.hourly_rate ? 'border-destructive' : ''}
                    />
                    {errors.hourly_rate_max && <p className="text-xs text-destructive">{errors.hourly_rate_max}</p>}
                  </div>
                </div>
              )}
              {errors.hourly_rate && <p className="text-xs text-destructive">{errors.hourly_rate}</p>}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_urgent"
                  checked={formData.is_urgent}
                  onChange={(e) => updateFormData('is_urgent', e.target.checked)}
                  className="h-4 w-4 rounded border-border"
                />
                <Label htmlFor="is_urgent" className="cursor-pointer">Mark as urgent</Label>
              </div>
              <div className="rounded-lg bg-info/10 p-4 text-sm text-info">
                Payments are secured via Stellar blockchain escrow. Funds will be held until both parties confirm job completion.
              </div>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            {step > 1 && (
              <Button variant="outline" onClick={() => setStep(step - 1)} disabled={createJobMutation.isPending}>
                <ArrowLeft className="mr-1 h-4 w-4" /> Back
              </Button>
            )}
            <div className="flex-1" />
            {step < 4 ? (
              <Button onClick={handleNext} disabled={createJobMutation.isPending}>
                Next <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            ) : (
              <Button 
                onClick={handleSubmit} 
                className="font-heading font-semibold"
                disabled={createJobMutation.isPending}
              >
                {createJobMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Publish Job
              </Button>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
