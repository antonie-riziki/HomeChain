import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Eye, EyeOff, Briefcase, Wrench, ArrowLeft, ArrowRight } from 'lucide-react';
import Navbar from '@/components/common/Navbar';

type UserType = 'employer' | 'worker' | null;

export default function Register() {
  const [step, setStep] = useState(1);
  const [userType, setUserType] = useState<UserType>(null);
  const [formData, setFormData] = useState({
    username: '', full_name: '', email: '', password: '', confirm_password: '',
    phone: '', location: '', company_name: '', hourly_rate: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const update = (field: string, value: string) => setFormData(prev => ({ ...prev, [field]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      // Transform user_type to uppercase for backend
      await register({ ...formData, user_type: userType?.toUpperCase() });
      navigate(userType === 'employer' ? '/employer/dashboard' : '/worker/dashboard');
    } catch (err: any) {
      console.error('Registration error:', err);
      const errorMessage = err?.response?.data?.message || err?.message || 'Registration failed. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-lg">
          <div className="rounded-2xl border border-border bg-card p-8 shadow-card">
            <div className="text-center mb-8">
              <h1 className="font-heading text-2xl font-bold">Create Your Account</h1>
              <p className="mt-1 text-sm text-muted-foreground">Step {step} of 3</p>
              {/* Progress bar */}
              <div className="mt-4 flex gap-1.5">
                {[1, 2, 3].map(s => (
                  <div key={s} className={`h-1.5 flex-1 rounded-full transition-colors ${s <= step ? 'bg-primary' : 'bg-muted'}`} />
                ))}
              </div>
            </div>

            {error && <div className="mb-4 rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}

            {/* Step 1: Choose Type */}
            {step === 1 && (
              <div className="space-y-4">
                <p className="text-center text-sm text-muted-foreground mb-4">How will you use HomeChain?</p>
                <div className="grid gap-4 sm:grid-cols-2">
                  <button
                    onClick={() => { setUserType('employer'); setStep(2); }}
                    className={`group rounded-xl border-2 p-6 text-center transition-all hover:border-primary hover:shadow-card ${userType === 'employer' ? 'border-primary bg-primary/5' : 'border-border'}`}
                  >
                    <Briefcase className="mx-auto mb-3 h-8 w-8 text-primary" />
                    <h3 className="font-heading font-semibold">I'm an Employer</h3>
                    <p className="mt-1 text-xs text-muted-foreground">I want to hire domestic workers</p>
                  </button>
                  <button
                    onClick={() => { setUserType('worker'); setStep(2); }}
                    className={`group rounded-xl border-2 p-6 text-center transition-all hover:border-primary hover:shadow-card ${userType === 'worker' ? 'border-primary bg-primary/5' : 'border-border'}`}
                  >
                    <Wrench className="mx-auto mb-3 h-8 w-8 text-accent" />
                    <h3 className="font-heading font-semibold">I'm a Worker</h3>
                    <p className="mt-1 text-xs text-muted-foreground">I provide domestic services</p>
                  </button>
                </div>
              </div>
            )}

            {/* Step 2: Personal Info */}
            {step === 2 && (
              <form onSubmit={e => { e.preventDefault(); setStep(3); }} className="space-y-4">
                <div className="space-y-2">
                  <Label>Username</Label>
                  <Input value={formData.username} onChange={e => update('username', e.target.value)} placeholder="Choose a unique username" required />
                  <p className="text-xs text-muted-foreground">This will be used for login</p>
                </div>
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input value={formData.full_name} onChange={e => update('full_name', e.target.value)} placeholder="John Doe" required />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input type="email" value={formData.email} onChange={e => update('email', e.target.value)} required />
                </div>
                <div className="space-y-2">
                  <Label>Password</Label>
                  <div className="relative">
                    <Input type={showPassword ? 'text' : 'password'} value={formData.password} onChange={e => update('password', e.target.value)} required minLength={8} />
                    <button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground" onClick={() => setShowPassword(!showPassword)}>
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Confirm Password</Label>
                  <Input type="password" value={formData.confirm_password} onChange={e => update('confirm_password', e.target.value)} required minLength={8} />
                </div>
                <div className="flex gap-3">
                  <Button type="button" variant="outline" onClick={() => setStep(1)} className="flex-1"><ArrowLeft className="mr-1 h-4 w-4" /> Back</Button>
                  <Button type="submit" className="flex-1 font-heading font-semibold">Next <ArrowRight className="ml-1 h-4 w-4" /></Button>
                </div>
              </form>
            )}

            {/* Step 3: Role-specific */}
            {step === 3 && (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label>Phone Number</Label>
                  <Input value={formData.phone} onChange={e => update('phone', e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Location</Label>
                  <Input value={formData.location} onChange={e => update('location', e.target.value)} placeholder="City, Country" />
                </div>
                {userType === 'employer' && (
                  <div className="space-y-2">
                    <Label>Company / Household Name</Label>
                    <Input value={formData.company_name} onChange={e => update('company_name', e.target.value)} placeholder="Optional" />
                  </div>
                )}
                {userType === 'worker' && (
                  <div className="space-y-2">
                    <Label>Hourly Rate ($)</Label>
                    <Input type="number" min="1" value={formData.hourly_rate} onChange={e => update('hourly_rate', e.target.value)} placeholder="e.g. 20" />
                  </div>
                )}
                <div className="flex gap-3">
                  <Button type="button" variant="outline" onClick={() => setStep(2)} className="flex-1"><ArrowLeft className="mr-1 h-4 w-4" /> Back</Button>
                  <Button type="submit" className="flex-1 font-heading font-semibold" disabled={loading}>{loading ? 'Creating...' : 'Create Account'}</Button>
                </div>
              </form>
            )}

            <p className="mt-6 text-center text-sm text-muted-foreground">
              Already have an account? <Link to="/login" className="font-medium text-primary hover:underline">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
