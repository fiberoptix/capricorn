"""
Retirement Calculator Service
Ports calculations from retirement_manager TypeScript to Python
Uses existing Tax API for all tax calculations
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.user_profile import UserProfile
from app.services.tax_calculation_service import TaxCalculationService
from app.core.constants import SINGLE_USER_ID

logger = logging.getLogger(__name__)

class RetirementCalculator:
    """Calculate retirement projections and analysis"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.current_year = 2025
        self.tax_service = TaxCalculationService(db)
    
    @staticmethod
    def _get_value(profile: Dict[str, Any], key: str, default: float = 0.0) -> float:
        """Safely get a numeric value from profile, handling None"""
        value = profile.get(key)
        return float(value) if value is not None else default
    
    async def calculate_all(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Master calculation method
        Returns all calculations: projections, assets, retirement, transition, summary
        """
        try:
            # Calculate user and partner retirement years
            user_retirement_year = self.current_year + profile.get('user_years_to_retirement', 25)
            partner_retirement_year = self.current_year + profile.get('partner_years_to_retirement', 30)
            total_years = max(
                profile.get('user_years_to_retirement', 25),
                profile.get('partner_years_to_retirement', 30),
                30  # Ensure minimum 30 years
            )
            
            # Generate yearly projections
            yearly_projections = await self.calculate_yearly_projections(
                profile, user_retirement_year, partner_retirement_year, total_years
            )
            
            # Calculate asset growth
            asset_growth = await self.calculate_asset_growth(
                profile, yearly_projections, user_retirement_year, partner_retirement_year
            )
            
            # Merge asset values into yearly projections for comprehensive display
            for i, projection in enumerate(yearly_projections):
                if i < len(asset_growth):
                    projection['userAccount401k'] = asset_growth[i]['userAccount401k']
                    projection['partnerAccount401k'] = asset_growth[i]['partnerAccount401k']
                    projection['accountIRA'] = asset_growth[i]['accountIRA']
                    projection['accountSavings'] = asset_growth[i]['accountSavings']
                    projection['accountTrading'] = asset_growth[i]['accountTrading']
                    projection['inheritance'] = asset_growth[i]['inheritance']
                    projection['totalAssets'] = asset_growth[i]['totalAssets']
                    projection['netWorth'] = asset_growth[i]['totalAssets']  # Net worth = total assets
            
            # Retirement analysis
            retirement_analysis = await self.calculate_retirement_analysis(
                profile, asset_growth[-1] if asset_growth else {}
            )
            
            # Transition analysis
            transition_analysis = await self.calculate_transition_analysis(
                profile, yearly_projections, asset_growth, user_retirement_year, partner_retirement_year
            )
            
            return {
                'yearly_projections': yearly_projections,
                'asset_growth': asset_growth,
                'retirement_analysis': retirement_analysis,
                'transition_analysis': transition_analysis,
                'summary': {
                    'total_years': total_years,
                    'user_retirement_year': user_retirement_year,
                    'partner_retirement_year': partner_retirement_year,
                    'final_assets': asset_growth[-1]['totalAssets'] if asset_growth else 0,
                }
            }
        except Exception as e:
            logger.error(f"Error in calculate_all: {e}", exc_info=True)
            raise
    
    async def calculate_yearly_projections(
        self,
        profile: Dict[str, Any],
        user_retirement_year: int,
        partner_retirement_year: int,
        total_years: int
    ) -> List[Dict[str, Any]]:
        """
        Calculate 30-year financial projections
        """
        projections = []
        
        for year_index in range(total_years):
            year = self.current_year + year_index
            projection = await self._calculate_year_projection(
                profile, year, year_index, user_retirement_year, partner_retirement_year
            )
            projections.append(projection)
        
        return projections
    
    async def _calculate_year_projection(
        self,
        profile: Dict[str, Any],
        year: int,
        year_index: int,
        user_retirement_year: int,
        partner_retirement_year: int
    ) -> Dict[str, Any]:
        """Calculate single year's financial projection"""
        
        # Helper to get values
        gv = self._get_value
        
        # Income calculations with raises
        user_salary = (
            gv(profile, 'user_salary', 100000) * ((1 + gv(profile, 'user_raise_rate', 0.05)) ** year_index)
            if year <= user_retirement_year else 0
        )
        user_bonus = user_salary * gv(profile, 'user_bonus_rate', 0.05) if year <= user_retirement_year else 0
        
        partner_salary = (
            gv(profile, 'partner_salary', 80000) * ((1 + gv(profile, 'partner_raise_rate', 0.05)) ** year_index)
            if year <= partner_retirement_year else 0
        )
        partner_bonus = partner_salary * gv(profile, 'partner_bonus_rate', 0.05) if year <= partner_retirement_year else 0
        
        gross_income = user_salary + user_bonus + partner_salary + partner_bonus
        
        # 401K contributions
        user_401k_contribution = gv(profile, 'user_401k_contribution', 12000) if year <= user_retirement_year else 0
        partner_401k_contribution = gv(profile, 'partner_401k_contribution', 0) if year <= partner_retirement_year else 0
        total_401k_contribution = user_401k_contribution + partner_401k_contribution
        
        # Taxable income
        taxable_income = gross_income - total_401k_contribution
        
        # Calculate taxes using existing Tax API
        total_taxes = 0
        tax_rates = {'federal': 0, 'state': 0, 'local': 0, 'total': 0}
        
        if taxable_income > 0:
            try:
                tax_result = await self.tax_service.calculate_income_tax(
                    income=taxable_income,
                    filing_status=profile.get('filing_status', 'married_filing_jointly'),
                    state=profile.get('state', 'NY'),
                    local_tax_rate=profile.get('local_tax_rate', 0.01),
                    year=2025
                )
                total_taxes = tax_result['total_tax']
                # Extract rates from nested structure returned by Tax API
                tax_rates['federal'] = tax_result.get('federal', {}).get('effective_rate', 0)
                tax_rates['state'] = tax_result.get('state', {}).get('effective_rate', 0)
                tax_rates['local'] = tax_result.get('local', {}).get('rate', 0)
                tax_rates['total'] = tax_result.get('effective_rate', 0)
            except Exception as e:
                logger.warning(f"Tax calculation failed for year {year}: {e}")
                total_taxes = taxable_income * 0.20  # Fallback rate
                tax_rates['total'] = 0.20
        
        # Take home pay
        take_home_pay = gross_income - total_401k_contribution - total_taxes
        
        # Expenses with inflation
        essential_expenses = gv(profile, 'monthly_living_expenses', 6000) * 12 * ((1 + gv(profile, 'annual_inflation_rate', 0.04)) ** year_index)
        discretionary_expenses = gv(profile, 'annual_discretionary_spending', 24000) * ((1 + gv(profile, 'annual_inflation_rate', 0.04)) ** year_index)
        total_expenses = essential_expenses + discretionary_expenses
        
        # Savings calculation
        leftover_money = take_home_pay - total_expenses
        monthly_leftover = max(0, leftover_money / 12)
        
        fixed_amount = gv(profile, 'fixed_monthly_savings', 1000)
        savings_rate = gv(profile, 'percentage_of_leftover', 0.50)
        
        if fixed_amount > 0:
            monthly_savings = fixed_amount
        elif savings_rate > 0 and monthly_leftover > 0:
            monthly_savings = monthly_leftover * savings_rate
        else:
            monthly_savings = max(fixed_amount, monthly_leftover * savings_rate)
        
        monthly_savings = max(0, monthly_savings)
        annual_savings = monthly_savings * 12
        
        # Withdrawals during transition
        total_withdrawals = 0
        if year >= user_retirement_year and year < partner_retirement_year:
            partner_net_income = partner_salary * (1 - tax_rates['total'])
            if total_expenses > partner_net_income:
                total_withdrawals = total_expenses - partner_net_income
        
        return {
            'year': year,
            'user_salary': round(user_salary, 2),
            'user_bonus': round(user_bonus, 2),
            'partner_salary': round(partner_salary, 2),
            'partner_bonus': round(partner_bonus, 2),
            'gross_income': round(gross_income, 2),
            'taxable_income': round(taxable_income, 2),
            'federal_tax_rate': round(tax_rates['federal'], 4),
            'state_tax_rate': round(tax_rates['state'], 4),
            'local_tax_rate': round(tax_rates['local'], 4),
            'total_effective_rate': round(tax_rates['total'], 4),
            'total_taxes': round(total_taxes, 2),
            'take_home_pay': round(take_home_pay, 2),
            'essential_expenses': round(essential_expenses, 2),
            'discretionary_expenses': round(discretionary_expenses, 2),
            'total_expenses': round(total_expenses, 2),
            'leftover_money': round(leftover_money, 2),
            'monthly_leftover': round(monthly_leftover, 2),
            'monthly_savings': round(monthly_savings, 2),
            'annual_savings': round(annual_savings, 2),
            'total_withdrawals': round(total_withdrawals, 2),
        }
    
    async def calculate_asset_growth(
        self,
        profile: Dict[str, Any],
        yearly_projections: List[Dict[str, Any]],
        user_retirement_year: int,
        partner_retirement_year: int
    ) -> List[Dict[str, Any]]:
        """Calculate asset growth over time"""
        
        asset_growth = []
        
        # Helper function
        gv = self._get_value
        
        # Starting balances
        user_401k = gv(profile, 'user_current_401k_balance', 0)
        partner_401k = gv(profile, 'partner_current_401k_balance', 0)
        ira = gv(profile, 'current_ira_balance', 0)
        savings = 0
        trading = gv(profile, 'current_trading_balance', 0)
        inheritance = 0
        cumulative_savings = 0
        
        for i, projection in enumerate(yearly_projections):
            year = projection['year']
            
            if i > 0:
                # User 401K growth
                user_contributions = (
                    gv(profile, 'user_401k_contribution', 12000) + gv(profile, 'user_employer_match', 1000)
                    if year <= user_retirement_year else 0
                )
                user_401k = (user_401k + user_contributions) * (1 + gv(profile, 'user_401k_growth_rate', 0.10))
                
                # Partner 401K growth
                partner_contributions = (
                    gv(profile, 'partner_401k_contribution', 0) + gv(profile, 'partner_employer_match', 0)
                    if year <= partner_retirement_year else 0
                )
                partner_401k = (partner_401k + partner_contributions) * (1 + gv(profile, 'partner_401k_growth_rate', 0.10))
                
                # IRA growth
                ira = ira * (1 + gv(profile, 'ira_return_rate', 0.10))
                
                # Savings accumulation (0% growth during year)
                new_savings = projection['annual_savings']
                withdrawals = projection['total_withdrawals']
                savings += new_savings
                
                # Year-end transfer to trading if selected
                if profile.get('savings_destination', 'trading') == 'trading':
                    trading += savings
                    savings = 0
                
                # Trading account growth
                trading = (trading - withdrawals) * (1 + gv(profile, 'trading_return_rate', 0.10))
                
                # Inheritance
                if year == self.current_year + int(gv(profile, 'inheritance_year', 20)):
                    inheritance = gv(profile, 'expected_inheritance', 0)
                elif inheritance > 0:
                    inheritance = inheritance * (1 + gv(profile, 'trading_return_rate', 0.10))
                
                cumulative_savings += new_savings
            
            total_assets = user_401k + partner_401k + ira + savings + trading + inheritance
            annual_growth = total_assets - asset_growth[-1]['totalAssets'] if i > 0 else 0
            uninvested_surplus = projection['leftover_money'] - projection['annual_savings']
            
            asset_growth.append({
                'year': year,
                'userAccount401k': round(user_401k, 2),
                'partnerAccount401k': round(partner_401k, 2),
                'accountIRA': round(ira, 2),
                'accountSavings': round(savings, 2),
                'accountTrading': round(trading, 2),
                'inheritance': round(inheritance, 2),
                'totalAssets': round(total_assets, 2),
                'annualGrowth': round(annual_growth, 2),
                'cumulativeSavings': round(cumulative_savings, 2),
                'uninvestedSurplus': round(uninvested_surplus, 2),
            })
        
        return asset_growth
    
    async def calculate_retirement_analysis(
        self,
        profile: Dict[str, Any],
        final_assets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate retirement sustainability analysis"""
        
        # Final asset values
        total_assets = final_assets.get('totalAssets', 0)
        user_401k = final_assets.get('userAccount401k', 0)
        partner_401k = final_assets.get('partnerAccount401k', 0)
        ira = final_assets.get('accountIRA', 0)
        trading = final_assets.get('accountTrading', 0)
        inheritance_val = final_assets.get('inheritance', 0)
        
        # Tax-deferred vs taxable assets
        tax_deferred_assets = user_401k + partner_401k + ira
        taxable_assets = trading + inheritance_val
        
        # Helper function
        gv = self._get_value
        
        # Withdrawal calculations (4% rule)
        withdrawal_rate = gv(profile, 'withdrawal_rate', 0.04)
        retirement_duration = int(gv(profile, 'years_of_retirement', 30))
        
        annual_gross_withdrawal = total_assets * withdrawal_rate
        monthly_gross_withdrawal = annual_gross_withdrawal / 12
        
        # Estimate taxes on withdrawal (reuse Tax API)
        monthly_tax = monthly_gross_withdrawal * 0.125  # Simplified for now
        monthly_net = monthly_gross_withdrawal - monthly_tax
        
        # Target monthly need (current expenses with inflation to retirement)
        years_to_retirement = int(gv(profile, 'user_years_to_retirement', 25))
        monthly_expenses = gv(profile, 'monthly_living_expenses', 6000)
        annual_discretionary = gv(profile, 'annual_discretionary_spending', 24000)
        inflation_rate = gv(profile, 'annual_inflation_rate', 0.04)
        
        future_monthly_expenses = monthly_expenses * ((1 + inflation_rate) ** years_to_retirement)
        future_annual_discretionary = annual_discretionary * ((1 + inflation_rate) ** years_to_retirement)
        target_monthly_need = future_monthly_expenses + (future_annual_discretionary / 12)
        
        # Lifestyle analysis
        monthly_surplus = monthly_net - target_monthly_need
        lifestyle_multiple = monthly_net / target_monthly_need if target_monthly_need > 0 else 0
        
        # Status indicators
        retirement_goal = "Achieved" if lifestyle_multiple >= 1.0 else "At Risk"
        savings_target = "On Track" if total_assets > 0 else "Behind"
        asset_growth_status = "Strong" if total_assets > 1000000 else "Moderate"
        
        return {
            'finalAssetValues': {
                'userAccount401k': round(user_401k, 2),
                'partnerAccount401k': round(partner_401k, 2),
                'accountIRA': round(ira, 2),
                'accountTrading': round(trading, 2),
                'inheritance': round(inheritance_val, 2),
                'totalAssets': round(total_assets, 2),
            },
            'withdrawalAnalysis': {
                'monthlyGrossWithdrawal': round(monthly_gross_withdrawal, 2),
                'monthlyTax': round(monthly_tax, 2),
                'monthlyNetWithdrawal': round(monthly_net, 2),
            },
            'lifestyleAnalysis': {
                'targetMonthlyNeed': round(target_monthly_need, 2),
                'monthlySurplus': round(monthly_surplus, 2),
                'lifestyleMultiple': round(lifestyle_multiple, 2),
            },
            'statusIndicators': {
                'retirementGoal': retirement_goal,
                'savingsTarget': savings_target,
                'assetGrowth': asset_growth_status,
            }
        }
    
    async def calculate_transition_analysis(
        self,
        profile: Dict[str, Any],
        yearly_projections: List[Dict[str, Any]],
        asset_growth: List[Dict[str, Any]],
        user_retirement_year: int,
        partner_retirement_year: int
    ) -> Dict[str, Any]:
        """Calculate transition period analysis (when one partner retires before the other)"""
        
        transition_duration = partner_retirement_year - user_retirement_year
        
        if transition_duration <= 0:
            return {
                'transitionPeriod': {
                    'duration': 0,
                    'startYear': user_retirement_year,
                    'endYear': partner_retirement_year,
                    'message': 'Both retire in the same year - no transition period'
                }
            }
        
        # Find transition year projections
        start_year_idx = user_retirement_year - self.current_year
        mid_year_idx = ((user_retirement_year + partner_retirement_year) // 2) - self.current_year
        end_year_idx = partner_retirement_year - self.current_year
        
        def get_projection(idx):
            return yearly_projections[idx] if 0 <= idx < len(yearly_projections) else {}
        
        start_projection = get_projection(start_year_idx)
        mid_projection = get_projection(mid_year_idx) if transition_duration > 2 else None
        end_projection = get_projection(end_year_idx)
        
        return {
            'transitionPeriod': {
                'duration': transition_duration,
                'startYear': user_retirement_year,
                'endYear': partner_retirement_year,
                'userRetirementYear': user_retirement_year,
                'partnerRetirementYear': partner_retirement_year,
            },
            'incomeAnalysis': {
                'partnerSalaryStart': start_projection.get('partner_salary', 0),
                'partnerSalaryMid': mid_projection.get('partner_salary', 0) if mid_projection else 0,
                'partnerSalaryEnd': end_projection.get('partner_salary', 0),
            },
            'expenseCoverage': {
                'expensesStart': start_projection.get('total_expenses', 0),
                'expensesMid': mid_projection.get('total_expenses', 0) if mid_projection else 0,
                'expensesEnd': end_projection.get('total_expenses', 0),
            }
        }

