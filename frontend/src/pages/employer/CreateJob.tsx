import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import DashboardLayout from '@/components/common/DashboardLayout';

const skillOptions = ['House Cleaning', 'Deep Cleaning', 'Laundry', 'Cooking', 'Childcare', 'Elderly Care', 'Gardening', 'Driving', 'First Aid', 'Meal Prep', 'Organizing', 'Pet Care'];

export default function CreateJob() {
  const [step, setStep] = useState(1);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const navigate = useNavigate();

  const toggleSkill = (skill: string) => {
    setSelectedSkills(prev => prev.includes(skill) ? prev.filter(s => s !== skill) : [...prev, skill]);
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
                <Label>Job Title</Label>
                <Input placeholder="e.g. Weekly House Cleaning" />
              </div>
              <div className="space-y-2">
                <Label>Category</Label>
                <Select>
                  <SelectTrigger><SelectValue placeholder="Select category" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cleaning">Cleaning</SelectItem>
                    <SelectItem value="cooking">Cooking</SelectItem>
                    <SelectItem value="childcare">Childcare</SelectItem>
                    <SelectItem value="caregiving">Caregiving</SelectItem>
                    <SelectItem value="gardening">Gardening</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea rows={5} placeholder="Describe the job requirements, schedule, and expectations..." />
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
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h2 className="font-heading text-lg font-semibold">Location & Schedule</h2>
              <div className="space-y-2">
                <Label>Location</Label>
                <Input placeholder="City, Area" />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Start Date</Label>
                  <Input type="date" />
                </div>
                <div className="space-y-2">
                  <Label>End Date</Label>
                  <Input type="date" />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Working Hours</Label>
                <Input placeholder="e.g. Mon-Fri, 8AM - 5PM" />
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <h2 className="font-heading text-lg font-semibold">Payment</h2>
              <div className="space-y-2">
                <Label>Payment Type</Label>
                <Select>
                  <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fixed">Fixed Price</SelectItem>
                    <SelectItem value="hourly">Hourly Rate</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Budget ($)</Label>
                <Input type="number" min="1" placeholder="e.g. 150" />
              </div>
              <div className="rounded-lg bg-info/10 p-4 text-sm text-info">
                Payments are secured via Stellar blockchain escrow. Funds will be held until both parties confirm job completion.
              </div>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            {step > 1 && (
              <Button variant="outline" onClick={() => setStep(step - 1)}>
                <ArrowLeft className="mr-1 h-4 w-4" /> Back
              </Button>
            )}
            <div className="flex-1" />
            {step < 4 ? (
              <Button onClick={() => setStep(step + 1)}>
                Next <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            ) : (
              <Button onClick={() => navigate('/employer/jobs')} className="font-heading font-semibold">
                Publish Job
              </Button>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
