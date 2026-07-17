# 🐐 Capricorn

**A unified personal finance platform for tracking investments, retirement planning, and financial analysis.**

> ### 🌐 [**Try the Live Demo → cap.gothamtechnologies.com**](https://cap.gothamtechnologies.com)
> *See it in action before you install!*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](docker/docker-compose.yml)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](backend/requirements.txt)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](frontend/package.json)

---

## ✨ Features

### 💰 Finance Manager
- **Plaid Bank Sync** - Auto-download transactions from Bank of America, AMEX, and more via Plaid API
- **CSV Import** - Manual import from bank statement CSV files (always available as backup)
- **ML-Powered Categorization** - 97% accuracy auto-tagging with 600+ patterns
- **Auto-Sync** - Transactions refresh every 15 minutes automatically
- **Budget Analysis** - Year-over-year spending comparison by category
- **Period Filtering** - View by month, year, or all-time

### 📈 Portfolio Manager
- **Hybrid Portfolios** - Manual entry OR auto-sync via Plaid (Schwab, Merrill, Voya, etc.)
- **Positions View** - Current holdings per ticker with FIFO lot drill-down: fee-inclusive
  average cost, % of portfolio, unrealized gain, and estimated tax owed (or sheltered) if sold
- **FIFO Tax-Lot Accounting** - Per-lot cost basis with fees, realized gains split
  short-term vs long-term using the IRS anniversary rule
- **Real-Time Prices** - TwelveData API integration for live stock quotes
- **Plaid Holdings Sync** - Real positions, cost basis, and buy/sell history from your broker
- **Tax-Aware Analysis** - Break-even calculations considering capital gains taxes
- **Distributions Tracking** - Dividend/interest history with YTD and lifetime totals
- **401k Support** - Institution-specific pricing for retirement fund classes

### 🏖️ Retirement Planner
- **30-Year Projections** - Compound growth calculations for all accounts
- **Asset Growth Charts** - Interactive visualization with Recharts
- **Withdrawal Analysis** - Tax-optimized retirement income planning
- **Dual-Income Support** - Model scenarios for couples

### 🧾 Tax Calculator
- **State Comparison** - Compare tax burden across all 50 states
- **2026 Tax Tables** - Federal progressive brackets with standard deductions (DB-driven, updated yearly)
- **Capital Gains** - Short-term vs long-term stacking across the 0/15/20% brackets, plus NIIT and state/local
- **Savings Calculator** - See potential savings from relocation

### 👤 Unified Profile
- **Single Data Entry** - One place for all your financial parameters
- **Sync from Portfolio** - Retirement balances (401k, IRA, trading) can track live
  portfolio values automatically instead of manual entry
- **Static Retirement Year** - Enter the year you plan to retire; time-based
  calculations never go stale
- **Auto-Refresh** - Changes propagate to all modules instantly

---

## 🏗️ Architecture

```
                    ┌──────────────┐    ┌──────────────┐
                    │  Plaid API   │    │  TwelveData  │
                    │ Bank & Invest│    │ Stock Prices │
                    └──────┬───────┘    └──────┬───────┘
                           │                   │
┌──────────────┐    ┌──────▼───────┐    ┌──────▼───────┐
│   Frontend   │───▶│   Backend    │───▶│  PostgreSQL  │
│  React/Vite  │    │   FastAPI    │    │   Database   │
│   Port 5001  │    │   Port 5002  │    │   Port 5003  │
└──────────────┘    └──────────────┘    └──────────────┘
                           │
                    ┌──────▼──────┐
                    │    Redis    │
                    │    Cache    │
                    │  Port 5004  │
                    └─────────────┘
```

**Tech Stack:**
- **Frontend:** React 18, TypeScript, Vite 8, Material-UI v7 (Node 22)
- **Backend:** FastAPI, Python 3.11, SQLAlchemy 2.0
- **Database:** PostgreSQL 15, Redis 7
- **Integrations:** Plaid API (bank + investment sync), TwelveData (stock prices)
- **Deployment:** Docker Compose, Kubernetes (GKE), GitLab CI/CD

---

## 🌐 Deployment Environments

Capricorn supports four deployment environments with automated CI/CD:

