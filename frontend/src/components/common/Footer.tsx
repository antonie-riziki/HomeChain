import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="border-t border-border bg-card">
      <div className="container mx-auto px-4 py-12">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                <span className="font-heading text-xs font-bold text-primary-foreground">HC</span>
              </div>
              <span className="font-heading text-lg font-bold">HomeChain</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Connecting domestic workers with employers through trusted, blockchain-secured contracts.
            </p>
          </div>

          <div>
            <h4 className="font-heading text-sm font-semibold mb-4">For Workers</h4>
            <nav className="flex flex-col gap-2">
              <Link to="/browse-jobs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Browse Jobs</Link>
              <Link to="/register" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Sign Up</Link>
            </nav>
          </div>

          <div>
            <h4 className="font-heading text-sm font-semibold mb-4">For Employers</h4>
            <nav className="flex flex-col gap-2">
              <Link to="/workers" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Find Workers</Link>
              <Link to="/register" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Post a Job</Link>
            </nav>
          </div>

          <div>
            <h4 className="font-heading text-sm font-semibold mb-4">Platform</h4>
            <nav className="flex flex-col gap-2">
              <span className="text-sm text-muted-foreground">About Us</span>
              <span className="text-sm text-muted-foreground">How It Works</span>
              <span className="text-sm text-muted-foreground">Support</span>
            </nav>
          </div>
        </div>

        <div className="mt-12 border-t border-border pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground">© {new Date().getFullYear()} HomeChain. All rights reserved.</p>
          <p className="text-xs text-muted-foreground">Secured by Stellar Blockchain</p>
        </div>
      </div>
    </footer>
  );
}
