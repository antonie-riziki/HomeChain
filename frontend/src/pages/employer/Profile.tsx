import { User, MapPin, Mail, Phone, Building2, Loader2 } from 'lucide-react';
import DashboardLayout from '@/components/common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/context/AuthContext';
import { useState } from 'react';
import { authService } from '@/services';
import { toast } from 'sonner';

export default function EmployerProfile() {
  const { user, fetchProfile } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || user?.first_name || '',
    first_name: user?.first_name || user?.full_name?.split(' ')[0] || '',
    last_name: user?.last_name || user?.full_name?.split(' ').slice(1).join(' ') || '',
    email: user?.email || '',
    phone: user?.phone || '',
    location: user?.location || '',
    company_name: user?.company_name || '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [e.target.id]: e.target.value }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // Use full_name if available, otherwise combine first_name and last_name
      const updateData = {
        ...formData,
        full_name: formData.full_name || `${formData.first_name} ${formData.last_name}`.trim(),
      };
      // Remove first_name and last_name as backend expects full_name
      delete (updateData as any).first_name;
      delete (updateData as any).last_name;
      await authService.updateProfile(updateData);
      await fetchProfile();
      toast.success('Profile updated successfully');
    } catch (err: any) {
      toast.error(err.response?.data?.error || err.response?.data?.message || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-2xl space-y-6">
        <h1 className="font-heading text-2xl font-bold">My Profile</h1>

        <Card className="shadow-card">
          <CardHeader><CardTitle className="font-heading text-base">Personal Information</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4 mb-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary font-heading text-xl font-bold text-primary-foreground">
                {(user?.full_name || user?.first_name || 'U').split(' ').map((n: string) => n[0]).join('').substring(0, 2)}
              </div>
              <div>
                <p className="font-heading font-semibold">{user?.full_name || `${user?.first_name || ''} ${user?.last_name || ''}`.trim() || 'User'}</p>
                <p className="text-sm text-muted-foreground">Employer Account</p>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name</Label>
              <Input id="full_name" value={formData.full_name || `${formData.first_name} ${formData.last_name}`.trim()} onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={formData.email} disabled />
              <p className="text-[10px] text-muted-foreground">Email cannot be changed.</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" value={formData.phone} onChange={handleChange} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input id="location" value={formData.location} onChange={handleChange} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="company_name">Company Name</Label>
              <Input id="company_name" value={formData.company_name} onChange={handleChange} />
            </div>
            <Button
              className="font-heading font-semibold"
              onClick={handleSave}
              disabled={loading}
            >
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save Changes
            </Button>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

