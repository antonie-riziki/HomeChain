import API from './api';

export const authService = {
  register: (data: Record<string, unknown>) => API.post('/accounts/register/', data),
  login: (data: { email: string; password: string }) => API.post('/accounts/login/', data),
  logout: () => API.post('/accounts/logout/'),
  refreshToken: (refresh: string) => API.post('/accounts/token/refresh/', { refresh }),
  getProfile: () => API.get('/accounts/profile/'),
  updateProfile: (data: Record<string, unknown>) => API.patch('/accounts/profile/', data),
};

export const jobService = {
  browseJobs: (params?: Record<string, unknown>) => API.get('/jobs/jobs/browse/', { params }),
  getMyJobs: () => API.get('/jobs/jobs/my_jobs/'),
  getJob: (id: string) => API.get(`/jobs/jobs/${id}/`),
  createJob: (data: Record<string, unknown>) => API.post('/jobs/jobs/', data),
  updateJob: (id: string, data: Record<string, unknown>) => API.put(`/jobs/jobs/${id}/`, data),
  deleteJob: (id: string) => API.delete(`/jobs/jobs/${id}/`),
  publishJob: (id: string) => API.post(`/jobs/jobs/${id}/publish/`),
  applyForJob: (id: string, data: Record<string, unknown>) => API.post(`/jobs/jobs/${id}/apply/`, data),
  getApplications: (id: string) => API.get(`/jobs/jobs/${id}/applications/`),
  acceptApplication: (id: string, data: Record<string, unknown>) => API.post(`/jobs/jobs/${id}/accept_application/`, data),
  completeJob: (id: string) => API.post(`/jobs/jobs/${id}/complete/`),
  saveJob: (id: string) => API.post(`/jobs/jobs/${id}/save/`),
  unsaveJob: (id: string) => API.post(`/jobs/jobs/${id}/unsave/`),
  getSavedJobs: () => API.get('/jobs/jobs/saved/'),
  getMyApplications: () => API.get('/jobs/applications/'),
  withdrawApplication: (id: string) => API.post(`/jobs/applications/${id}/withdraw/`),
};

export const contractService = {
  getContracts: () => API.get('/contracts/contracts/'),
  getContract: (id: string) => API.get(`/contracts/contracts/${id}/`),
  createContract: (data: Record<string, unknown>) => API.post('/contracts/contracts/', data),
  signContract: (id: string) => API.post(`/contracts/contracts/${id}/sign/`),
  downloadPDF: (id: string) => API.get(`/contracts/contracts/${id}/download_pdf/`, { responseType: 'blob' }),
  completeContract: (id: string) => API.post(`/contracts/contracts/${id}/complete/`),
  disputeContract: (id: string, data: Record<string, unknown>) => API.post(`/contracts/contracts/${id}/dispute/`, data),
  getTemplates: () => API.get('/contracts/templates/'),
  createFromTemplate: (id: string, data: Record<string, unknown>) => API.post(`/contracts/templates/${id}/create_contract/`, data),
  getMilestones: () => API.get('/contracts/milestones/'),
  createMilestone: (data: Record<string, unknown>) => API.post('/contracts/milestones/', data),
  completeMilestone: (id: string) => API.post(`/contracts/milestones/${id}/complete/`),
};

export const paymentService = {
  getWallet: () => API.get('/payments/wallets/me/'),
  getTransactions: () => API.get('/payments/wallets/me/transactions/'),
  syncWallet: () => API.post('/payments/wallets/me/sync/'),
  getEscrows: () => API.get('/payments/escrows/'),
  getEscrow: (id: string) => API.get(`/payments/escrows/${id}/`),
  approveEscrow: (id: string) => API.post(`/payments/escrows/${id}/approve/`),
  disputeEscrow: (id: string, data: Record<string, unknown>) => API.post(`/payments/escrows/${id}/dispute/`, data),
  getEscrowStatus: (id: string) => API.get(`/payments/escrows/${id}/status/`),
  getWithdrawals: () => API.get('/payments/withdrawals/'),
  requestWithdrawal: (data: Record<string, unknown>) => API.post('/payments/withdrawals/', data),
  cancelWithdrawal: (id: string) => API.delete(`/payments/withdrawals/${id}/`),
  getAllTransactions: () => API.get('/payments/transactions/'),
  getCurrentFee: () => API.get('/payments/fees/current/'),
};

export const ratingService = {
  rateContract: (data: Record<string, unknown>) => API.post('/ratings/ratings/rate_contract/', data),
  getMyRatings: () => API.get('/ratings/ratings/my_ratings/'),
  getMyReviews: () => API.get('/ratings/ratings/my_reviews/'),
  getPendingRatings: () => API.get('/ratings/ratings/pending/'),
  respondToRating: (id: string, data: Record<string, unknown>) => API.post(`/ratings/ratings/${id}/respond/`, data),
  flagRating: (id: string, data: Record<string, unknown>) => API.post(`/ratings/ratings/${id}/flag/`, data),
  getPublicSummary: (userId: string) => API.get(`/ratings/summaries/public/?user_id=${userId}`),
  getTopWorkers: () => API.get('/ratings/summaries/top_workers/'),
};

export const userService = {
  listWorkers: (params?: Record<string, unknown>) => API.get('/accounts/users/workers/', { params }),
  getSkills: () => API.get('/accounts/skills/'),
  getSkillCategories: () => API.get('/accounts/skills/categories/'),
  getMySkills: () => API.get('/accounts/worker-skills/'),
  addSkill: (data: Record<string, unknown>) => API.post('/accounts/worker-skills/', data),
  removeSkill: (id: string) => API.delete(`/accounts/worker-skills/${id}/`),
  getDocuments: () => API.get('/accounts/documents/'),
  uploadDocument: (data: FormData) => API.post('/accounts/documents/', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  deleteDocument: (id: string) => API.delete(`/accounts/documents/${id}/`),
  submitVerification: () => API.post('/accounts/verification-requests/'),
  toggleAvailability: () => API.patch('/accounts/users/toggle_availability/'),
};
