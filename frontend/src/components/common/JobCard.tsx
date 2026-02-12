import { Link } from 'react-router-dom';
import { MapPin, Clock, DollarSign, BookmarkCheck } from 'lucide-react';
import StatusBadge from './StatusBadge';
import SkillBadge from './SkillBadge';

interface JobCardProps {
  id: string;
  title: string;
  description: string;
  location: string;
  budget: string;
  budgetType: 'fixed' | 'hourly';
  category: string;
  skills: string[];
  status: 'open' | 'in_progress' | 'completed' | 'cancelled';
  createdAt: string;
  employerName?: string;
  onSaveToggle?: () => void;
}

export default function JobCard({ id, title, description, location, budget, budgetType, skills, status, createdAt, employerName, onSaveToggle }: JobCardProps) {
  return (
    <Link
      to={`/job/${id}`}
      className="group block rounded-xl border border-border bg-card p-5 shadow-card transition-all hover:shadow-card-hover hover:-translate-y-0.5"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <h3 className="font-heading text-base font-semibold text-card-foreground group-hover:text-primary transition-colors line-clamp-1">
          {title}
        </h3>
        <div className="flex items-center gap-2">
          {onSaveToggle && (
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onSaveToggle();
              }}
              className="p-1 rounded-full hover:bg-muted text-primary"
              title="Remove from saved"
            >
              <BookmarkCheck className="h-4 w-4 fill-current" />
            </button>
          )}
          <StatusBadge status={status} />
        </div>
      </div>

      <p className="text-sm text-muted-foreground line-clamp-2 mb-4">{description}</p>

      <div className="flex flex-wrap gap-1.5 mb-4">
        {skills.slice(0, 3).map(skill => (
          <SkillBadge key={skill} name={skill} />
        ))}
        {skills.length > 3 && <span className="text-xs text-muted-foreground self-center">+{skills.length - 3}</span>}
      </div>

      <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{location}</span>
        <span className="flex items-center gap-1"><DollarSign className="h-3.5 w-3.5" />{budget} {budgetType === 'hourly' ? '/hr' : 'fixed'}</span>
        <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{createdAt}</span>
      </div>

      {employerName && <p className="mt-3 text-xs text-muted-foreground">Posted by <span className="font-medium text-foreground">{employerName}</span></p>}
    </Link>
  );
}