### **🖥️ DEV - Local Development**
- **Purpose:** Active development on your workstation
- **URL:** http://localhost:5001
- **Ports:** All exposed (5001-5004)
- **Features:** Hot reload, debugging, direct database access
- **Script:** `./scripts/run-dev.sh [start|stop|restart|bb|nuke]`

### **🧪 QA - Home Lab Testing**
- **Purpose:** Automated testing on local Kubernetes
- **URL:** http://192.168.1.180:5001
- **Deployment:** Automatic on `develop` branch push via GitLab CI/CD
- **Features:** Production-like environment, automated deployments
- **Script:** `./scripts/run-qa.sh [start|stop|restart|bb|nuke]` (manual)

### **🏠 PROD-Local - Home Lab Production** ⭐ PRIMARY
- **Purpose:** Live production deployment (replaces GCP)
- **URL:** https://cap.gothamtechnologies.com
- **Deployment:** Manual button in GitLab on `production` branch
- **Features:** Traefik reverse proxy, Let's Encrypt SSL, persistent storage
- **Cost Savings:** ~$400/year vs GCP hosting

### **☁️ PROD-GCP - Google Cloud** (Interview Demos Only)
- **Purpose:** Demo environment for interviews (use sparingly to save costs)
- **URL:** https://capricorn.gothamtechnologies.com ⚠️ **Not always running** - deployed on-demand
- **Deployment:** Manual button in GitLab on `production` branch
- **Features:** GKE Autopilot, Ingress, persistent volumes, auto-scaling
- **Script:** `./scripts/run-gcp.sh [start|stop|restart|bb|nuke]` (manual)
- **Note:** For testing, please use **cap.gothamtechnologies.com** (always available)

---

## 🚀 Quick Start

### Prerequisites
- **Linux** (Ubuntu 22.04+ recommended)
- Docker & Docker Compose
- Git

> ⚠️ **Note:** This application currently only runs on Linux. macOS and Windows support may be added in a future release.

### Installation (Simple Method)

```bash
# Clone the repository
git clone https://github.com/fiberoptix/capricorn.git
cd capricorn

# (Optional) Set up TwelveData API for live stock prices
cp backend/market_data/TwelveData_Config.example.txt backend/market_data/TwelveData_Config.txt
# Edit the file and add your API key from https://twelvedata.com

# Start DEV environment
./scripts/run-dev.sh start

# Wait for services to initialize (~30 seconds)
# Then open http://localhost:5001 in your browser
```

### Installation (Using Deployment Scripts)

Capricorn includes three environment-specific deployment scripts:

```bash
# DEV - Local development (hot reload)
./scripts/run-dev.sh start

# QA - Production-like testing
./scripts/run-qa.sh start

# GCP - Deploy to Google Cloud (requires GCP setup)
./scripts/run-gcp.sh start
```

**Script Commands:**
- `start` - Start containers (default)
- `stop` - Stop containers
- `restart` - Restart containers
- `bb` - Burn & Build (rebuild from scratch + run QA tests)
- `nuke` - Complete destruction (requires typing 'NUKE')

> ℹ️ **Note:** The QA host is deployed by the GitLab pipeline (registry images), so
> `run-qa.sh` cleanup targets don't match pipeline-deployed resources — clean the QA
> box manually with `docker` commands when needed.

### 🎮 Try with Demo Data (Recommended for First-Time Users)

Want to see all features in action right away? Import the included demo dataset:

1. Navigate to http://localhost:5001
2. Go to the **Data** tab
3. Click **Import Data**
4. Select `demo_UserData/Capricorn_DEMO_Data.json` from the repository
5. All modules will populate with sample data for "Bob & Mary Smith"

**Demo Data Includes:**
- 23 months of realistic transactions (Jan 2024 - Nov 2025)
- 3 investment portfolios (~$200K total)
- Complete profile with retirement projections
- Pre-configured tax settings (NY, Married Filing Jointly)

This lets you explore all features without entering your own data first!

---

### First-Time Setup (Your Own Data)

1. Navigate to http://localhost:5001
2. Go to **Profile** tab and enter your financial information
3. Connect banks via **Data & Plaid → Plaid Connectivity** (or import CSV via **Finance → Upload**)
4. Add portfolios via **Portfolio → New Portfolio** (Manual or Connect via Plaid)

