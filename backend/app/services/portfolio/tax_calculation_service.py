"""
Tax Calculation Service for Portfolio Manager Application

Handles all tax calculations including:
- Short-term vs Long-term capital gains determination
- Federal tax calculations using investor profile tax brackets
- NIIT (Net Investment Income Tax) calculations
- Holding period analysis
- Break-even analysis for tax optimization decisions
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum

from app.models.portfolio_models import Transaction, InvestorProfile
from .investor_profile_service import InvestorProfileService
from .transaction_service import TransactionService


class CapitalGainsType(Enum):
    SHORT_TERM = "short_term"  # <= 1 year
    LONG_TERM = "long_term"   # > 1 year


class TaxCalculationService:
    """Service class for comprehensive tax calculations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.investor_service = InvestorProfileService(db)
        self.transaction_service = TransactionService(db)
    
    def calculate_holding_period(self, purchase_date: date, sale_date: date) -> Tuple[int, CapitalGainsType]:
        """
        Calculate holding period and determine capital gains type
        
        Args:
            purchase_date: Date stock was purchased
            sale_date: Date stock was/will be sold
            
        Returns:
            Tuple of (days_held, capital_gains_type)
        """
        holding_period = (sale_date - purchase_date).days
        
        # Long-term capital gains require holding > 365 days (more than 1 year)
        if holding_period > 365:
            gains_type = CapitalGainsType.LONG_TERM
        else:
            gains_type = CapitalGainsType.SHORT_TERM
            
        return holding_period, gains_type
    
    def calculate_capital_gains(
        self, 
        purchase_price: Decimal, 
        sale_price: Decimal, 
        quantity: Decimal
    ) -> Decimal:
        """
        Calculate capital gains/loss amount
        
        Args:
            purchase_price: Price per share when purchased
            sale_price: Price per share when sold
            quantity: Number of shares
            
        Returns:
            Capital gains/loss amount (positive = gain, negative = loss)
        """
        cost_basis = purchase_price * quantity
        sale_proceeds = sale_price * quantity
        return sale_proceeds - cost_basis
    
    def calculate_federal_tax(
        self, 
        investor_profile_id: int, 
        gains_type: CapitalGainsType,
        capital_gains_amount: Decimal
    ) -> Dict[str, Any]:
        """
        Calculate federal tax using progressive tax calculation
        
        Args:
            investor_profile_id: Investor profile ID
            gains_type: Short-term or long-term capital gains
            capital_gains_amount: Amount of capital gains
            
        Returns:
            Dictionary with progressive tax calculation details
        """
        profile = self.investor_service.get_profile(investor_profile_id)
        if not profile:
            raise ValueError(f"Investor profile {investor_profile_id} not found")
        
        capital_gains_float = float(capital_gains_amount)
        
        if gains_type == CapitalGainsType.LONG_TERM:
            # Use progressive long-term capital gains calculation
            return self.investor_service.calculate_progressive_tax(
                investor_profile_id,
                capital_gains_float,
                is_capital_gains=True,
                is_long_term=True
            )
        else:
            # Short-term gains: progressive ordinary income calculation
            return self.investor_service.calculate_progressive_tax(
                investor_profile_id,
                capital_gains_float,
                is_capital_gains=True,
                is_long_term=False
            )

    def get_federal_tax_rate(
        self, 
        investor_profile_id: int, 
        gains_type: CapitalGainsType,
        capital_gains_amount: Decimal
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Use calculate_federal_tax() for accurate progressive calculation
        
        Get applicable federal tax rates for capital gains (simplified method)
        
        Args:
            investor_profile_id: Investor profile ID
            gains_type: Short-term or long-term capital gains
            capital_gains_amount: Amount of capital gains
            
        Returns:
            Dictionary with tax rate information
        """
        # Get investor tax brackets
        tax_brackets = self.investor_service.calculate_tax_brackets(investor_profile_id)
        if not tax_brackets:
            raise ValueError(f"Investor profile {investor_profile_id} not found")
        
        profile = self.investor_service.get_profile(investor_profile_id)
        
        if gains_type == CapitalGainsType.SHORT_TERM:
            # Short-term capital gains taxed as ordinary income
            return {
                'gains_type': 'short_term',
                'federal_rate': tax_brackets['marginal_tax_rate'],
                'federal_rate_percent': tax_brackets['marginal_tax_rate_percent'],
                'niit_applies': tax_brackets['niit_applies'],
                'niit_rate': tax_brackets['niit_rate'],
                'total_federal_rate': tax_brackets['marginal_tax_rate'] + (tax_brackets['niit_rate'] if tax_brackets['niit_applies'] else 0),
                'explanation': 'Short-term capital gains taxed as ordinary income at marginal rate'
            }
        else:
            # Long-term capital gains have preferential rates
            filing_status = profile.filing_status
            household_income = float(profile.annual_household_income)
            
            # 2025 Long-term capital gains tax brackets
            if filing_status == 'single':
                if household_income <= 47025:
                    ltcg_rate = 0.0
                elif household_income <= 518900:
                    ltcg_rate = 0.15
                else:
                    ltcg_rate = 0.20
            elif filing_status == 'married_joint':
                if household_income <= 94050:
                    ltcg_rate = 0.0
                elif household_income <= 583750:
                    ltcg_rate = 0.15
                else:
                    ltcg_rate = 0.20
            else:
                # Default to single brackets for other filing statuses
                if household_income <= 47025:
                    ltcg_rate = 0.0
                elif household_income <= 518900:
                    ltcg_rate = 0.15
                else:
                    ltcg_rate = 0.20
            
            return {
                'gains_type': 'long_term',
                'federal_rate': ltcg_rate,
                'federal_rate_percent': ltcg_rate * 100,
                'niit_applies': tax_brackets['niit_applies'],
                'niit_rate': tax_brackets['niit_rate'],
                'total_federal_rate': ltcg_rate + (tax_brackets['niit_rate'] if tax_brackets['niit_applies'] else 0),
                'explanation': f'Long-term capital gains preferential rate: {ltcg_rate * 100}%'
            }
    
    def calculate_federal_tax_owed(
        self,
        investor_profile_id: int,
        capital_gains_amount: Decimal,
        gains_type: CapitalGainsType
    ) -> Dict[str, Any]:
        """
        Calculate federal tax owed on capital gains
        
        Args:
            investor_profile_id: Investor profile ID
            capital_gains_amount: Amount of capital gains
            gains_type: Short-term or long-term
            
        Returns:
            Detailed tax calculation breakdown
        """
        if capital_gains_amount <= 0:
            return {
                'capital_gains_amount': float(capital_gains_amount),
                'gains_type': gains_type.value,
                'federal_tax_owed': 0.0,
                'niit_tax_owed': 0.0,
                'total_tax_owed': 0.0,
                'explanation': 'No tax owed on capital losses'
            }
        
        tax_rates = self.get_federal_tax_rate(investor_profile_id, gains_type, capital_gains_amount)
        
        # Calculate federal tax
        federal_tax = capital_gains_amount * Decimal(str(tax_rates['federal_rate']))
        
        # Calculate NIIT if applicable
        niit_tax = Decimal('0.0')
        if tax_rates['niit_applies']:
            niit_tax = capital_gains_amount * Decimal(str(tax_rates['niit_rate']))
        
        total_tax = federal_tax + niit_tax
        
        return {
            'capital_gains_amount': float(capital_gains_amount),
            'gains_type': gains_type.value,
            'federal_rate_percent': tax_rates['federal_rate_percent'],
            'federal_tax_owed': float(federal_tax),
            'niit_applies': tax_rates['niit_applies'],
            'niit_rate_percent': tax_rates['niit_rate'] * 100 if tax_rates['niit_applies'] else 0.0,
            'niit_tax_owed': float(niit_tax),
            'total_federal_rate_percent': tax_rates['total_federal_rate'] * 100,
            'total_tax_owed': float(total_tax),
            'explanation': tax_rates['explanation']
        }
    
    def analyze_stock_sale_tax_impact(
        self,
        portfolio_id: int,
        ticker: str,
        quantity_to_sell: Decimal,
        sale_price: Decimal,
        sale_date: date = None
    ) -> Dict[str, Any]:
        """
        Analyze tax impact of selling specific stocks using FIFO method
        
        Args:
            portfolio_id: Portfolio ID
            ticker: Stock ticker symbol
            quantity_to_sell: Number of shares to sell
            sale_price: Price per share for sale
            sale_date: Date of sale (defaults to today)
            
        Returns:
            Comprehensive tax impact analysis
        """
        if sale_date is None:
            sale_date = date.today()
        
        # Get all buy transactions for this stock, ordered by date (FIFO)
        buy_transactions = self.transaction_service.get_transactions_by_portfolio(
            portfolio_id=portfolio_id,
            ticker=ticker,
            transaction_type='buy',
            order_by='date_asc'
        )
        
        if not buy_transactions:
            raise ValueError(f"No buy transactions found for {ticker} in portfolio {portfolio_id}")
        
        # Get investor profile for tax calculations
        portfolio = self.transaction_service.portfolio_service.get_portfolio(portfolio_id)
        if not portfolio or not portfolio.investor_profile_id:
            raise ValueError(f"No investor profile associated with portfolio {portfolio_id}")
        
        remaining_to_sell = quantity_to_sell
        total_cost_basis = Decimal('0.0')
        total_proceeds = quantity_to_sell * sale_price
        tax_lots = []
        
        for transaction in buy_transactions:
            if remaining_to_sell <= 0:
                break
            
            available_shares = transaction.quantity
            shares_to_use = min(remaining_to_sell, available_shares)
            
            # Calculate holding period
            holding_days, gains_type = self.calculate_holding_period(
                transaction.transaction_date, 
                sale_date
            )
            
            # Calculate gains for this lot
            lot_cost_basis = shares_to_use * transaction.price_per_share
            lot_proceeds = shares_to_use * sale_price
            lot_gains = lot_proceeds - lot_cost_basis
            
            # Calculate tax for this lot
            tax_calculation = self.calculate_federal_tax_owed(
                portfolio.investor_profile_id,
                lot_gains,
                gains_type
            )
            
            tax_lots.append({
                'transaction_id': transaction.id,
                'transaction_date': transaction.transaction_date.isoformat(),
                'shares_used': float(shares_to_use),
                'purchase_price': float(transaction.price_per_share),
                'holding_days': holding_days,
                'gains_type': gains_type.value,
                'cost_basis': float(lot_cost_basis),
                'proceeds': float(lot_proceeds),
                'capital_gains': float(lot_gains),
                'tax_owed': tax_calculation['total_tax_owed']
            })
            
            total_cost_basis += lot_cost_basis
            remaining_to_sell -= shares_to_use
        
        if remaining_to_sell > 0:
            raise ValueError(f"Insufficient shares available. Requested: {quantity_to_sell}, Available: {quantity_to_sell - remaining_to_sell}")
        
        # Calculate totals
        total_capital_gains = total_proceeds - total_cost_basis
        total_tax_owed = sum(lot['tax_owed'] for lot in tax_lots)
        
        # Calculate after-tax proceeds
        after_tax_proceeds = total_proceeds - Decimal(str(total_tax_owed))
        
        return {
            'analysis_date': sale_date.isoformat(),
            'portfolio_id': portfolio_id,
            'ticker': ticker,
            'quantity_sold': float(quantity_to_sell),
            'sale_price': float(sale_price),
            'total_proceeds': float(total_proceeds),
            'total_cost_basis': float(total_cost_basis),
            'total_capital_gains': float(total_capital_gains),
            'total_tax_owed': total_tax_owed,
            'after_tax_proceeds': float(after_tax_proceeds),
            'effective_tax_rate_percent': (total_tax_owed / float(total_capital_gains) * 100) if total_capital_gains > 0 else 0.0,
            'tax_lots': tax_lots,
            'summary': {
                'short_term_lots': len([lot for lot in tax_lots if lot['gains_type'] == 'short_term']),
                'long_term_lots': len([lot for lot in tax_lots if lot['gains_type'] == 'long_term']),
                'total_lots_used': len(tax_lots)
            }
        }
    
    def calculate_break_even_price(
        self,
        portfolio_id: int,
        ticker: str,
        quantity_to_sell: Decimal,
        target_after_tax_amount: Decimal,
        sale_date: date = None
    ) -> Dict[str, Any]:
        """
        Calculate the minimum sale price needed to achieve target after-tax proceeds
        
        Args:
            portfolio_id: Portfolio ID
            ticker: Stock ticker symbol
            quantity_to_sell: Number of shares to sell
            target_after_tax_amount: Desired after-tax proceeds
            sale_date: Date of sale (defaults to today)
            
        Returns:
            Break-even analysis with required sale price
        """
        if sale_date is None:
            sale_date = date.today()
        
        # Binary search for break-even price
        low_price = Decimal('0.01')
        high_price = Decimal('10000.00')  # Start with reasonable upper bound
        tolerance = Decimal('0.01')
        max_iterations = 100
        
        for iteration in range(max_iterations):
            test_price = (low_price + high_price) / 2
            
            try:
                analysis = self.analyze_stock_sale_tax_impact(
                    portfolio_id, ticker, quantity_to_sell, test_price, sale_date
                )
                
                after_tax_proceeds = Decimal(str(analysis['after_tax_proceeds']))
                
                if abs(after_tax_proceeds - target_after_tax_amount) <= tolerance:
                    # Found break-even price
                    return {
                        'break_even_price': float(test_price),
                        'target_after_tax_amount': float(target_after_tax_amount),
                        'actual_after_tax_amount': float(after_tax_proceeds),
                        'total_proceeds': analysis['total_proceeds'],
                        'total_tax_owed': analysis['total_tax_owed'],
                        'effective_tax_rate_percent': analysis['effective_tax_rate_percent'],
                        'iterations_required': iteration + 1,
                        'analysis': analysis
                    }
                elif after_tax_proceeds < target_after_tax_amount:
                    low_price = test_price
                else:
                    high_price = test_price
                    
            except ValueError as e:
                # If price is too low, increase low_price
                low_price = test_price
                continue
        
        # If we couldn't find exact break-even, return best estimate
        return {
            'break_even_price': float(high_price),
            'target_after_tax_amount': float(target_after_tax_amount),
            'estimated': True,
            'message': 'Could not find exact break-even price, returning estimate'
        }


def get_tax_calculation_service(db: Session) -> TaxCalculationService:
    """Dependency injection helper for Flask"""
    return TaxCalculationService(db)