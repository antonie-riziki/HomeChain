import DashboardLayout from '@/components/common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { BadgeCheck, Upload, Loader2, Plus } from 'lucide-react';
import SkillBadge from '@/components/common/SkillBadge';
import { useAuth } from '@/context/AuthContext';
import { useState } from 'react';
import { authService, userService } from '@/services';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';

export default function WorkerProfile() {
  const { user, fetchProfile } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
    location: user?.location || '',
    bio: user?.bio || '',
    hourly_rate: user?.hourly_rate || '',
  });

  const { data: skills, isLoading: skillsLoading } = useQuery({
    queryKey: ['my-skills'],
    queryFn: () => userService.getMySkills().then(res => res.data),
  });

  const { data: documents, isLoading: docsLoading } = useQuery({
    queryKey: ['my-documents'],
    queryFn: () => userService.getDocuments().then(res => res.data),
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.id]: e.target.value }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await authService.updateProfile(formData);
      await fetchProfile();
      toast.success('Profile updated successfully');
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-2xl space-y-6">
        <h1 className="font-heading text-2xl font-bold">My Profile</h1>

        {/* Basic Info */}
        <Card className="shadow-card">
          <CardHeader><CardTitle className="font-heading text-base">Personal Information</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4 mb-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary font-heading text-xl font-bold text-primary-foreground">
                {user?.first_name?.[0]}{user?.last_name?.[0]}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-heading font-semibold">{user?.first_name} {user?.last_name}</p>
                  {user?.is_verified && <BadgeCheck className="h-4 w-4 text-success" />}
                </div>
                <p className="text-sm text-muted-foreground">Worker Account · {user?.is_verified ? 'Verified' : 'Unverified'}</p>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="first_name">First Name</Label>
                <Input id="first_name" value={formData.first_name} onChange={handleChange} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name">Last Name</Label>
                <Input id="last_name" value={formData.last_name} onChange={handleChange} />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={user?.email} disabled />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input id="phone" value={formData.phone} onChange={handleChange} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input id="location" value={formData.location} onChange={handleChange} />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="hourly_rate">Hourly Rate ($)</Label>
              <Input id="hourly_rate" type="number" value={formData.hourly_rate} onChange={handleChange} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bio">Bio</Label>
              <Textarea id="bio" rows={3} value={formData.bio} onChange={handleChange} />
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

        {/* Skills */}
        <Card className="shadow-card">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="font-heading text-base">My Skills</CardTitle>
            <Button variant="outline" size="sm"><Plus className="mr-1 h-3 w-3" /> Add Skill</Button>
          </CardHeader>
          <CardContent>
            {skillsLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
            ) : (
              <div className="flex flex-wrap gap-2">
                {skills?.map((s: any) => <SkillBadge key={s.id} name={s.skill_name} verified={s.is_verified} />)}
                {(!skills || skills.length === 0) && <p className="text-sm text-muted-foreground">No skills added yet.</p>}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Documents */}
        <Card className="shadow-card">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="font-heading text-base">Documents</CardTitle>
            <Button variant="outline" size="sm"><Upload className="mr-1 h-3 w-3" /> Upload</Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {docsLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
            ) : (
              <>
                {documents?.map((d: any) => (
                  <div key={d.id} className="flex items-center justify-between rounded-lg border border-border p-3">
                    <div>
                      <p className="text-sm font-medium">{d.document_type_display || d.document_type}</p>
                      <p className="text-xs text-muted-foreground">Uploaded: {d.uploaded_at ? new Date(d.uploaded_at).toLocaleDateString() : 'N/A'}</p>
                    </div>
                    <span className={`text-xs font-semibold ${d.status === 'VERIFIED' ? 'text-success' : 'text-warning'}`}>{d.status}</span>
                  </div>
                ))}
                {(!documents || documents.length === 0) && <p className="text-sm text-muted-foreground text-center py-4">No documents uploaded.</p>}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

