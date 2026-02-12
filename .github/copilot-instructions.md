# HomeChain AI Coding Agent Instructions

## Project Architecture

**Multi-tier Decentralized Platform**: Domestic worker marketplace with Django REST backend, React frontend, Stellar blockchain integration, and USSD support.

### Directory Structure
- `HomeChain/` - Django REST API backend (port 8000)
- `frontend/` - React + Vite + shadcn/ui frontend (port 5173)
- `smart_contracts/` - Soroban/Rust smart contracts for Stellar blockchain
- `HomeChain_ussd/` - Flask-based USSD interface for feature phones

## Backend (Django REST Framework)

### Core Apps & Responsibilities
- **accounts**: Custom user model with `USER_TYPES` (WORKER/EMPLOYER/ADMIN), Stellar wallet integration via `stellar_public_key`/`stellar_secret_key`, JWT auth
- **jobs**: Job postings with status lifecycle (DRAFT→OPEN→IN_PROGRESS→COMPLETED), JSONField for `skills_required`, payment types (FIXED/HOURLY)
- **contracts**: Digital agreements linking Job↔Employer↔Worker, signature tracking, payment schedules (FULL/HALF/MILESTONE/WEEKLY), status flow (DRAFT→PENDING→ACTIVE→COMPLETED)
- **payments**: Stellar blockchain integration via `stellar_client.py`, escrow wallet management, USDC transactions
- **ratings**: Bidirectional rating system after contract completion

### Key Patterns

**Custom User Model**: Extends `AbstractBaseUser` with `UserManager`. Always use `User` model from `accounts.models`, never Django's default. User types determine field relevance (e.g., `hourly_rate` for WORKER, `company_name` for EMPLOYER).

**JSONField Usage**: SQLite backend requires JSONField instead of PostgreSQL ArrayField. See `jobs.models.Job.skills_required`, `accounts.models.User.skills`, `contracts.models.Contract.working_days`.

**Authentication**: JWT via `rest_framework_simplejwt`. Tokens stored in localStorage. Registration auto-creates Stellar wallet (testnet). Login returns `{access, refresh}` tokens - frontend expects exact keys.

**API URL Pattern**: All endpoints under `/api/{app_name}/`. Example: `/api/accounts/register/`, `/api/jobs/jobs/`, `/api/contracts/contracts/{id}/sign/`.

**Permissions**: DRF permission classes in viewsets. Custom permissions in `{app}/permissions.py` check user_type and ownership (e.g., `IsEmployerOrReadOnly`, `IsOwnerOrReadOnly`).

### Stellar Blockchain Integration

**StellarEscrowClient** (`payments/stellar_client.py`):
- Testnet by default, configurable via `settings.STELLAR_NETWORK`
- Creates escrow accounts with `create_escrow_account()` - auto-funded via Friendbot on testnet
- Smart contract interactions via Soroban: `create_escrow()`, `release_payment()`, `dispute_payment()`
- Amount conversion: 1 XLM/USDC = 10,000,000 stroops
- Platform fee deduction on payment release

**Contract Lifecycle**: Job accepted → Contract created → Employer funds escrow → Worker completes → Employer approves → Smart contract releases payment.

### Development Commands

```bash
# Backend setup (from HomeChain/HomeChain/)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver  # http://localhost:8000

# Create superuser
python manage.py createsuperuser
```

**Database**: SQLite (`db.sqlite3`). Migrations in each app's `migrations/`. Always run `makemigrations` + `migrate` after model changes.

## Frontend (React + TypeScript)

### Tech Stack
- **React 18** + **TypeScript** + **Vite** (SWC for fast refresh)
- **shadcn/ui** (Radix UI primitives) + **Tailwind CSS**
- **React Router v6** for routing
- **TanStack Query** for server state
- **Axios** with interceptors for API calls

### Key Files
- `src/services/api.ts`: Axios instance with JWT interceptor, auto-detects backend URL via `VITE_API_BASE_URL`
- `src/context/AuthContext.tsx`: Global auth state, normalizes `full_name` ↔ `first_name`/`last_name` for compatibility
- `src/pages/`: Role-specific routes under `employer/` and `worker/` subdirectories
- `src/components/ui/`: shadcn/ui components (DO NOT edit manually, regenerate via CLI)