---

## ⚙️ Configuration

### Plaid API (Optional - For Automatic Bank & Investment Sync)

Connect your bank accounts and brokerage for automatic transaction and portfolio sync:

1. Sign up at [dashboard.plaid.com](https://dashboard.plaid.com) (free to start)
2. Set environment variables before starting Docker:

```bash
export PLAID_CLIENT_ID=your_client_id
export PLAID_SECRET=your_secret
export PLAID_ENV=production    # or 'sandbox' for testing
```

3. Start the app and go to **Data & Plaid → Plaid Connectivity** to connect banks
4. For investments, go to **Portfolio → New Portfolio → Connect via Plaid**

**Without Plaid:** The app works fully with manual CSV imports and manual portfolio entry. Plaid is additive -- if credentials aren't set, Plaid features are hidden.

**Cost:** ~$0.30/account/month for bank transactions, ~$0.35/account/month for investment data. Sync frequency doesn't affect cost.

### TwelveData API (Optional - For Live Stock Prices)

For real-time stock prices, get a free API key from [TwelveData](https://twelvedata.com/):

1. Edit `backend/market_data/TwelveData_Config.txt`
2. Replace `YOUR_API_KEY_HERE` with your actual API key
3. Restart the backend container

```ini
PROVIDER=twelve_data
API_KEY=YOUR_API_KEY_HERE
TIMEZONE=America/New_York
TTL_SECONDS=300
MAX_BATCH=8
```

---

## 📁 Project Structure

```
capricorn/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   └── core/            # Config, database
│   ├── migrations/          # SQL migrations
│   └── requirements.txt
├── frontend/                # React frontend
│   ├── src/
│   │   ├── modules/         # Feature modules
│   │   ├── components/      # Shared components
│   │   └── pages/           # Page components
│   └── package.json
├── database/
│   └── init/                # Database initialization scripts
├── docker/
│   └── docker-compose.yml   # Docker orchestration
└── README.md
```

---

## 🔄 CI/CD Pipeline

**GitLab CI/CD integration for automated deployments:**

### Workflow

**QA Deployment (Automatic):**
```bash
# Push to develop branch
git push gitlab develop

# Pipeline automatically:
# 1. Builds frontend + backend Docker images
# 2. Pushes to GitLab Container Registry
# 3. Deploys to QA host (192.168.1.180)
# Result: App live in ~3-5 minutes at http://192.168.1.180:5001
```

**PROD-Local Deployment (Manual):** ⭐ PRIMARY
```bash
# Merge develop to production
git checkout production
git merge develop
git push gitlab production

# In GitLab UI:
# 1. Go to Pipelines
# 2. Click "Deploy" button next to deploy_prod_local
# 3. Wait ~2 minutes for deployment
# Result: App live at https://cap.gothamtechnologies.com
```

**PROD-GCP Deployment (Manual - Interviews Only):**
```bash
# Same as above, but click deploy_prod_gcp instead
# In GitLab UI:
# 1. Go to Pipelines
# 2. Click "Deploy" button next to deploy_prod_gcp
# 3. Wait 10-15 minutes for GCP deployment
# Result: App live at https://capricorn.gothamtechnologies.com
```

### Pipeline Stages

| Stage | Description | Duration |
|-------|-------------|----------|
| `build_frontend` | Vite production build | ~40s |
| `build_backend` | FastAPI Docker image | ~30s |
| `push_images` | Push to Container Registry | ~30s |
| `scan` | SonarQube code quality analysis | ~2-3m |
| `deploy_qa` | Deploy to QA host (develop branch, auto) | ~60s |
| `deploy_prod_local` | Deploy to PROD-Local (production branch, manual) | ~2m |
| `deploy_prod_gcp` | Deploy to GCP (production branch, manual, interviews only) | ~10-15m |

**CI/CD Variables Required (GitLab Settings → CI/CD → Variables):**
- `CI_REGISTRY_USER` - GitLab registry username
- `CI_REGISTRY_PASSWORD` - GitLab registry password
- `SSH_PRIVATE_KEY` - SSH key for QA deployment
- `GCP_SERVICE_ACCOUNT_KEY` - GCP service account JSON (base64)
- `GCP_PROJECT_ID` - Google Cloud project ID

---

## 🔧 Development

### Local Development

The recommended workflow is the full Docker stack (`./scripts/run-dev.sh start`) —
both frontend (Vite hot reload) and backend (`uvicorn --reload`) pick up source
changes live via volume mounts, no rebuild needed.

> ⚠️ **npm must run inside the container.** If your working copy lives on a network
> share (NAS/SMB), host-side `npm install` fails on symlinks and corrupts
> `node_modules`. For dependency changes:
>
> ```bash
> # Update the lockfile inside a container, then rebuild the image
> docker run --rm -v $PWD/frontend:/app -w /app node:22-alpine npm install --package-lock-only
> docker compose -f docker/docker-compose.dev.yml build frontend
> docker compose -f docker/docker-compose.dev.yml up -d --force-recreate --renew-anon-volumes frontend
> ```

### API Documentation

Available in **DEV only** (disabled when `DEBUG=false`, i.e. in QA/PROD):
- Swagger UI: http://localhost:5002/docs
- ReDoc: http://localhost:5002/redoc

> Note: all mutating API requests (POST/PUT/PATCH/DELETE) require the
> `X-Capricorn-Client: 1` header — scripts and `curl` calls must send it or
> they receive a 403.

---

## 📊 Data Import

### Plaid (Recommended)

Connect your banks directly for automatic transaction sync:
- **Bank of America** - Checking, savings, credit cards
- **American Express** - Credit cards
- **Charles Schwab** - Brokerage (requires OAuth registration on Plaid Dashboard)
- **Merrill Lynch** - IRA, brokerage
- **Voya / BNY Mellon** - 401k retirement accounts
- And thousands more via Plaid

Transactions auto-sync every 15 minutes. Internal transfers and credit card payments are automatically filtered.

### CSV Import (Manual Fallback)

The ML tagger recognizes CSV files from:
- Bank of America (checking and credit)
- American Express
- Generic CSV format

```csv
Date,Description,Amount,Category
2025-01-15,AMAZON.COM,49.99,Shopping
2025-01-16,WHOLE FOODS,125.43,Groceries
```

### Export/Import

Use the **Data & Plaid** tab to:
- **Export** all data to JSON backup
- **Import** from a previous backup
- **Clear** all data and start fresh

Plaid connections (access tokens, sync cursors, cutoff dates) are preserved in exports. After importing a backup on a new environment, Plaid syncs continue automatically -- no reconnecting needed.

**Safety features:** Plaid access tokens in export files are Fernet-encrypted (requires
the same `EXPORT_ENCRYPTION_KEY` on both environments to round-trip). Import and Clear
require explicit confirmation tokens and automatically snapshot the database before
touching anything. Imports are transactional -- a bad file leaves the database untouched.

---

## 🛡️ Security Notes

This is a **single-user personal finance application** designed for home lab use:

- No authentication system (designed for private network)
- All data stored locally in PostgreSQL
- No data leaves your network except optional API calls to:
  - **Plaid** - Bank/investment connectivity (your bank credentials are never shared with the app)
  - **TwelveData** - Stock price quotes

**Built-in hardening** (2026 security pass):
- CORS pinned to known origins; all mutating requests require a custom client header
- Plaid tokens encrypted in export files; API docs disabled outside DEV
- Destructive operations (clear/import) require confirmation tokens + auto-snapshot first
- Demo mode denies all mutations by default; 500 errors are sanitized
- Upload size limits; parameterized SQL throughout

**For production use**, consider adding:
- Authentication layer
- HTTPS/TLS
- Network isolation
- Regular backups

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Plaid](https://plaid.com/) for bank and investment connectivity
- [TwelveData](https://twelvedata.com/) for stock market API
- [Material-UI](https://mui.com/) for React components
- [Recharts](https://recharts.org/) for interactive charts
- Built with ❤️ using [Cursor](https://cursor.sh/) AI

---

## 📫 Contact

- GitHub: [@fiberoptix](https://github.com/fiberoptix)
- Project Link: [https://github.com/fiberoptix/capricorn](https://github.com/fiberoptix/capricorn)

