"""
Async State Tax Service for Capricorn Portfolio Manager

Handles state-specific tax calculations for all 50 US states:
- State capital gains tax rates (2025 data)
- State income tax brackets
- Integration with federal tax calculations
- State tax optimization analysis

IMPORTANT: Tax rates should be updated annually (January 1st)
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.investor_profile_service import InvestorProfileService


class StateTaxService:
    """Async service for state tax calculations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.investor_service = InvestorProfileService(db)
        
        # 2025 State Tax Data - Capital Gains and Income Tax Rates
        # SOURCE: State tax websites and IRS publications (as of 2025)
        # TODO: Update these rates annually on January 1st
        self.state_tax_data = {
            # States with NO state income tax
            'AK': {'name': 'Alaska', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'FL': {'name': 'Florida', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'NV': {'name': 'Nevada', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'NH': {'name': 'New Hampshire', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax on wages'},
            'SD': {'name': 'South Dakota', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'TN': {'name': 'Tennessee', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'TX': {'name': 'Texas', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            'WA': {'name': 'Washington', 'capital_gains_rate': 0.07, 'income_tax_rate': 0.0, 'notes': 'Capital gains tax on high earners only'},
            'WY': {'name': 'Wyoming', 'capital_gains_rate': 0.0, 'income_tax_rate': 0.0, 'notes': 'No state income tax'},
            
            # States with preferential capital gains rates
            'AZ': {'name': 'Arizona', 'capital_gains_rate': 0.025, 'income_tax_rate': 0.045},
            'AR': {'name': 'Arkansas', 'capital_gains_rate': 0.0495, 'income_tax_rate': 0.066},
            'CO': {'name': 'Colorado', 'capital_gains_rate': 0.044, 'income_tax_rate': 0.044},
            'HI': {'name': 'Hawaii', 'capital_gains_rate': 0.075, 'income_tax_rate': 0.11},
            'LA': {'name': 'Louisiana', 'capital_gains_rate': 0.045, 'income_tax_rate': 0.085},
            'MO': {'name': 'Missouri', 'capital_gains_rate': 0.0465, 'income_tax_rate': 0.054},
            'MT': {'name': 'Montana', 'capital_gains_rate': 0.067, 'income_tax_rate': 0.067},
            'NM': {'name': 'New Mexico', 'capital_gains_rate': 0.0497, 'income_tax_rate': 0.059},
            'ND': {'name': 'North Dakota', 'capital_gains_rate': 0.029, 'income_tax_rate': 0.029},
            'SC': {'name': 'South Carolina', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.07},
            'VT': {'name': 'Vermont', 'capital_gains_rate': 0.075, 'income_tax_rate': 0.0875},
            'WI': {'name': 'Wisconsin', 'capital_gains_rate': 0.0605, 'income_tax_rate': 0.0765},
            
            # States that tax capital gains as ordinary income (high tax states)
            'AL': {'name': 'Alabama', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.05},
            'CA': {'name': 'California', 'capital_gains_rate': 0.133, 'income_tax_rate': 0.133},
            'CT': {'name': 'Connecticut', 'capital_gains_rate': 0.0699, 'income_tax_rate': 0.0699},
            'DE': {'name': 'Delaware', 'capital_gains_rate': 0.066, 'income_tax_rate': 0.066},
            'GA': {'name': 'Georgia', 'capital_gains_rate': 0.0575, 'income_tax_rate': 0.0575},
            'ID': {'name': 'Idaho', 'capital_gains_rate': 0.058, 'income_tax_rate': 0.058},
            'IL': {'name': 'Illinois', 'capital_gains_rate': 0.0495, 'income_tax_rate': 0.0495},
            'IN': {'name': 'Indiana', 'capital_gains_rate': 0.0323, 'income_tax_rate': 0.0323},
            'IA': {'name': 'Iowa', 'capital_gains_rate': 0.0853, 'income_tax_rate': 0.0853},
            'KS': {'name': 'Kansas', 'capital_gains_rate': 0.057, 'income_tax_rate': 0.057},
            'KY': {'name': 'Kentucky', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.05},
            'ME': {'name': 'Maine', 'capital_gains_rate': 0.075, 'income_tax_rate': 0.075},
            'MD': {'name': 'Maryland', 'capital_gains_rate': 0.0575, 'income_tax_rate': 0.0575},
            'MA': {'name': 'Massachusetts', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.05},
            'MI': {'name': 'Michigan', 'capital_gains_rate': 0.0425, 'income_tax_rate': 0.0425},
            'MN': {'name': 'Minnesota', 'capital_gains_rate': 0.0985, 'income_tax_rate': 0.0985},
            'MS': {'name': 'Mississippi', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.05},
            'NE': {'name': 'Nebraska', 'capital_gains_rate': 0.0684, 'income_tax_rate': 0.0684},
            'NJ': {'name': 'New Jersey', 'capital_gains_rate': 0.1075, 'income_tax_rate': 0.1075},
            'NY': {'name': 'New York', 'capital_gains_rate': 0.0882, 'income_tax_rate': 0.0882},  # CRITICAL: 8.82% not 6.85%!
            'NC': {'name': 'North Carolina', 'capital_gains_rate': 0.0475, 'income_tax_rate': 0.0475},
            'OH': {'name': 'Ohio', 'capital_gains_rate': 0.0399, 'income_tax_rate': 0.0399},
            'OK': {'name': 'Oklahoma', 'capital_gains_rate': 0.05, 'income_tax_rate': 0.05},
            'OR': {'name': 'Oregon', 'capital_gains_rate': 0.099, 'income_tax_rate': 0.099},
            'PA': {'name': 'Pennsylvania', 'capital_gains_rate': 0.0307, 'income_tax_rate': 0.0307},
            'RI': {'name': 'Rhode Island', 'capital_gains_rate': 0.0599, 'income_tax_rate': 0.0599},
            'UT': {'name': 'Utah', 'capital_gains_rate': 0.0495, 'income_tax_rate': 0.0495},
            'VA': {'name': 'Virginia', 'capital_gains_rate': 0.0575, 'income_tax_rate': 0.0575},
            'WV': {'name': 'West Virginia', 'capital_gains_rate': 0.065, 'income_tax_rate': 0.065},
            'DC': {'name': 'District of Columbia', 'capital_gains_rate': 0.0975, 'income_tax_rate': 0.0975},
        }
    
    def get_state_info(self, state_code: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive state tax information"""
        state_code = state_code.upper()
        if state_code not in self.state_tax_data:
            return None
        
        state_info = self.state_tax_data[state_code].copy()
        state_info['state_code'] = state_code
        return state_info
    
    async def calculate_state_capital_gains_tax(
        self,
        capital_gains_amount: float,
        gains_type: str = 'long_term'
    ) -> Dict[str, Any]:
        """
        Calculate state capital gains tax for the investor
        
        Args:
            capital_gains_amount: Amount of capital gains
            gains_type: 'short_term' or 'long_term' (both use same state rates)
            
        Returns:
            Dictionary with state tax calculation details
        """
        profile = await self.investor_service.get_or_create_profile()
        
        state_info = self.get_state_info(profile.state_of_residence)
        if not state_info:
            # Default to 5% if state not found
            state_info = {'capital_gains_rate': 0.05, 'name': profile.state_of_residence}
        
        # Calculate state tax owed
        state_rate = Decimal(str(state_info['capital_gains_rate']))
        state_tax_owed = Decimal(str(capital_gains_amount)) * state_rate if capital_gains_amount > 0 else Decimal('0.0')
        
        # Add local tax if applicable
        local_tax_owed = Decimal(str(capital_gains_amount)) * profile.local_tax_rate if capital_gains_amount > 0 else Decimal('0.0')
        
        total_state_local_tax = state_tax_owed + local_tax_owed
        
        return {
            'state_code': profile.state_of_residence,
            'state_name': state_info.get('name', profile.state_of_residence),
            'capital_gains_amount': capital_gains_amount,
            'gains_type': gains_type,
            'state_capital_gains_rate': float(state_rate),
            'state_capital_gains_rate_percent': float(state_rate * 100),
            'state_tax_owed': float(state_tax_owed),
            'local_tax_rate': float(profile.local_tax_rate),
            'local_tax_rate_percent': float(profile.local_tax_rate * 100),
            'local_tax_owed': float(local_tax_owed),
            'total_state_local_tax': float(total_state_local_tax),
            'total_state_local_rate_percent': float((state_rate + profile.local_tax_rate) * 100),
            'state_notes': state_info.get('notes', '')
        }

