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
- **Transaction Tracking** - Import bank statements from CSV (supports multiple banks)
- **ML-Powered Categorization** - 97% accuracy auto-tagging with 600+ patterns
- **Budget Analysis** - Year-over-year spending comparison by category
- **Period Filtering** - View by month, year, or all-time

### 📈 Portfolio Manager
- **Portfolio CRUD** - Create and manage multiple investment portfolios
- **Real-Time Prices** - TwelveData API integration for live stock quotes
- **Tax-Aware Analysis** - Break-even calculations considering capital gains taxes
- **Holdings Tracking** - Buy/sell transactions with cost basis tracking

### 🏖️ Retirement Planner
- **30-Year Projections** - Compound growth calculations for all accounts
- **Asset Growth Charts** - Interactive visualization with Recharts
- **Withdrawal Analysis** - Tax-optimized retirement income planning
- **Dual-Income Support** - Model scenarios for couples

### 🧾 Tax Calculator
- **State Comparison** - Compare tax burden across all 50 states
- **2025 Tax Tables** - Federal progressive brackets with standard deductions
- **Capital Gains** - Short-term vs long-term rate calculations
- **Savings Calculator** - See potential savings from relocation

### 👤 Unified Profile
- **Single Data Entry** - One place for all your financial parameters
- **Auto-Refresh** - Changes propagate to all modules instantly
- **49 Configurable Fields** - Comprehensive personal finance modeling

---

## 🏗️ Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
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
- **Frontend:** React 18, TypeScript, Vite, Material-UI, Tailwind CSS
- **Backend:** FastAPI, Python 3.11, SQLAlchemy 2.0
- **Database:** PostgreSQL 15, Redis 7
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
- **URL:** https://capricorn.gothamtechnologies.com
- **Deployment:** Manual button in GitLab on `production` branch
- **Features:** GKE Autopilot, Ingress, persistent volumes, auto-scaling
- **Script:** `./scripts/run-gcp.sh [start|stop|restart|bb|nuke]` (manual)

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
3. Import transactions via **Finance → Upload** (CSV format)
4. Add portfolios via **Portfolio → New Portfolio**

---

## ⚙️ Configuration

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

```bash
# Start just the database and redis
cd docker
docker-compose up -d postgres redis

# Backend development
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5002

# Frontend development
cd frontend
npm install
npm run dev
```

### API Documentation

Once running, access the API docs at:
- Swagger UI: http://localhost:5002/docs
- ReDoc: http://localhost:5002/redoc

---

## 📊 Data Import

### Supported Banks

The ML tagger recognizes transactions from:
- Bank of America
- American Express
- Chase (coming soon)
- Generic CSV format

### CSV Format

```csv
Date,Description,Amount,Category
2025-01-15,AMAZON.COM,49.99,Shopping
2025-01-16,WHOLE FOODS,125.43,Groceries
```

### Export/Import

Use the **Data** tab to:
- **Export** all data to JSON backup
- **Import** from a previous backup
- **Clear** all data and start fresh

---

## 🛡️ Security Notes

This is a **single-user personal finance application** designed for home lab use:

- No authentication system (designed for private network)
- All data stored locally in PostgreSQL
- No data leaves your network (except optional TwelveData API calls)

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

- [TwelveData](https://twelvedata.com/) for stock market API
- [Material-UI](https://mui.com/) for React components
- [Recharts](https://recharts.org/) for interactive charts
- Built with ❤️ using [Cursor](https://cursor.sh/) AI

---

## 📫 Contact

- GitHub: [@fiberoptix](https://github.com/fiberoptix)
- Project Link: [https://github.com/fiberoptix/capricorn](https://github.com/fiberoptix/capricorn)