### Environment Setup
```bash
# From frontend/
bun install  # or npm install
cp .env.example .env.local
bun dev  # http://localhost:5173
```

**Required `.env.local`**: `VITE_API_BASE_URL=http://localhost:8000/api`

### API Service Pattern
```typescript
// services/api.ts defines base axios instance
import { API } from '@/services/api';

// Service modules export typed functions
export const jobService = {
  getJobs: () => API.get<Job[]>('/jobs/jobs/'),
  applyToJob: (id: number) => API.post(`/jobs/jobs/${id}/apply/`)
};
```

**Auth Flow**: Login/Register → tokens to localStorage → AuthContext fetches profile → normalizes user data → provides global `user`, `isAuthenticated`, `logout()`.

### Styling Conventions
- Tailwind utility-first with `clsx` + `tailwind-merge` via `cn()` helper
- shadcn/ui components use `class-variance-authority` for variants
- Responsive: mobile-first breakpoints (`sm:`, `md:`, `lg:`)

### Testing
```bash
bun test         # Run vitest once
bun test:watch   # Watch mode
```
Tests in `src/test/`, setup in `src/test/setup.ts` with `@testing-library/react`.

## Smart Contracts (Soroban/Rust)

**Location**: `smart_contracts/src/lib.rs`

**WorkContract**: Escrow agreement between client and worker.
- `init()`: Create agreement with client, worker, amount
- `fund()`: Client deposits tokens to contract
- `submit_work()`: Worker marks completion
- `approve_and_pay()`: Client releases funds to worker

**Deployment**: Soroban contracts deployed to Stellar testnet. Contract ID stored in Django `settings.STELLAR_ESCROW_CONTRACT_ID`.

**Build**: `cargo build --target wasm32-unknown-unknown --release` (requires Rust + wasm target).

## USSD Interface (Flask)

**Purpose**: Feature phone access for users without smartphones. Menu-driven text interface.

**Structure**: `HomeChain_ussd/ussd.py` - Flask app handling AT Africa's Gateway USSD webhook.

**Flow**: Main menu → Employer/Worker flows → AI-generated tips (`ussd_response/ai_response.py`) + SMS notifications.

## CORS & Integration

Backend allows all origins in development (`CORS_ALLOW_ALL_ORIGINS = True`). Frontend must run on port 5173 or 3000 for cookie handling. Both servers must run simultaneously for local dev.

## Testing & Debugging

**Backend Tests**: `python manage.py test {app_name}`. Use `tests.py` in each app.

**API Testing**: Django REST Framework browsable API at `http://localhost:8000/api/` (when authenticated).

**Common Issues**:
- JWT token expiry: 1 day default (`SIMPLE_JWT` in settings)
- Stellar testnet rate limits: Use friendbot sparingly
- File uploads: Check `MEDIA_URL` and `MEDIA_ROOT` settings
- CORS errors: Verify both servers running, check browser console

## Conventions

**Naming**: `snake_case` for Python, `camelCase` for TypeScript. Models use `UPPERCASE` for choice constants.

**Serializers**: Use nested serializers for related objects in read operations, IDs for writes. Example: `ContractSerializer` embeds `UserSerializer` for employer/worker on GET, accepts IDs on POST.

**ViewSets**: Prefer `ModelViewSet` with custom actions (`@action` decorator). Use `permission_classes` and `filter_backends` at viewset level.

**Error Handling**: Backend returns `{error: string, errors?: object}` format. Frontend displays via toast notifications.

## Security Notes

⚠️ **Production TODO**:
- Encrypt `stellar_secret_key` at rest (currently plaintext)
- Move `SECRET_KEY` and Stellar keys to environment variables
- Disable `DEBUG = True`
- Configure `ALLOWED_HOSTS` and CORS whitelist
- Use PostgreSQL instead of SQLite
- Implement rate limiting
