# Frontend-Backend Integration Setup Guide

## Quick Start

### 1. Backend Setup (Django)

```bash
cd HomeChain/HomeChain
.\env\Scripts\activate
python manage.py runserver
```

Backend runs on: `http://localhost:8000`

### 2. Frontend Setup (React)

```bash
cd HomeChain/frontend

# Create environment file (copy from .env.example)
# On Windows:
copy .env.example .env.local

# On Mac/Linux:
cp .env.example .env.local

npm install
npm run dev
```

Frontend runs on: `http://localhost:5173`

## Environment Configuration

### Frontend `.env.local`
```
VITE_API_BASE_URL=http://localhost:8000/api
```

## API Endpoints Reference

### Authentication
- `POST /api/accounts/register/` - Register
- `POST /api/accounts/login/` - Login
- `GET /api/accounts/profile/` - Get profile

### Jobs
- `GET /api/jobs/jobs/` - List jobs
- `POST /api/jobs/jobs/` - Create job
- `POST /api/jobs/jobs/{id}/apply/` - Apply

### Contracts
- `GET /api/contracts/contracts/` - List contracts
- `POST /api/contracts/contracts/{id}/sign/` - Sign contract

### Payments
- `GET /api/payments/wallets/me/` - Get wallet
- `GET /api/payments/transactions/` - List transactions

### Ratings
- `POST /api/ratings/ratings/rate_contract/` - Rate contract
- `GET /api/ratings/ratings/my_ratings/` - My ratings

## CORS Configuration

The backend allows requests from:
- `http://localhost:5173` (Vite)
- `http://localhost:3000` (React)
- `http://127.0.0.1:5173`
- `http://127.0.0.1:3000`

## Troubleshooting

### CORS Errors
✅ Verify both servers are running
✅ Check `.env.local` exists with correct URL
✅ Ensure frontend is on port 5173 or 3000

### Authentication Issues
✅ Check browser localStorage for tokens
✅ Verify JWT tokens in Authorization header
✅ Check token hasn't expired (1 day default)

### Connection Issues
✅ Backend: `http://localhost:8000`
✅ Frontend: `http://localhost:5173`
✅ Check browser console for errors
