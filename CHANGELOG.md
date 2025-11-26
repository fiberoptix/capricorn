# Changelog

All notable changes to Capricorn will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-beta] - 2025-11-26

### 🎉 Initial Beta Release

This is the first public release of Capricorn, a unified personal finance platform.

### Added

#### Finance Manager
- CSV import for bank transactions (Bank of America, American Express, generic format)
- ML-powered auto-categorization with 97% accuracy (600+ patterns)
- Transaction management with CRUD operations
- Budget analysis with year-over-year comparison
- Period filtering (month, year, all-time)
- Spending summary cards with averages

#### Portfolio Manager
- Portfolio CRUD operations (create, edit, delete)
- Transaction tracking (buy/sell with cost basis)
- Real-time stock prices via TwelveData API
- Tax-aware break-even analysis
- Market price management with background refresh
- Advanced analytics dashboard

#### Retirement Planner
- 30-year financial projections
- Compound growth calculations for all account types
- Interactive asset growth charts (Recharts)
- Withdrawal analysis with tax optimization
- Dual-income support for couples
- Transition analysis for retirement planning

#### Tax Calculator
- 2025 federal tax brackets (progressive calculation)
- State tax comparison across all 50 states
- Standard deduction support
- Short-term vs long-term capital gains
- NIIT (Net Investment Income Tax) calculation
- Savings calculator for state relocation

#### Profile System
- Unified profile with 49 configurable fields
- Single source of truth for all modules
- Auto-refresh across all modules on save

#### Data Management
- Full data export to JSON
- Import from JSON backup
- Clear all data with bootstrap user recreation

### Technical Features
- Docker Compose deployment (4 containers)
- PostgreSQL 15 database with migrations
- Redis caching
- FastAPI backend with async support
- React 18 frontend with TypeScript
- Material-UI + Tailwind CSS styling
- Background task system for long operations

---

## Future Roadmap

### Planned Features
- [ ] Dark mode support
- [ ] PDF export functionality
- [ ] Mobile responsiveness improvements
- [ ] Additional bank CSV formats
- [ ] Authentication layer (optional)
- [ ] API rate limiting
- [ ] Comprehensive documentation

---

*For detailed development history, see the project documentation in `/project/` directory.*

