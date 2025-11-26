"""
Break-Even Analysis Service for Portfolio Manager Application

This service answers the core question: "Should I sell this stock and pay taxes, 
or hold it through potential market downturns?"

Calculates break-even thresholds where selling becomes more beneficial than holding.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from app.models.portfolio_models import Transaction, InvestorProfile, MarketPrice
from .investor_profile_service import InvestorProfileService
from .transaction_service import TransactionService
from .market_price_service import MarketPriceService
from .tax_calculation_service import TaxCalculationService, CapitalGainsType
from .state_tax_service import StateTaxService
from .comprehensive_tax_service import ComprehensiveTaxService


class BreakEvenService:
    """Service class for break-even analysis calculations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.investor_service = InvestorProfileService(db)
        self.transaction_service = TransactionService(db)
        self.market_price_service = MarketPriceService(db)
        self.tax_service = TaxCalculationService(db)
        self.state_tax_service = StateTaxService(db)
        self.comprehensive_tax_service = ComprehensiveTaxService(db)
    
    def calculate_break_even_single_transaction(
        self,
        transaction_id: int,
        investor_profile_id: int,
        current_price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate break-even analysis for a single transaction
        
        Args:
            transaction_id: Transaction ID to analyze
            investor_profile_id: Investor profile for tax calculations
            current_price: Optional current market price (will fetch if not provided)
            
        Returns:
            Dictionary with break-even analysis details
        """
        # Get transaction details
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        if transaction.transaction_type != 'buy':
            raise ValueError("Break-even analysis only applies to buy transactions")
        
        # Get current market price
        if current_price is None:
            market_price = self.market_price_service.get_price(transaction.ticker_symbol)
            if not market_price:
                raise ValueError(f"No market price found for {transaction.ticker_symbol}")
            current_price = market_price.current_price
        
        # Calculate current position value
        current_value = transaction.quantity * current_price
        cost_basis = transaction.quantity * transaction.price_per_share
        current_gain_loss = current_value - cost_basis
        
        # Determine holding period and gains type (needed for consistent UI regardless of gain/loss)
        holding_days = (date.today() - transaction.transaction_date).days
        gains_type = CapitalGainsType.LONG_TERM if holding_days > 365 else CapitalGainsType.SHORT_TERM
        
        # If at a loss, enrich payload with tax-loss harvesting estimate so UI doesn't have to fetch extra
        if current_gain_loss <= 0:
            # Compute estimated tax-loss harvesting savings using marginal ordinary + state + local rates
            try:
                profile = self.investor_service.get_profile(investor_profile_id)
                # Use true marginal ordinary bracket rate at current income
                tax_brackets = self.investor_service.calculate_tax_brackets(investor_profile_id)
                marginal_ordinary_rate = float(tax_brackets.get('marginal_tax_rate') or 0.0)
                state_info = self.state_tax_service.get_state_info(profile.state_of_residence) if profile else {'capital_gains_rate': 0.0}
                state_rate = float(state_info.get('capital_gains_rate') or 0.0)
                local_rate = float(profile.local_tax_rate) if profile else 0.0
                loss_dollars = float(abs(current_gain_loss))
                ordinary_offset = float(min(loss_dollars, 3000.0))
                estimated_savings = ordinary_offset * (marginal_ordinary_rate + state_rate + local_rate)
                tax_loss_harvest_estimate = {
                    'loss_dollars': loss_dollars,
                    'ordinary_offset_applied': ordinary_offset,
                    'marginal_ordinary_rate': marginal_ordinary_rate,
                    'state_rate': state_rate,
                    'local_rate': local_rate,
                    'estimated_savings': estimated_savings,
                    'notes': 'Assumes up to $3,000 ordinary-income offset; excludes wash-sale and carryovers.'
                }
            except Exception:
                tax_loss_harvest_estimate = None

            return {
                'transaction_id': transaction_id,
                'ticker_symbol': transaction.ticker_symbol,
                'transaction_date': transaction.transaction_date.isoformat(),
                'quantity': float(transaction.quantity),
                'purchase_price': float(transaction.price_per_share),
                'current_price': float(current_price),
                'position_status': 'loss',
                'holding_period': {
                    'days': holding_days,
                    'type': gains_type.value,
                    'is_long_term': gains_type == CapitalGainsType.LONG_TERM
                },
                'financial_analysis': {
                    'cost_basis': float(cost_basis),
                    'current_value': float(current_value),
                    'current_gain_loss': float(current_gain_loss),
                    'gain_loss_percentage': float((current_gain_loss / cost_basis) * 100) if cost_basis != 0 else 0.0
                },
                'tax_analysis': None,
                'break_even_analysis': None,
                'tax_loss_harvest_estimate': tax_loss_harvest_estimate,
                'recommendation': 'hold',
                'reason': 'Position is at a loss - consider tax-loss harvesting if appropriate'
            }
        
        # Determine holding period and gains type
        # (already computed above, retained here for readability)
        
        # Calculate tax owed if sold today using progressive tax calculation
        tax_calculation = self.investor_service.calculate_progressive_tax(
            investor_profile_id,
            float(current_gain_loss),
            is_capital_gains=True,
            is_long_term=(gains_type == CapitalGainsType.LONG_TERM)
        )
        
        # Get state and local taxes
        investor_profile = self.investor_service.get_profile(investor_profile_id)
        if not investor_profile:
            raise ValueError(f"Investor profile {investor_profile_id} not found")
        
        # Calculate state tax
        gains_type_str = 'long_term' if gains_type == CapitalGainsType.LONG_TERM else 'short_term'
        state_tax = self.state_tax_service.calculate_state_capital_gains_tax(
            investor_profile_id,
            Decimal(str(current_gain_loss)),
            gains_type_str
        )
        
        # Calculate local tax
        local_tax = float(current_gain_loss) * float(investor_profile.local_tax_rate)
        
        # Total tax burden
        total_federal_tax = tax_calculation['total_federal_tax']
        total_tax_owed = total_federal_tax + state_tax['state_tax_owed'] + local_tax
        
        # Calculate after-tax proceeds if sold today
        after_tax_proceeds = float(current_value) - total_tax_owed
        
        # Break-even calculation
        # The stock needs to drop to the point where current value equals after-tax proceeds
        break_even_total_value = after_tax_proceeds
        break_even_price_per_share = break_even_total_value / float(transaction.quantity)
        
        # Calculate required loss (dollar and percentage)
        loss_required_dollars = float(current_value) - break_even_total_value
        loss_required_percentage = (loss_required_dollars / float(current_value)) * 100
        
        # Price drop calculations
        price_drop_required = float(current_price) - break_even_price_per_share
        price_drop_percentage = (price_drop_required / float(current_price)) * 100
        
        # Recommendation logic
        if loss_required_percentage < 5.0:
            recommendation = 'consider_selling'
            reason = f'Stock only needs to drop {loss_required_percentage:.1f}% to break even'
        elif loss_required_percentage < 15.0:
            recommendation = 'monitor_closely'
            reason = f'Moderate risk - {loss_required_percentage:.1f}% drop needed to break even'
        else:
            recommendation = 'hold'
            reason = f'Low risk - {loss_required_percentage:.1f}% drop needed to break even'
        
        return {
            'transaction_id': transaction_id,
            'ticker_symbol': transaction.ticker_symbol,
            'transaction_date': transaction.transaction_date.isoformat(),
            'quantity': float(transaction.quantity),
            'purchase_price': float(transaction.price_per_share),
            'current_price': float(current_price),
            'position_status': 'gain',
            'holding_period': {
                'days': holding_days,
                'type': gains_type.value,
                'is_long_term': gains_type == CapitalGainsType.LONG_TERM
            },
            'financial_analysis': {
                'cost_basis': float(cost_basis),
                'current_value': float(current_value),
                'current_gain_loss': float(current_gain_loss),
                'gain_loss_percentage': float((current_gain_loss / cost_basis) * 100)
            },
            'tax_analysis': {
                'federal_tax': total_federal_tax,
                'state_tax': state_tax['state_tax_owed'],
                'local_tax': local_tax,
                'total_tax_owed': total_tax_owed,
                'effective_tax_rate': (total_tax_owed / float(current_gain_loss)) * 100,
                'after_tax_proceeds': after_tax_proceeds
            },
            'break_even_analysis': {
                'break_even_total_value': break_even_total_value,
                'break_even_price_per_share': break_even_price_per_share,
                'loss_required_dollars': loss_required_dollars,
                'loss_required_percentage': loss_required_percentage,
                'price_drop_required': price_drop_required,
                'price_drop_percentage': price_drop_percentage
            },
            'recommendation': recommendation,
            'reason': reason,
            'calculation_timestamp': datetime.now().isoformat()
        }
    
    def calculate_break_even_portfolio(
        self,
        portfolio_id: int,
        investor_profile_id: int
    ) -> Dict[str, Any]:
        """
        Calculate break-even analysis for all positions in a portfolio
        
        Args:
            portfolio_id: Portfolio ID to analyze
            investor_profile_id: Investor profile for tax calculations
            
        Returns:
            Dictionary with portfolio-wide break-even analysis
        """
        # Get portfolio holdings
        holdings = self.transaction_service.get_portfolio_holdings(portfolio_id)
        
        if not holdings:
            return {
                'portfolio_id': portfolio_id,
                'total_positions': 0,
                'positions_analyzed': 0,
                'analysis': {},
                'portfolio_summary': {
                    'total_current_value': 0,
                    'total_tax_if_sold': 0,
                    'total_after_tax_proceeds': 0,
                    'average_break_even_percentage': 0
                }
            }
        
        portfolio_analysis: Dict[str, Any] = {}
        total_tax_owed = 0
        total_after_tax_proceeds = 0
        total_current_value = 0  # Track total portfolio value
        valid_analyses = []
        all_transaction_analyses: list[Dict[str, Any]] = []
        
        # Analyze each holding
        for ticker, holding_info in holdings.items():
            try:
                # Analyze ALL buy transactions (lots) for this ticker
                transactions = holding_info.get('transactions', [])
                buy_transactions = [t for t in transactions if t.transaction_type == 'buy']

                if not buy_transactions:
                    continue

                ticker_analyses: list[Dict[str, Any]] = []
                for tx in buy_transactions:
                    try:
                        analysis = self.calculate_break_even_single_transaction(
                            tx.id,
                            investor_profile_id
                        )
                        ticker_analyses.append(analysis)
                        all_transaction_analyses.append(analysis)
                        
                        # Add current value from financial analysis
                        if 'financial_analysis' in analysis and 'current_value' in analysis['financial_analysis']:
                            total_current_value += analysis['financial_analysis']['current_value']
                        
                        if analysis['position_status'] == 'gain':
                            total_tax_owed += analysis['tax_analysis']['total_tax_owed']
                            total_after_tax_proceeds += analysis['tax_analysis']['after_tax_proceeds']
                            valid_analyses.append(analysis)
                    except Exception as inner_e:
                        ticker_analyses.append({
                            'transaction_id': tx.id,
                            'ticker_symbol': ticker,
                            'error': str(inner_e),
                        })

                portfolio_analysis[ticker] = ticker_analyses

            except Exception as e:
                # Log error but continue with other positions
                portfolio_analysis[ticker] = {
                    'error': str(e),
                    'ticker_symbol': ticker
                }
        
        # Calculate portfolio-level metrics
        average_break_even_percentage = 0
        if valid_analyses:
            total_break_even_percentage = sum(
                a['break_even_analysis']['loss_required_percentage'] 
                for a in valid_analyses
            )
            average_break_even_percentage = total_break_even_percentage / len(valid_analyses)
        
        return {
            'portfolio_id': portfolio_id,
            'total_positions': len(holdings),
            'positions_analyzed': sum(len(v) if isinstance(v, list) else 1 for v in portfolio_analysis.values()),
            'positions_with_gains': len(valid_analyses),
            'analysis': portfolio_analysis,
            'transactions': all_transaction_analyses,
            'portfolio_summary': {
                'total_current_value': total_current_value,
                'total_tax_if_all_sold': total_tax_owed,
                'total_after_tax_proceeds': total_after_tax_proceeds,
                'average_break_even_percentage': average_break_even_percentage
            },
            'calculation_timestamp': datetime.now().isoformat()
        }
    
    def calculate_break_even_by_ticker(
        self,
        ticker: str,
        investor_profile_id: int,
        portfolio_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate break-even analysis for all positions of a specific ticker
        
        Args:
            ticker: Stock ticker symbol
            investor_profile_id: Investor profile for tax calculations
            portfolio_id: Optional portfolio filter
            
        Returns:
            Dictionary with ticker-specific break-even analysis
        """
        # Get all transactions for this ticker
        transactions = self.transaction_service.get_transactions_by_ticker(
            ticker, portfolio_id
        )
        
        buy_transactions = [t for t in transactions if t.transaction_type == 'buy']
        
        if not buy_transactions:
            return {
                'ticker_symbol': ticker,
                'total_transactions': 0,
                'analysis': [],
                'error': 'No buy transactions found for this ticker'
            }
        
        ticker_analysis = []
        
        for transaction in buy_transactions:
            try:
                analysis = self.calculate_break_even_single_transaction(
                    transaction.id,
                    investor_profile_id
                )
                ticker_analysis.append(analysis)
            except Exception as e:
                ticker_analysis.append({
                    'transaction_id': transaction.id,
                    'error': str(e)
                })
        
        # Calculate aggregated metrics
        valid_analyses = [a for a in ticker_analysis if 'error' not in a and a['position_status'] == 'gain']
        
        summary = {
            'total_positions': len(buy_transactions),
            'positions_with_gains': len(valid_analyses),
            'total_tax_if_sold': sum(a['tax_analysis']['total_tax_owed'] for a in valid_analyses),
            'average_break_even_percentage': 0
        }
        
        if valid_analyses:
            summary['average_break_even_percentage'] = sum(
                a['break_even_analysis']['loss_required_percentage'] for a in valid_analyses
            ) / len(valid_analyses)
        
        return {
            'ticker_symbol': ticker,
            'portfolio_id': portfolio_id,
            'total_transactions': len(buy_transactions),
            'analysis': ticker_analysis,
            'summary': summary,
            'calculation_timestamp': datetime.now().isoformat()
        }


def get_break_even_service(db: Session) -> BreakEvenService:
    """Dependency injection helper for Flask"""
    return BreakEvenService(db)