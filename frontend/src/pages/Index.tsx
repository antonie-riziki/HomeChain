import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, Users, Briefcase, Wallet, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/common/Navbar';
import Footer from '@/components/common/Footer';

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.5 } }),
};

const steps = [
  { icon: Users, title: 'Create Account', desc: 'Sign up as a worker or employer in minutes.' },
  { icon: Briefcase, title: 'Post or Find Jobs', desc: 'Employers post jobs, workers browse and apply.' },
  { icon: Shield, title: 'Secure Contract', desc: 'Agree on terms with blockchain-backed escrow.' },
  { icon: Wallet, title: 'Get Paid', desc: 'Funds released securely upon job completion.' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {/* Hero */}
      <section className="relative overflow-hidden bg-hero">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMSIgZmlsbD0icmdiYSgyNTUsMjU1LDI1NSwwLjA1KSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3QgZmlsbD0idXJsKCNnKSIgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIvPjwvc3ZnPg==')] opacity-50" />
        <div className="container relative mx-auto px-4 py-20 lg:py-32">
          <div className="flex flex-col items-center gap-10 text-center">
            <motion.div initial="hidden" animate="visible" className="max-w-3xl">
              <motion.div custom={0} variants={fadeUp} className="mb-4">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-secondary/20 px-3 py-1 text-xs font-semibold text-secondary">
                  <Shield className="h-3.5 w-3.5" /> Powered by Stellar Blockchain
                </span>
              </motion.div>
              <motion.h1 custom={1} variants={fadeUp} className="font-heading text-5xl font-extrabold leading-tight text-primary-foreground lg:text-6xl xl:text-7xl">
                Connect Workers & Employers, <span className="text-gradient-gold">Secured by Blockchain</span>
              </motion.h1>
              <motion.p custom={2} variants={fadeUp} className="mt-5 text-xl leading-relaxed text-primary-foreground/80 max-w-2xl mx-auto">
                HomeChain is a trusted platform connecting verified domestic workers with employers. We use blockchain technology to ensure secure payments and transparent contracts.
              </motion.p>
            </motion.div>

            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3, duration: 0.6 }}>
              <div className="relative max-w-sm max-h-80 mx-auto rounded-2xl overflow-hidden shadow-elevated">
                <img src="/african_homechain_hero.png" alt="African domestic workers and employers" className="w-full h-full object-cover rounded-2xl" />
                <div className="absolute inset-0 bg-gradient-to-t from-primary/40 to-transparent" />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-background py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-14">
            <h2 className="font-heading text-3xl font-bold">How It Works</h2>
            <p className="mt-3 text-muted-foreground max-w-2xl mx-auto">
              Whether you're looking for work or looking to hire, HomeChain makes it simple and secure.
            </p>
          </div>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((step, i) => (
              <motion.div key={step.title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.12 }} className="relative rounded-xl border border-border bg-card p-6 text-center shadow-card">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                  <step.icon className="h-6 w-6 text-primary" />
                </div>
                <div className="absolute -top-3 left-4 flex h-6 w-6 items-center justify-center rounded-full bg-secondary text-xs font-bold text-secondary-foreground">{i + 1}</div>
                <h3 className="font-heading text-base font-semibold mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* What We Offer */}
      <section className="bg-card py-20 border-y border-border">
        <div className="container mx-auto px-4">
          <div className="text-center mb-14">
            <h2 className="font-heading text-3xl font-bold">What We Offer</h2>
            <p className="mt-3 text-muted-foreground max-w-2xl mx-auto">
              A platform built on trust, transparency, and cutting-edge technology.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3 max-w-5xl mx-auto">
            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="rounded-xl bg-background p-6 border border-border">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Shield className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-heading text-lg font-semibold mb-2">Secure Payments</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">Blockchain-based escrow ensures funds are protected until work is completed and verified.</p>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }} className="rounded-xl bg-background p-6 border border-border">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-heading text-lg font-semibold mb-2">Verified Profiles</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">All workers go through verification to ensure quality and trustworthiness.</p>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }} className="rounded-xl bg-background p-6 border border-border">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Briefcase className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-heading text-lg font-semibold mb-2">Smart Contracts</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">Clear agreements with automated payment release upon job completion.</p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-hero py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="font-heading text-3xl font-bold text-primary-foreground lg:text-4xl">Ready to Get Started?</h2>
          <p className="mx-auto mt-4 max-w-md text-lg text-primary-foreground/80">Join HomeChain today and experience the future of domestic work.</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button size="lg" className="bg-secondary text-secondary-foreground hover:bg-secondary/90 font-heading font-semibold" asChild>
              <Link to="/register">Create Free Account</Link>
            </Button>
            <Button size="lg" variant="outline" className="border-primary-foreground/30 text-primary-foreground hover:bg-primary-foreground/10" asChild>
              <Link to="/workers">Find Workers</Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
