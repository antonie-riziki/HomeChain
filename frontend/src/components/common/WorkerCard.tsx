import { Link } from 'react-router-dom';
import { MapPin, BadgeCheck } from 'lucide-react';
import RatingStars from './RatingStars';
import SkillBadge from './SkillBadge';

interface WorkerCardProps {
  id: string;
  name: string;
  avatar?: string;
  location: string;
  hourlyRate: string;
  rating: number;
  completedJobs: number;
  skills: string[];
  isVerified: boolean;
}

export default function WorkerCard({ id, name, avatar, location, hourlyRate, rating, completedJobs, skills, isVerified }: WorkerCardProps) {
  return (
    <Link
      to={`/worker/${id}`}
      className="group block rounded-xl border border-border bg-card p-5 shadow-card transition-all hover:shadow-card-hover hover:-translate-y-0.5"
    >
      <div className="flex items-center gap-4 mb-4">
        <div className="relative h-14 w-14 shrink-0 rounded-full bg-muted overflow-hidden">
          {avatar ? (
            <img src={avatar} alt={name} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-primary font-heading text-lg font-bold text-primary-foreground">
              {name.charAt(0)}
            </div>
          )}
          {isVerified && (
            <div className="absolute -bottom-0.5 -right-0.5 rounded-full bg-card p-0.5">
              <BadgeCheck className="h-4 w-4 text-success" />
            </div>
          )}
        </div>
        <div className="min-w-0">
          <h3 className="font-heading text-base font-semibold text-card-foreground group-hover:text-primary transition-colors truncate">
            {name}
          </h3>
          <div className="flex items-center gap-2 mt-0.5">
            <RatingStars rating={rating} size="sm" />
            <span className="text-xs text-muted-foreground">({completedJobs} jobs)</span>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-4">
        {skills.slice(0, 3).map(skill => (
          <SkillBadge key={skill} name={skill} />
        ))}
      </div>

      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-1 text-muted-foreground"><MapPin className="h-3.5 w-3.5" />{location}</span>
        <span className="font-heading font-semibold text-foreground">${hourlyRate}/hr</span>
      </div>
    </Link>
  );
}
