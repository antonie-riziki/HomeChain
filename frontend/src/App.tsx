import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import Index from "./pages/Index";
import Login from "./pages/Login";
import Register from "./pages/Register";
import BrowseJobs from "./pages/BrowseJobs";
import BrowseWorkers from "./pages/BrowseWorkers";
import EmployerDashboard from "./pages/employer/Dashboard";
import EmployerJobs from "./pages/employer/Jobs";
import CreateJob from "./pages/employer/CreateJob";
import EmployerProfile from "./pages/employer/Profile";
import EmployerPayments from "./pages/employer/Payments";
import Contracts from "./pages/Contracts";
import WorkerDashboard from "./pages/worker/Dashboard";
import WorkerWallet from "./pages/worker/Wallet";
import WorkerProfile from "./pages/worker/Profile";
import WorkerRatings from "./pages/worker/Ratings";
import WorkerApplications from "./pages/worker/Applications";
import SavedJobs from "./pages/worker/SavedJobs";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <AuthProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/browse-jobs" element={<BrowseJobs />} />
            <Route path="/workers" element={<BrowseWorkers />} />

            {/* Employer Routes */}
            <Route path="/employer/dashboard" element={<EmployerDashboard />} />
            <Route path="/employer/jobs" element={<EmployerJobs />} />
            <Route path="/employer/jobs/create" element={<CreateJob />} />
            <Route path="/employer/contracts" element={<Contracts />} />
            <Route path="/employer/payments" element={<EmployerPayments />} />
            <Route path="/employer/profile" element={<EmployerProfile />} />

            {/* Worker Routes */}
            <Route path="/worker/dashboard" element={<WorkerDashboard />} />
            <Route path="/worker/jobs/browse" element={<BrowseJobs />} />
            <Route path="/worker/jobs/applied" element={<WorkerApplications />} />
            <Route path="/worker/wallet" element={<WorkerWallet />} />
            <Route path="/worker/profile" element={<WorkerProfile />} />
            <Route path="/worker/ratings" element={<WorkerRatings />} />
            <Route path="/worker/jobs/saved" element={<SavedJobs />} />
            <Route path="/worker/contracts" element={<Contracts />} />

            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
