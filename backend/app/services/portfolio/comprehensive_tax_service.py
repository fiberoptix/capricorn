"""
Comprehensive Tax Service for Portfolio Manager Application

This is the master tax service that integrates federal, state, and local tax calculations
to provide comprehensive tax optimization strategies and recommendations.

Features:
- Complete tax impact analysis for any investment decision
- Multi-scenario tax optimization comparisons
- Tax-loss harvesting recommendations
- Year-end tax planning strategies
- Portfolio-wide tax optimization
- State relocation tax impact analysis
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum

from .tax_calculation_service import TaxCalculationService, CapitalGainsType
from .state_tax_service import StateTaxService
from .investor_profile_service import InvestorProfileService
from .transaction_service import TransactionService
from .market_price_service import MarketPriceService


class TaxOptimizationStrategy(Enum):
    MINIMIZE_CURRENT_YEAR = "minimize_current_year"
    MAXIMIZE_LONG_TERM = "maximize_long_term" 
    HARVEST_LOSSES = "harvest_losses"
    DEFER_GAINS = "defer_gains"
    RELOCATE_FRIENDLY_STATE = "relocate_friendly_state"


class ComprehensiveTaxService:
    """Master service for comprehensive tax calculations and optimization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.federal_tax_service = TaxCalculationService(db)
        self.state_tax_service = StateTaxService(db)
        self.investor_service = InvestorProfileService(db)
        self.transaction_service = TransactionService(db)
        self.market_price_service = MarketPriceService(db)
    
    def analyze_complete_tax_impact(
        self,
        portfolio_id: int,
        ticker: str,
        quantity_to_sell: Decimal,
        sale_price: Decimal,
        sale_date: date = None
    ) -> Dict[str, Any]:
        """
        Complete federal + state + local tax impact analysis for a stock sale
        
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
        
        # Get federal tax analysis (FIFO method)
        federal_analysis = self.federal_tax_service.analyze_stock_sale_tax_impact(
            portfolio_id=portfolio_id,
            ticker=ticker,
            quantity_to_sell=quantity_to_sell,
            sale_price=sale_price,
            sale_date=sale_date
        )
        
        # Get portfolio to find investor profile
        portfolio = self.transaction_service.portfolio_service.get_portfolio(portfolio_id)
        if not portfolio or not portfolio.investor_profile_id:
            raise ValueError(f"No investor profile associated with portfolio {portfolio_id}")
        
        # Calculate state and local taxes for each tax lot
        total_state_tax = Decimal('0.0')
        total_local_tax = Decimal('0.0')
        
        for lot in federal_analysis['tax_lots']:
            lot_gains = Decimal(str(lot['capital_gains']))
            gains_type = lot['gains_type']
            
            # Calculate state tax for this lot
            state_tax = self.state_tax_service.calculate_state_capital_gains_tax(
                investor_profile_id=portfolio.investor_profile_id,
                capital_gains_amount=lot_gains,
                gains_type=gains_type
            )
            
            total_state_tax += Decimal(str(state_tax['state_tax_owed']))
            total_local_tax += Decimal(str(state_tax['local_tax_owed']))
            
            # Add state/local tax info to the lot
            lot['state_tax_owed'] = state_tax['state_tax_owed']
            lot['local_tax_owed'] = state_tax['local_tax_owed']
            lot['total_lot_tax'] = lot['tax_owed'] + state_tax['state_tax_owed'] + state_tax['local_tax_owed']
        
        # Calculate comprehensive totals
        federal_tax = Decimal(str(federal_analysis['total_tax_owed']))
        total_comprehensive_tax = federal_tax + total_state_tax + total_local_tax
        
        total_proceeds = Decimal(str(federal_analysis['total_proceeds']))
        comprehensive_after_tax = total_proceeds - total_comprehensive_tax
        
        comprehensive_effective_rate = (total_comprehensive_tax / Decimal(str(federal_analysis['total_capital_gains'])) * 100) if federal_analysis['total_capital_gains'] > 0 else Decimal('0.0')
        
        # Get state information
        profile = self.investor_service.get_profile(portfolio.investor_profile_id)
        state_info = self.state_tax_service.get_state_info(profile.state_of_residence)
        
        return {
            **federal_analysis,  # Include all federal analysis data
            'comprehensive_tax_analysis': {
                'federal_tax_owed': float(federal_tax),
                'state_tax_owed': float(total_state_tax),
                'local_tax_owed': float(total_local_tax),
                'total_comprehensive_tax': float(total_comprehensive_tax),
                'comprehensive_after_tax_proceeds': float(comprehensive_after_tax),
                'comprehensive_effective_rate_percent': float(comprehensive_effective_rate),
                'state_info': {
                    'state_code': profile.state_of_residence,
                    'state_name': state_info['name'],
                    'state_rate_percent': state_info['capital_gains_rate'] * 100,
                    'local_rate_percent': float(profile.local_tax_rate * 100)
                }
            }
        }
    
    def compare_sale_timing_scenarios(
        self,
        portfolio_id: int,
        ticker: str,
        quantity_to_sell: Decimal,
        sale_price: Decimal,
        scenarios: List[date] = None
    ) -> Dict[str, Any]:
        """
        Compare tax impact of selling at different dates
        
        Args:
            portfolio_id: Portfolio ID
            ticker: Stock ticker symbol  
            quantity_to_sell: Number of shares to sell
            sale_price: Price per share for sale
            scenarios: List of potential sale dates (defaults to today, 30 days, 365 days)
            
        Returns:
            Comparison of tax impacts across different timing scenarios
        """
        if scenarios is None:
            today = date.today()
            scenarios = [
                today,
                today + timedelta(days=30),
                today + timedelta(days=365)
            ]
        
        scenario_analyses = []
        
        for scenario_date in scenarios:
            try:
                analysis = self.analyze_complete_tax_impact(
                    portfolio_id=portfolio_id,
                    ticker=ticker,
                    quantity_to_sell=quantity_to_sell,
                    sale_price=sale_price,
                    sale_date=scenario_date
                )
                
                scenario_analyses.append({
                    'sale_date': scenario_date.isoformat(),
                    'days_from_today': (scenario_date - date.today()).days,
                    'total_tax_owed': analysis['comprehensive_tax_analysis']['total_comprehensive_tax'],
                    'after_tax_proceeds': analysis['comprehensive_tax_analysis']['comprehensive_after_tax_proceeds'],
                    'effective_rate_percent': analysis['comprehensive_tax_analysis']['comprehensive_effective_rate_percent'],
                    'capital_gains_types': {
                        'short_term_lots': analysis['summary']['short_term_lots'],
                        'long_term_lots': analysis['summary']['long_term_lots']
                    }
                })
            except Exception as e:
                scenario_analyses.append({
                    'sale_date': scenario_date.isoformat(),
                    'days_from_today': (scenario_date - date.today()).days,
                    'error': str(e)
                })
        
        # Find optimal scenario
        valid_scenarios = [s for s in scenario_analyses if 'error' not in s]
        if valid_scenarios:
            optimal_scenario = min(valid_scenarios, key=lambda x: x['total_tax_owed'])
            optimal_index = next(i for i, s in enumerate(scenario_analyses) if s == optimal_scenario)
        else:
            optimal_scenario = None
            optimal_index = None
        
        return {
            'portfolio_id': portfolio_id,
            'ticker': ticker,
            'quantity_to_sell': float(quantity_to_sell),
            'sale_price': float(sale_price),
            'scenarios': scenario_analyses,
            'optimal_scenario': {
                'index': optimal_index,
                'scenario': optimal_scenario,
                'recommendation': f"Sell on {optimal_scenario['sale_date']} to minimize tax burden" if optimal_scenario else "No valid scenarios found"
            } if optimal_scenario else None
        }
    
    def analyze_tax_loss_harvesting_opportunities(
        self,
        portfolio_id: int,
        target_loss_amount: Decimal = None,
        min_position_value: Decimal = Decimal('1000')
    ) -> Dict[str, Any]:
        """
        Identify tax-loss harvesting opportunities in a portfolio
        
        Args:
            portfolio_id: Portfolio ID
            target_loss_amount: Target loss amount to harvest (optional)
            min_position_value: Minimum position value to consider
            
        Returns:
            Tax-loss harvesting recommendations
        """
        # Get portfolio holdings
        holdings = self.transaction_service.get_portfolio_holdings(portfolio_id)
        
        # Get current market prices
        tickers = list(holdings.keys())
        current_prices = self.market_price_service.get_prices_for_tickers(tickers)
        
        loss_opportunities = []
        total_available_losses = Decimal('0.0')
        
        for ticker, holding in holdings.items():
            current_price_obj = current_prices.get(ticker)
            if not current_price_obj:
                continue
            
            current_market_value = holding['quantity'] * current_price_obj.current_price
            
            # Only consider positions above minimum value
            if current_market_value < min_position_value:
                continue
            
            # Calculate unrealized loss
            cost_basis = holding['cost_basis']
            unrealized_loss = cost_basis - current_market_value
            
            if unrealized_loss > 0:  # Only consider positions at a loss
                # Analyze tax impact of selling entire position
                try:
                    tax_analysis = self.analyze_complete_tax_impact(
                        portfolio_id=portfolio_id,
                        ticker=ticker,
                        quantity_to_sell=holding['quantity'],
                        sale_price=current_price_obj.current_price
                    )
                    
                    # Calculate tax savings from loss
                    profile = self.transaction_service.portfolio_service.get_portfolio(portfolio_id)
                    if profile and profile.investor_profile_id:
                        # Estimate tax savings (simplified - assumes loss offsets gains at marginal rate)
                        tax_brackets = self.investor_service.calculate_tax_brackets(profile.investor_profile_id)
                        estimated_tax_savings = unrealized_loss * Decimal(str(tax_brackets['marginal_tax_rate']))
                        
                        # Add state tax savings
                        state_info = self.state_tax_service.get_state_info(
                            self.investor_service.get_profile(profile.investor_profile_id).state_of_residence
                        )
                        state_tax_savings = unrealized_loss * Decimal(str(state_info['capital_gains_rate']))
                        
                        total_tax_savings = estimated_tax_savings + state_tax_savings
                        
                        loss_opportunities.append({
                            'ticker': ticker,
                            'quantity': float(holding['quantity']),
                            'cost_basis': float(cost_basis),
                            'current_market_value': float(current_market_value),
                            'current_price': float(current_price_obj.current_price),
                            'unrealized_loss': float(unrealized_loss),
                            'estimated_federal_tax_savings': float(estimated_tax_savings),
                            'estimated_state_tax_savings': float(state_tax_savings),
                            'total_estimated_tax_savings': float(total_tax_savings),
                            'loss_percentage': float((unrealized_loss / cost_basis) * 100),
                            'tax_efficiency_ratio': float(total_tax_savings / unrealized_loss) if unrealized_loss > 0 else 0
                        })
                        
                        total_available_losses += unrealized_loss
                
                except Exception as e:
                    # Skip positions that can't be analyzed
                    continue
        
        # Sort by tax efficiency ratio (highest tax savings per dollar of loss)
        loss_opportunities.sort(key=lambda x: x['tax_efficiency_ratio'], reverse=True)
        
        # Create harvesting recommendations
        recommendations = []
        cumulative_losses = Decimal('0.0')
        cumulative_tax_savings = Decimal('0.0')
        
        for opportunity in loss_opportunities:
            if target_loss_amount and cumulative_losses >= target_loss_amount:
                break
            
            recommendations.append(opportunity)
            cumulative_losses += Decimal(str(opportunity['unrealized_loss']))
            cumulative_tax_savings += Decimal(str(opportunity['total_estimated_tax_savings']))
        
        return {
            'portfolio_id': portfolio_id,
            'analysis_date': date.today().isoformat(),
            'total_available_losses': float(total_available_losses),
            'total_opportunities': len(loss_opportunities),
            'recommended_harvesting': {
                'opportunities': recommendations,
                'total_recommended_loss': float(cumulative_losses),
                'total_estimated_tax_savings': float(cumulative_tax_savings),
                'recommendation_count': len(recommendations)
            },
            'all_opportunities': loss_opportunities
        }
    
    def calculate_year_end_tax_strategy(
        self,
        portfolio_id: int,
        target_tax_bracket: str = None,
        target_loss_harvest: Decimal = None
    ) -> Dict[str, Any]:
        """
        Comprehensive year-end tax planning strategy
        
        Args:
            portfolio_id: Portfolio ID
            target_tax_bracket: Target tax bracket to stay within
            target_loss_harvest: Target amount of losses to harvest
            
        Returns:
            Year-end tax optimization strategy
        """
        # Get tax-loss harvesting opportunities
        loss_harvest_analysis = self.analyze_tax_loss_harvesting_opportunities(
            portfolio_id=portfolio_id,
            target_loss_amount=target_loss_harvest
        )
        
        # Get portfolio holdings and identify gain positions
        holdings = self.transaction_service.get_portfolio_holdings(portfolio_id)
        tickers = list(holdings.keys())
        current_prices = self.market_price_service.get_prices_for_tickers(tickers)
        
        gain_opportunities = []
        
        for ticker, holding in holdings.items():
            current_price_obj = current_prices.get(ticker)
            if not current_price_obj:
                continue
            
            current_market_value = holding['quantity'] * current_price_obj.current_price
            cost_basis = holding['cost_basis']
            unrealized_gain = current_market_value - cost_basis
            
            if unrealized_gain > 0:
                # Analyze different timing scenarios for realizing gains
                timing_analysis = self.compare_sale_timing_scenarios(
                    portfolio_id=portfolio_id,
                    ticker=ticker,
                    quantity_to_sell=holding['quantity'],
                    sale_price=current_price_obj.current_price,
                    scenarios=[
                        date.today(),
                        date(date.today().year, 12, 31),  # End of current year
                        date(date.today().year + 1, 1, 15)  # Early next year
                    ]
                )
                
                gain_opportunities.append({
                    'ticker': ticker,
                    'quantity': float(holding['quantity']),
                    'cost_basis': float(cost_basis),
                    'current_market_value': float(current_market_value),
                    'unrealized_gain': float(unrealized_gain),
                    'timing_analysis': timing_analysis
                })
        
        # Create comprehensive strategy
        strategy = {
            'portfolio_id': portfolio_id,
            'analysis_date': date.today().isoformat(),
            'year_end_strategy': {
                'loss_harvesting': loss_harvest_analysis['recommended_harvesting'],
                'gain_realization': {
                    'opportunities': gain_opportunities,
                    'total_opportunities': len(gain_opportunities)
                },
                'overall_recommendation': self._generate_year_end_recommendations(
                    loss_harvest_analysis, gain_opportunities
                )
            }
        }
        
        return strategy
    
    def _generate_year_end_recommendations(
        self,
        loss_analysis: Dict[str, Any],
        gain_opportunities: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate year-end tax strategy recommendations"""
        recommendations = []
        
        total_loss_harvest = loss_analysis['recommended_harvesting']['total_recommended_loss']
        total_tax_savings = loss_analysis['recommended_harvesting']['total_estimated_tax_savings']
        
        if total_loss_harvest > 0:
            recommendations.append(
                f"Harvest ${total_loss_harvest:,.0f} in losses to save approximately ${total_tax_savings:,.0f} in taxes"
            )
        
        if len(gain_opportunities) > 0:
            total_gains = sum(opp['unrealized_gain'] for opp in gain_opportunities)
            recommendations.append(
                f"Consider timing of ${total_gains:,.0f} in unrealized gains across {len(gain_opportunities)} positions"
            )
        
        if total_loss_harvest > 0 and len(gain_opportunities) > 0:
            net_position = sum(opp['unrealized_gain'] for opp in gain_opportunities) - total_loss_harvest
            if net_position > 0:
                recommendations.append(
                    f"After loss harvesting, you would have net gains of ${net_position:,.0f} for the year"
                )
            else:
                recommendations.append(
                    f"Loss harvesting would more than offset current gains, creating ${abs(net_position):,.0f} in net losses"
                )
        
        if not recommendations:
            recommendations.append("No significant tax optimization opportunities identified at this time")
        
        return recommendations
    
    def analyze_multi_state_tax_impact(
        self,
        investor_profile_id: int,
        annual_capital_gains: Decimal,
        target_states: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze tax impact across multiple states for relocation planning
        
        Args:
            investor_profile_id: Investor profile ID
            annual_capital_gains: Expected annual capital gains
            target_states: List of states to analyze (defaults to tax-friendly states)
            
        Returns:
            Multi-state tax impact analysis
        """
        if target_states is None:
            # Default to most tax-friendly states
            tax_friendly = self.state_tax_service.get_tax_friendly_states(limit=10)
            target_states = [state['state_code'] for state in tax_friendly]
        
        analyses = []
        
        for state_code in target_states:
            try:
                relocation_analysis = self.state_tax_service.analyze_relocation_tax_savings(
                    investor_profile_id=investor_profile_id,
                    target_state=state_code,
                    annual_capital_gains=annual_capital_gains
                )
                analyses.append(relocation_analysis)
            except Exception as e:
                analyses.append({
                    'target_state': {'code': state_code, 'error': str(e)}
                })
        
        # Sort by tax savings (highest to lowest)
        valid_analyses = [a for a in analyses if 'tax_savings' in a]
        valid_analyses.sort(key=lambda x: x['tax_savings']['annual_savings'], reverse=True)
        
        return {
            'investor_profile_id': investor_profile_id,
            'annual_capital_gains': float(annual_capital_gains),
            'analysis_date': date.today().isoformat(),
            'state_comparisons': valid_analyses,
            'top_recommendation': valid_analyses[0] if valid_analyses else None,
            'total_states_analyzed': len(valid_analyses)
        }


def get_comprehensive_tax_service(db: Session) -> ComprehensiveTaxService:
    """Dependency injection helper for Flask"""
    return ComprehensiveTaxService(db)