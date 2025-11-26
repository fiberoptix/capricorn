# 🐐 Capricorn

**A unified personal finance platform for tracking investments, retirement planning, and financial analysis.**

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
- **Deployment:** Docker Compose

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/fiberoptix/capricorn.git
cd capricorn

# Copy environment files
cp .env.example .env
cp backend/market_data/TwelveData_Config.example.txt backend/market_data/TwelveData_Config.txt

# Start all services
cd docker
docker-compose up -d --build

# Wait for services to initialize (~30 seconds)
# Then open http://localhost:5001 in your browser
```

### First-Time Setup

1. Navigate to http://localhost:5001
2. Go to **Profile** tab and enter your financial information
3. Import transactions via **Finance → Upload** (CSV format)
4. Add portfolios via **Portfolio → New Portfolio**

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
POSTGRES_USER=capricorn
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=capricorn_db

# Build
BUILD_NUMBER=1
```

### TwelveData API (Optional)

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

