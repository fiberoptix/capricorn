"""
State Tax Service for Portfolio Manager Application

Handles state-specific tax calculations including:
- State capital gains tax rates for all 50 states
- State income tax brackets and marginal rates
- Integration with federal tax calculations
- State-specific tax optimization strategies
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from app.models.portfolio_models import InvestorProfile, StateTaxRate
from .investor_profile_service import InvestorProfileService


class StateTaxService:
    """Service class for state tax calculations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.investor_service = InvestorProfileService(db)
        
        # 2025 State Tax Data - Capital Gains and Income Tax Rates
        self.state_tax_data = {
            # States with NO state income tax (and therefore no state capital gains tax)
            'AK': {'name': 'Alaska', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'FL': {'name': 'Florida', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'NV': {'name': 'Nevada', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'NH': {'name': 'New Hampshire', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax on wages'},
            'SD': {'name': 'South Dakota', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'TN': {'name': 'Tennessee', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'TX': {'name': 'Texas', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'WA': {'name': 'Washington', 'capital_gains_rate': 0.07, 'income_tax_rate': 0.0, 'notes': 'Capital gains tax on high earners only'},
            'WY': {'name': 'Wyoming', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            
            # States with preferential capital gains rates (lower than ordinary income)
            'AZ': {'name': 'Arizona', 'capital_gains_rate': 0.025, 'income_tax_rate': 0.045, 'notes': 'Capital gains taxed at preferential rate'},
            'AR': {'name': 'Arkansas', 'capital_gains_rate': 0.0495, 'income_tax_rate': 0.066, 'notes': '25% of capital gains excluded'},
            'CO': {'name': 'Colorado', 'capital_gains_rate': 0.044, 'income_tax_rate': 0.044, 'notes': 'Flat rate, same for all income'},
            'HI': {'name': 'Hawaii', 'capital_gains_rate': 0.075, 'income_tax_rate': 0.11, 'notes': 'Capital gains taxed at preferential rate'},
            'LA': {'name': 'Louisiana', 'capital_gains_rate': 0.045, 'income_tax_rate': 0.085, 'notes': 'Capital gains taxed at preferential rate'},
            'MO': {'name': 'Missouri', 'capital_gains_rate': 0.0465, 'income_tax_rate': 0.054, 'notes': 'Capital gains taxed at preferential rate'},
            'MT': {'name': 'Montana', 'capital_gains_rate': 0.067, 'income_tax_rate': 0.067, 'notes': 'Flat rate, same for all income'},
            'NM': {'name': 'New Mexico', 'capital_gains_rate': 0.0497, 'income_tax_rate': 0.059, 'notes': 'Capital gains taxed at preferential rate'},
            'ND': {'name': 'North Dakota', 'capital_gains_rate': 0.029, 'income_tax_rate': 0.029, 'notes': 'Flat rate, same for all income'},
            'SC': {'name': 'South Carolina', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.07, 'notes': 'Capital gains taxed at preferential rate'},
            'VT': {'name': 'Vermont', 'capital_gains_rate': 0.075, 'income_tax_rate': 0.0875, 'notes': 'Capital gains taxed at preferential rate'},
            'WI': {'name': 'Wisconsin', 'capital_gains_rate': 0.0605, 'income_tax_rate': 0.0765, 'notes': '30% of long-term capital gains excluded'},
            
            # States that tax capital gains as ordinary income (high tax states)
            'AL': {'name': 'Alabama', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.05, 'notes': 'Capital gains taxed as ordinary income'},
            'CA': {'name': 'California', 'capital_gains_rate': 0.133, 'income_tax_rate': 0.133, 'notes': 'Highest state tax rate in US'},
            'CT': {'name': 'Connecticut', 'capital_gains_rate': 0.0699, 'income_tax_rate': 0.0699, 'notes': 'Capital gains taxed as ordinary income'},
            'DE': {'name': 'Delaware', 'capital_gains_rate': 0.066, 'income_tax_rate': 0.066, 'notes': 'Capital gains taxed as ordinary income'},
            'GA': {'name': 'Georgia', 'capital_gains_rate': 0.0575, 'income_tax_rate': 0.0575, 'notes': 'Capital gains taxed as ordinary income'},
            'ID': {'name': 'Idaho', 'capital_gains_rate': 0.058, 'income_tax_rate': 0.058, 'notes': 'Capital gains taxed as ordinary income'},
            'IL': {'name': 'Illinois', 'capital_gains_rate': 0.0495, 'income_tax_rate': 0.0495, 'notes': 'Flat rate, same for all income'},
            'IN': {'name': 'Indiana', 'capital_gains_rate': 0.0323, 'income_tax_rate': 0.0323, 'notes': 'Flat rate, same for all income'},
            'IA': {'name': 'Iowa', 'capital_gains_rate': 0.0853, 'income_tax_rate': 0.0853, 'notes': 'Capital gains taxed as ordinary income'},
            'KS': {'name': 'Kansas', 'capital_gains_rate': 0.057, 'income_tax_rate': 0.057, 'notes': 'Capital gains taxed as ordinary income'},
            'KY': {'name': 'Kentucky', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.05, 'notes': 'Flat rate, same for all income'},
            'ME': {'name': 'Maine', 'capital_gains_rate': 0.075, 'income_tax_rate': 0.075, 'notes': 'Capital gains taxed as ordinary income'},
            'MD': {'name': 'Maryland', 'capital_gains_rate': 0.0575, 'income_tax_rate': 0.0575, 'notes': 'Capital gains taxed as ordinary income'},
            'MA': {'name': 'Massachusetts', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.05, 'notes': 'Flat rate, same for all income'},
            'MI': {'name': 'Michigan', 'capital_gains_rate': 0.0425, 'income_tax_rate': 0.0425, 'notes': 'Flat rate, same for all income'},
            'MN': {'name': 'Minnesota', 'capital_gains_rate': 0.0985, 'income_tax_rate': 0.0985, 'notes': 'Capital gains taxed as ordinary income'},
            'MS': {'name': 'Mississippi', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.05, 'notes': 'Capital gains taxed as ordinary income'},
            'NE': {'name': 'Nebraska', 'capital_gains_rate': 0.0684, 'income_tax_rate': 0.0684, 'notes': 'Capital gains taxed as ordinary income'},
            'NJ': {'name': 'New Jersey', 'capital_gains_rate': 0.1075, 'income_tax_rate': 0.1075, 'notes': 'Capital gains taxed as ordinary income'},
            'NY': {'name': 'New York', 'capital_gains_rate': 0.0882, 'income_tax_rate': 0.0882, 'notes': 'Capital gains taxed as ordinary income'},
            'NC': {'name': 'North Carolina', 'capital_gains_rate': 0.0475, 'income_tax_rate': 0.0475, 'notes': 'Flat rate, same for all income'},
            'OH': {'name': 'Ohio', 'capital_gains_rate': 0.0399, 'income_tax_rate': 0.0399, 'notes': 'Capital gains taxed as ordinary income'},
            'OK': {'name': 'Oklahoma', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.05, 'notes': 'Capital gains taxed as ordinary income'},
            'OR': {'name': 'Oregon', 'capital_gains_rate': 0.099, 'income_tax_rate': 0.099, 'notes': 'Capital gains taxed as ordinary income'},
            'PA': {'name': 'Pennsylvania', 'capital_gains_rate': 0.0307, 'income_tax_rate': 0.0307, 'notes': 'Flat rate, same for all income'},
            'RI': {'name': 'Rhode Island', 'capital_gains_rate': 0.0599, 'income_tax_rate': 0.0599, 'notes': 'Capital gains taxed as ordinary income'},
            'UT': {'name': 'Utah', 'capital_gains_rate': 0.0495, 'income_tax_rate': 0.0495, 'notes': 'Flat rate, same for all income'},
            'VA': {'name': 'Virginia', 'capital_gains_rate': 0.0575, 'income_tax_rate': 0.0575, 'notes': 'Capital gains taxed as ordinary income'},
            'WV': {'name': 'West Virginia', 'capital_gains_rate': 0.065, 'income_tax_rate': 0.065, 'notes': 'Capital gains taxed as ordinary income'},
            'DC': {'name': 'District of Columbia', 'capital_gains_rate': 0.0975, 'income_tax_rate': 0.0975, 'notes': 'Capital gains taxed as ordinary income'},
        }
    
    def get_state_info(self, state_code: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive state tax information
        
        Args:
            state_code: Two-letter state code (e.g., 'NY', 'CA')
            
        Returns:
            Dictionary with state tax information or None if not found
        """
        state_code = state_code.upper()
        if state_code not in self.state_tax_data:
            return None
        
        state_info = self.state_tax_data[state_code].copy()
        state_info['state_code'] = state_code
        return state_info
    
    def calculate_state_capital_gains_tax(
        self,
        investor_profile_id: int,
        capital_gains_amount: Decimal,
        gains_type: str = 'long_term'
    ) -> Dict[str, Any]:
        """
        Calculate state capital gains tax for an investor
        
        Args:
            investor_profile_id: Investor profile ID
            capital_gains_amount: Amount of capital gains
            gains_type: 'short_term' or 'long_term'
            
        Returns:
            Dictionary with state tax calculation details
        """
        profile = self.investor_service.get_profile(investor_profile_id)
        if not profile:
            raise ValueError(f"Investor profile {investor_profile_id} not found")
        
        state_info = self.get_state_info(profile.state_of_residence)
        if not state_info:
            raise ValueError(f"State tax data not available for {profile.state_of_residence}")
        
        # Calculate state tax owed
        state_rate = Decimal(str(state_info['capital_gains_rate']))
        state_tax_owed = capital_gains_amount * state_rate if capital_gains_amount > 0 else Decimal('0.0')
        
        # Add local tax if applicable
        local_tax_owed = capital_gains_amount * profile.local_tax_rate if capital_gains_amount > 0 else Decimal('0.0')
        
        total_state_local_tax = state_tax_owed + local_tax_owed
        
        return {
            'investor_profile_id': investor_profile_id,
            'state_code': profile.state_of_residence,
            'state_name': state_info['name'],
            'capital_gains_amount': float(capital_gains_amount),
            'gains_type': gains_type,
            'state_capital_gains_rate': float(state_rate),
            'state_capital_gains_rate_percent': float(state_rate * 100),
            'state_tax_owed': float(state_tax_owed),
            'local_tax_rate': float(profile.local_tax_rate),
            'local_tax_rate_percent': float(profile.local_tax_rate * 100),
            'local_tax_owed': float(local_tax_owed),
            'total_state_local_tax': float(total_state_local_tax),
            'total_state_local_rate_percent': float((state_rate + profile.local_tax_rate) * 100),
            'state_notes': state_info['notes']
        }
    
    def calculate_combined_tax_burden(
        self,
        investor_profile_id: int,
        capital_gains_amount: Decimal,
        gains_type: str = 'long_term',
        federal_tax_calculation: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Calculate combined federal + state + local tax burden
        
        Args:
            investor_profile_id: Investor profile ID
            capital_gains_amount: Amount of capital gains
            gains_type: 'short_term' or 'long_term'
            federal_tax_calculation: Pre-calculated federal tax data
            
        Returns:
            Comprehensive tax burden analysis
        """
        # Get state tax calculation
        state_tax = self.calculate_state_capital_gains_tax(
            investor_profile_id, capital_gains_amount, gains_type
        )
        
        # If federal tax not provided, we'll need to import and calculate it
        if federal_tax_calculation is None:
            from services.tax_calculation_service import TaxCalculationService, CapitalGainsType
            
            federal_service = TaxCalculationService(self.db)
            gains_type_enum = CapitalGainsType.LONG_TERM if gains_type == 'long_term' else CapitalGainsType.SHORT_TERM
            
            federal_tax_calculation = federal_service.calculate_federal_tax_owed(
                investor_profile_id, capital_gains_amount, gains_type_enum
            )
        
        # Calculate total tax burden
        federal_tax = Decimal(str(federal_tax_calculation['total_tax_owed']))
        state_local_tax = Decimal(str(state_tax['total_state_local_tax']))
        total_tax_burden = federal_tax + state_local_tax
        
        # Calculate after-tax proceeds
        after_tax_proceeds = capital_gains_amount - total_tax_burden if capital_gains_amount > 0 else capital_gains_amount
        
        # Calculate effective tax rate
        effective_rate = (total_tax_burden / capital_gains_amount * 100) if capital_gains_amount > 0 else Decimal('0.0')
        
        return {
            'investor_profile_id': investor_profile_id,
            'capital_gains_amount': float(capital_gains_amount),
            'gains_type': gains_type,
            
            # Federal taxes
            'federal_tax_owed': federal_tax_calculation['total_tax_owed'],
            'federal_rate_percent': federal_tax_calculation.get('total_federal_rate_percent', 0.0),
            
            # State taxes
            'state_code': state_tax['state_code'],
            'state_name': state_tax['state_name'],
            'state_tax_owed': state_tax['state_tax_owed'],
            'state_rate_percent': state_tax['state_capital_gains_rate_percent'],
            
            # Local taxes
            'local_tax_owed': state_tax['local_tax_owed'],
            'local_rate_percent': state_tax['local_tax_rate_percent'],
            
            # Totals
            'total_tax_burden': float(total_tax_burden),
            'after_tax_proceeds': float(after_tax_proceeds),
            'effective_tax_rate_percent': float(effective_rate),
            
            # Breakdown
            'tax_breakdown': {
                'federal': federal_tax_calculation['total_tax_owed'],
                'state': state_tax['state_tax_owed'],
                'local': state_tax['local_tax_owed'],
                'total': float(total_tax_burden)
            }
        }
    
    def compare_state_tax_rates(self, capital_gains_amount: Decimal = Decimal('10000')) -> List[Dict[str, Any]]:
        """
        Compare capital gains tax rates across all states
        
        Args:
            capital_gains_amount: Amount to use for comparison (default $10,000)
            
        Returns:
            List of states sorted by tax burden (lowest to highest)
        """
        state_comparisons = []
        
        for state_code, state_data in self.state_tax_data.items():
            tax_owed = capital_gains_amount * Decimal(str(state_data['capital_gains_rate']))
            effective_rate = (tax_owed / capital_gains_amount * 100) if capital_gains_amount > 0 else Decimal('0.0')
            
            state_comparisons.append({
                'state_code': state_code,
                'state_name': state_data['name'],
                'capital_gains_rate': state_data['capital_gains_rate'],
                'capital_gains_rate_percent': state_data['capital_gains_rate'] * 100,
                'tax_owed_on_amount': float(tax_owed),
                'effective_rate_percent': float(effective_rate),
                'notes': state_data['notes']
            })
        
        # Sort by effective tax rate (lowest to highest)
        state_comparisons.sort(key=lambda x: x['effective_rate_percent'])
        
        return state_comparisons
    
    def get_tax_friendly_states(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most tax-friendly states for capital gains
        
        Args:
            limit: Number of states to return
            
        Returns:
            List of most tax-friendly states
        """
        all_states = self.compare_state_tax_rates()
        return all_states[:limit]
    
    def get_high_tax_states(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the highest tax burden states for capital gains
        
        Args:
            limit: Number of states to return
            
        Returns:
            List of highest tax burden states
        """
        all_states = self.compare_state_tax_rates()
        return all_states[-limit:]
    
    def analyze_relocation_tax_savings(
        self,
        investor_profile_id: int,
        target_state: str,
        annual_capital_gains: Decimal
    ) -> Dict[str, Any]:
        """
        Analyze potential tax savings from relocating to a different state
        
        Args:
            investor_profile_id: Current investor profile
            target_state: Target state code
            annual_capital_gains: Expected annual capital gains
            
        Returns:
            Relocation tax analysis
        """
        profile = self.investor_service.get_profile(investor_profile_id)
        if not profile:
            raise ValueError(f"Investor profile {investor_profile_id} not found")
        
        current_state = profile.state_of_residence
        current_tax = self.calculate_state_capital_gains_tax(
            investor_profile_id, annual_capital_gains
        )
        
        # Calculate tax in target state (temporarily modify profile)
        target_state_info = self.get_state_info(target_state)
        if not target_state_info:
            raise ValueError(f"State tax data not available for {target_state}")
        
        target_rate = Decimal(str(target_state_info['capital_gains_rate']))
        target_tax_owed = annual_capital_gains * target_rate
        target_local_tax = annual_capital_gains * profile.local_tax_rate  # Assume same local rate
        target_total_tax = target_tax_owed + target_local_tax
        
        # Calculate savings
        current_total_tax = Decimal(str(current_tax['total_state_local_tax']))
        tax_savings = current_total_tax - target_total_tax
        savings_percent = (tax_savings / current_total_tax * 100) if current_total_tax > 0 else Decimal('0.0')
        
        return {
            'investor_profile_id': investor_profile_id,
            'annual_capital_gains': float(annual_capital_gains),
            'current_state': {
                'code': current_state,
                'name': self.state_tax_data[current_state]['name'],
                'tax_owed': current_tax['total_state_local_tax'],
                'rate_percent': current_tax['total_state_local_rate_percent']
            },
            'target_state': {
                'code': target_state,
                'name': target_state_info['name'],
                'tax_owed': float(target_total_tax),
                'rate_percent': float((target_rate + profile.local_tax_rate) * 100)
            },
            'tax_savings': {
                'annual_savings': float(tax_savings),
                'savings_percent': float(savings_percent),
                'is_beneficial': tax_savings > 0
            },
            'analysis': {
                'current_effective_rate': current_tax['total_state_local_rate_percent'],
                'target_effective_rate': float((target_rate + profile.local_tax_rate) * 100),
                'recommendation': 'beneficial' if tax_savings > 0 else 'not_beneficial'
            }
        }


def get_state_tax_service(db: Session) -> StateTaxService:
    """Dependency injection helper for Flask"""
    return StateTaxService(db)