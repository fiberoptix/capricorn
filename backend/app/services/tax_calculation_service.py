"""
Comprehensive Tax Calculation Service
Queries database tables for accurate tax calculations
Handles income tax, short-term and long-term capital gains
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class TaxCalculationService:
    """Database-driven tax calculation service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _get_standard_deduction(self, year: int, filing_status: str) -> Decimal:
        """Get federal standard deduction from database"""
        result = await self.db.execute(text("""
            SELECT federal_amount FROM standard_deductions 
            WHERE year = :year AND filing_status = :filing_status
        """), {"year": year, "filing_status": filing_status})
        
        row = result.fetchone()
        return Decimal(str(row[0])) if row else Decimal('0')
    
    async def _get_state_standard_deduction(self, year: int, state: str, filing_status: str) -> Decimal:
        """Get state standard deduction from database"""
        result = await self.db.execute(text("""
            SELECT amount FROM state_standard_deductions 
            WHERE year = :year AND state_code = :state AND filing_status = :filing_status
        """), {"year": year, "state": state, "filing_status": filing_status})
        
        row = result.fetchone()
        return Decimal(str(row[0])) if row else Decimal('0')
    
    async def _calculate_federal_income_tax(
        self, 
        taxable_income: Decimal, 
        year: int, 
        filing_status: str
    ) -> Tuple[Decimal, Decimal]:
        """Calculate federal income tax using progressive brackets"""
        # Get brackets from database
        result = await self.db.execute(text("""
            SELECT bracket_min, bracket_max, rate
            FROM federal_tax_brackets
            WHERE year = :year AND filing_status = :filing_status
            ORDER BY bracket_min
        """), {"year": year, "filing_status": filing_status})
        
        brackets = result.fetchall()
        tax_owed = Decimal('0')
        marginal_rate = Decimal('0')
        
        for bracket_min, bracket_max, rate in brackets:
            bracket_min = Decimal(str(bracket_min))
            bracket_max = Decimal(str(bracket_max)) if bracket_max else Decimal('999999999')
            rate = Decimal(str(rate))
            
            if taxable_income > bracket_min:
                taxable_in_bracket = min(taxable_income, bracket_max) - bracket_min
                tax_owed += taxable_in_bracket * rate
                marginal_rate = rate  # Track the highest bracket we hit
                
                if taxable_income <= bracket_max:
                    break
        
        return tax_owed, marginal_rate
    
    async def _calculate_state_income_tax(
        self, 
        taxable_income: Decimal, 
        year: int, 
        state: str,
        filing_status: str
    ) -> Tuple[Decimal, Decimal]:
        """Calculate state income tax using progressive brackets"""
        # Handle states with no income tax
        no_tax_states = ['FL', 'TX', 'WA', 'NV', 'SD', 'WY', 'AK', 'TN', 'NH']
        if state in no_tax_states:
            return Decimal('0'), Decimal('0')
        
        # Get brackets from database
        result = await self.db.execute(text("""
            SELECT bracket_min, bracket_max, rate
            FROM state_tax_brackets
            WHERE year = :year AND state_code = :state AND filing_status = :filing_status
            ORDER BY bracket_min
        """), {"year": year, "state": state, "filing_status": filing_status})
        
        brackets = result.fetchall()
        if not brackets:
            # Fallback to flat 5% if state not in database
            return taxable_income * Decimal('0.05'), Decimal('0.05')
        
        tax_owed = Decimal('0')
        marginal_rate = Decimal('0')
        
        for bracket_min, bracket_max, rate in brackets:
            bracket_min = Decimal(str(bracket_min))
            bracket_max = Decimal(str(bracket_max)) if bracket_max else Decimal('999999999')
            rate = Decimal(str(rate))
            
            if taxable_income > bracket_min:
                taxable_in_bracket = min(taxable_income, bracket_max) - bracket_min
                tax_owed += taxable_in_bracket * rate
                marginal_rate = rate
                
                if taxable_income <= bracket_max:
                    break
        
        return tax_owed, marginal_rate
    
    async def _calculate_capital_gains_tax(
        self,
        gains: Decimal,
        total_income: Decimal,
        year: int,
        filing_status: str
    ) -> Tuple[Decimal, Decimal]:
        """Calculate long-term capital gains tax using preferential rates"""
        # Get brackets from database
        result = await self.db.execute(text("""
            SELECT bracket_min, bracket_max, rate
            FROM capital_gains_brackets
            WHERE year = :year AND filing_status = :filing_status
            ORDER BY bracket_min
        """), {"year": year, "filing_status": filing_status})
        
        brackets = result.fetchall()
        
        for bracket_min, bracket_max, rate in brackets:
            bracket_min = Decimal(str(bracket_min))
            bracket_max = Decimal(str(bracket_max)) if bracket_max else Decimal('999999999')
            rate = Decimal(str(rate))
            
            if total_income <= bracket_max:
                return gains * rate, rate
        
        # Highest bracket
        return gains * Decimal('0.20'), Decimal('0.20')
    
    async def _calculate_niit(
        self,
        investment_income: Decimal,
        total_income: Decimal,
        year: int,
        filing_status: str
    ) -> Decimal:
        """Calculate Net Investment Income Tax if applicable"""
        result = await self.db.execute(text("""
            SELECT threshold, rate FROM niit_thresholds
            WHERE year = :year AND filing_status = :filing_status
        """), {"year": year, "filing_status": filing_status})
        
        row = result.fetchone()
        if not row:
            return Decimal('0')
        
        threshold = Decimal(str(row[0]))
        rate = Decimal(str(row[1]))
        
        if total_income > threshold:
            excess = total_income - threshold
            return min(investment_income, excess) * rate
        
        return Decimal('0')
    
    async def calculate_income_tax(
        self,
        income: float,
        filing_status: str,
        state: str,
        local_tax_rate: float = 0.0,
        year: int = 2025
    ) -> Dict[str, Any]:
        """
        Calculate total tax on ordinary income
        
        Args:
            income: Gross income
            filing_status: 'single', 'married_filing_jointly', etc.
            state: Two-letter state code (e.g., 'NY')
            local_tax_rate: Local tax rate as decimal (e.g., 0.01 for 1%)
            year: Tax year (default 2025)
        
        Returns:
            Comprehensive tax breakdown
        """
        income_dec = Decimal(str(income))
        
        # Get standard deductions
        federal_std_deduction = await self._get_standard_deduction(year, filing_status)
        state_std_deduction = await self._get_state_standard_deduction(year, state, filing_status)
        
        # Calculate taxable income
        federal_taxable = max(Decimal('0'), income_dec - federal_std_deduction)
        state_taxable = max(Decimal('0'), income_dec - state_std_deduction)
        
        # Calculate taxes
        federal_tax, federal_marginal = await self._calculate_federal_income_tax(
            federal_taxable, year, filing_status
        )
        state_tax, state_marginal = await self._calculate_state_income_tax(
            state_taxable, year, state, filing_status
        )
        local_tax = income_dec * Decimal(str(local_tax_rate))
        
        total_tax = federal_tax + state_tax + local_tax
        after_tax_income = income_dec - total_tax
        effective_rate = (total_tax / income_dec) if income_dec > 0 else Decimal('0')
        
        return {
            "gross_income": float(income_dec),
            "federal": {
                "standard_deduction": float(federal_std_deduction),
                "taxable_income": float(federal_taxable),
                "tax": float(federal_tax),
                "marginal_rate": float(federal_marginal),
                "effective_rate": float(federal_tax / income_dec) if income_dec > 0 else 0.0
            },
            "state": {
                "state_code": state,
                "standard_deduction": float(state_std_deduction),
                "taxable_income": float(state_taxable),
                "tax": float(state_tax),
                "marginal_rate": float(state_marginal),
                "effective_rate": float(state_tax / income_dec) if income_dec > 0 else 0.0
            },
            "local": {
                "tax": float(local_tax),
                "rate": local_tax_rate
            },
            "total_tax": float(total_tax),
            "after_tax_income": float(after_tax_income),
            "effective_rate": float(effective_rate)
        }
    
    async def calculate_short_term_capital_gains_tax(
        self,
        gains: float,
        base_income: float,
        filing_status: str,
        state: str,
        local_tax_rate: float = 0.0,
        purchase_date: Optional[date] = None,
        sale_date: Optional[date] = None,
        year: int = 2025
    ) -> Dict[str, Any]:
        """
        Calculate tax on short-term capital gains (held ≤365 days)
        Taxed as ordinary income
        
        Args:
            gains: Capital gains amount
            base_income: Income before gains
            filing_status: Tax filing status
            state: State code
            local_tax_rate: Local tax rate
            purchase_date: Date asset was purchased
            sale_date: Date asset was sold
            year: Tax year
        
        Returns:
            Tax calculation breakdown
        """
        gains_dec = Decimal(str(gains))
        base_income_dec = Decimal(str(base_income))
        total_income = base_income_dec + gains_dec
        
        # Calculate holding period if dates provided
        holding_days = None
        if purchase_date and sale_date:
            holding_days = (sale_date - purchase_date).days
            if holding_days > 365:
                return {
                    "error": "Holding period > 365 days. Use long-term calculation.",
                    "holding_period_days": holding_days
                }
        
        # Get standard deductions
        federal_std_deduction = await self._get_standard_deduction(year, filing_status)
        state_std_deduction = await self._get_state_standard_deduction(year, state, filing_status)
        
        # Calculate tax on base income alone
        base_federal_taxable = max(Decimal('0'), base_income_dec - federal_std_deduction)
        base_federal_tax, _ = await self._calculate_federal_income_tax(
            base_federal_taxable, year, filing_status
        )
        
        base_state_taxable = max(Decimal('0'), base_income_dec - state_std_deduction)
        base_state_tax, _ = await self._calculate_state_income_tax(
            base_state_taxable, year, state, filing_status
        )
        
        # Calculate tax with gains included
        total_federal_taxable = max(Decimal('0'), total_income - federal_std_deduction)
        total_federal_tax, marginal_rate = await self._calculate_federal_income_tax(
            total_federal_taxable, year, filing_status
        )
        
        total_state_taxable = max(Decimal('0'), total_income - state_std_deduction)
        total_state_tax, state_marginal = await self._calculate_state_income_tax(
            total_state_taxable, year, state, filing_status
        )
        
        # Tax on gains = difference
        federal_tax_on_gains = total_federal_tax - base_federal_tax
        state_tax_on_gains = total_state_tax - base_state_tax
        
        # NIIT if applicable
        niit_tax = await self._calculate_niit(gains_dec, total_income, year, filing_status)
        
        # Local tax on gains
        local_tax = gains_dec * Decimal(str(local_tax_rate))
        
        total_tax_on_gains = federal_tax_on_gains + state_tax_on_gains + niit_tax + local_tax
        after_tax_gains = gains_dec - total_tax_on_gains
        effective_rate = (total_tax_on_gains / gains_dec) if gains_dec > 0 else Decimal('0')
        
        return {
            "holding_period_days": holding_days,
            "gains_type": "short_term",
            "gains_amount": float(gains_dec),
            "base_income": float(base_income_dec),
            "federal_tax": float(federal_tax_on_gains),
            "federal_marginal_rate": float(marginal_rate),
            "state_tax": float(state_tax_on_gains),
            "state_marginal_rate": float(state_marginal),
            "niit_tax": float(niit_tax),
            "local_tax": float(local_tax),
            "total_tax": float(total_tax_on_gains),
            "effective_rate": float(effective_rate),
            "after_tax_gains": float(after_tax_gains)
        }
    
    async def calculate_long_term_capital_gains_tax(
        self,
        gains: float,
        base_income: float,
        filing_status: str,
        state: str,
        local_tax_rate: float = 0.0,
        purchase_date: Optional[date] = None,
        sale_date: Optional[date] = None,
        year: int = 2025
    ) -> Dict[str, Any]:
        """
        Calculate tax on long-term capital gains (held >365 days)
        Uses preferential capital gains rates
        
        Args:
            gains: Capital gains amount
            base_income: Income before gains
            filing_status: Tax filing status
            state: State code
            local_tax_rate: Local tax rate
            purchase_date: Date asset was purchased
            sale_date: Date asset was sold
            year: Tax year
        
        Returns:
            Tax calculation breakdown
        """
        gains_dec = Decimal(str(gains))
        base_income_dec = Decimal(str(base_income))
        total_income = base_income_dec + gains_dec
        
        # Calculate holding period if dates provided
        holding_days = None
        if purchase_date and sale_date:
            holding_days = (sale_date - purchase_date).days
            if holding_days <= 365:
                return {
                    "error": "Holding period ≤ 365 days. Use short-term calculation.",
                    "holding_period_days": holding_days
                }
        
        # Get standard deductions for taxable income calculation
        federal_std_deduction = await self._get_standard_deduction(year, filing_status)
        state_std_deduction = await self._get_state_standard_deduction(year, state, filing_status)
        
        # Federal long-term capital gains tax (preferential rates)
        federal_taxable = max(Decimal('0'), total_income - federal_std_deduction)
        federal_tax, federal_rate = await self._calculate_capital_gains_tax(
            gains_dec, federal_taxable, year, filing_status
        )
        
        # State tax (most states tax as ordinary income)
        state_taxable_base = max(Decimal('0'), base_income_dec - state_std_deduction)
        state_taxable_total = max(Decimal('0'), total_income - state_std_deduction)
        
        base_state_tax, _ = await self._calculate_state_income_tax(
            state_taxable_base, year, state, filing_status
        )
        total_state_tax, state_marginal = await self._calculate_state_income_tax(
            state_taxable_total, year, state, filing_status
        )
        state_tax = total_state_tax - base_state_tax
        
        # NIIT if applicable
        niit_tax = await self._calculate_niit(gains_dec, total_income, year, filing_status)
        
        # Local tax on gains
        local_tax = gains_dec * Decimal(str(local_tax_rate))
        
        total_tax_on_gains = federal_tax + state_tax + niit_tax + local_tax
        after_tax_gains = gains_dec - total_tax_on_gains
        effective_rate = (total_tax_on_gains / gains_dec) if gains_dec > 0 else Decimal('0')
        
        return {
            "holding_period_days": holding_days,
            "gains_type": "long_term",
            "gains_amount": float(gains_dec),
            "base_income": float(base_income_dec),
            "federal_tax": float(federal_tax),
            "federal_ltcg_rate": float(federal_rate),
            "state_tax": float(state_tax),
            "state_marginal_rate": float(state_marginal),
            "niit_tax": float(niit_tax),
            "local_tax": float(local_tax),
            "total_tax": float(total_tax_on_gains),
            "effective_rate": float(effective_rate),
            "after_tax_gains": float(after_tax_gains)
        }
    
    async def get_tax_breakdown(
        self,
        scenario_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get detailed tax breakdown for any scenario
        
        Args:
            scenario_type: 'income', 'short_term_gains', 'long_term_gains'
            **kwargs: Parameters for the specific scenario
        
        Returns:
            Detailed tax breakdown with all components
        """
        if scenario_type == 'income':
            return await self.calculate_income_tax(**kwargs)
        elif scenario_type == 'short_term_gains':
            return await self.calculate_short_term_capital_gains_tax(**kwargs)
        elif scenario_type == 'long_term_gains':
            return await self.calculate_long_term_capital_gains_tax(**kwargs)
        else:
            return {"error": f"Unknown scenario type: {scenario_type}"}
