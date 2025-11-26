"""
Async InvestorProfile Service for Capricorn Portfolio Manager

Handles investor profile management with single-user architecture:
- Auto-creates profile ID=1 if missing
- Tax calculations and settings
- Progressive tax bracket calculations
"""

from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload

from app.models.portfolio_models import InvestorProfile, Portfolio
from app.core.constants import SINGLE_USER_ID


class InvestorProfileService:
    """Async service for investor profile operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_profile(self) -> InvestorProfile:
        """
        Get the single user's investor profile or create default one
        
        Returns:
            InvestorProfile object (always ID=1)
        """
        # Try to get existing profile
        result = await self.db.execute(
            select(InvestorProfile).where(InvestorProfile.id == SINGLE_USER_ID)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            # Create default profile with specified values
            profile = InvestorProfile(
                id=SINGLE_USER_ID,
                name="Primary Investor",
                annual_household_income=Decimal('300000'),
                filing_status='married_filing_jointly',
                state_of_residence='NY',
                local_tax_rate=Decimal('0.01')  # 1.0%
            )
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
            
        return profile
    
    async def get_profile(self) -> Optional[InvestorProfile]:
        """
        Get the investor profile (single user system)
        
        Returns:
            InvestorProfile object or None
        """
        result = await self.db.execute(
            select(InvestorProfile).where(InvestorProfile.id == SINGLE_USER_ID)
        )
        return result.scalar_one_or_none()
    
    async def update_profile(
        self,
        name: str = None,
        annual_household_income: Decimal = None,
        filing_status: str = None,
        state_of_residence: str = None,
        local_tax_rate: Decimal = None
    ) -> InvestorProfile:
        """
        Update the investor profile
        
        Args:
            name: Updated name
            annual_household_income: Updated income
            filing_status: single, married_filing_jointly, married_filing_separately, head_of_household
            state_of_residence: 2-letter state code
            local_tax_rate: Local tax rate as decimal (0.01 = 1%)
            
        Returns:
            Updated InvestorProfile
        """
        profile = await self.get_or_create_profile()
        
        # Validate and update fields
        if name is not None:
            profile.name = name
            
        if annual_household_income is not None:
            if annual_household_income <= 0:
                raise ValueError("Annual household income must be positive")
            profile.annual_household_income = annual_household_income
            
        if filing_status is not None:
            valid_statuses = ['single', 'married_filing_jointly', 'married_filing_separately', 'head_of_household']
            if filing_status not in valid_statuses:
                raise ValueError(f"Filing status must be one of: {', '.join(valid_statuses)}")
            profile.filing_status = filing_status
            
        if state_of_residence is not None:
            if len(state_of_residence) != 2 or not state_of_residence.isalpha():
                raise ValueError("State must be a 2-letter code")
            profile.state_of_residence = state_of_residence.upper()
            
        if local_tax_rate is not None:
            if local_tax_rate < 0 or local_tax_rate > Decimal('0.20'):
                raise ValueError("Local tax rate must be between 0% and 20%")
            profile.local_tax_rate = local_tax_rate
        
        profile.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(profile)
        
        return profile
    
    async def get_tax_settings(self) -> Dict[str, Any]:
        """
        Get tax settings for the profile
        
        Returns:
            Dictionary with tax settings
        """
        profile = await self.get_or_create_profile()
        
        return {
            'profile_id': profile.id,
            'name': profile.name,
            'annual_household_income': float(profile.annual_household_income),
            'filing_status': profile.filing_status,
            'state_of_residence': profile.state_of_residence,
            'local_tax_rate': float(profile.local_tax_rate),
            'local_tax_rate_percent': float(profile.local_tax_rate) * 100,
            'tax_year': datetime.now().year
        }
    
    async def calculate_tax_brackets(self) -> Dict[str, Any]:
        """
        Calculate applicable tax brackets for the investor
        
        Returns:
            Dictionary with tax bracket information
        """
        profile = await self.get_or_create_profile()
        
        # 2025 Federal Tax Brackets
        if profile.filing_status in ['married_filing_jointly', 'married_filing_separately']:
            brackets = [
                {'rate': 0.10, 'min': 0, 'max': 22000},
                {'rate': 0.12, 'min': 22000, 'max': 89450},
                {'rate': 0.22, 'min': 89450, 'max': 190750},
                {'rate': 0.24, 'min': 190750, 'max': 364200},
                {'rate': 0.32, 'min': 364200, 'max': 462500},
                {'rate': 0.35, 'min': 462500, 'max': 693750},
                {'rate': 0.37, 'min': 693750, 'max': float('inf')}
            ]
        else:  # single or head_of_household
            brackets = [
                {'rate': 0.10, 'min': 0, 'max': 11000},
                {'rate': 0.12, 'min': 11000, 'max': 44725},
                {'rate': 0.22, 'min': 44725, 'max': 95375},
                {'rate': 0.24, 'min': 95375, 'max': 182050},
                {'rate': 0.32, 'min': 182050, 'max': 231250},
                {'rate': 0.35, 'min': 231250, 'max': 578125},
                {'rate': 0.37, 'min': 578125, 'max': float('inf')}
            ]
        
        income = float(profile.annual_household_income)
        applicable_brackets = []
        marginal_rate = 0.10
        
        for bracket in brackets:
            if income > bracket['min']:
                bracket_info = {
                    'rate': bracket['rate'],
                    'rate_percent': bracket['rate'] * 100,
                    'min_income': bracket['min'],
                    'max_income': bracket['max'] if bracket['max'] != float('inf') else 'unlimited',
                    'applies': True
                }
                applicable_brackets.append(bracket_info)
                
                if income <= bracket['max'] or bracket['max'] == float('inf'):
                    marginal_rate = bracket['rate']
                    if income < bracket['max']:
                        break
        
        # NIIT (Net Investment Income Tax) check
        niit_threshold = 250000 if profile.filing_status == 'married_filing_jointly' else 200000
        niit_applies = income > niit_threshold
        
        # State tax info (simplified for NY)
        state_tax_rate = 0.0685 if profile.state_of_residence == 'NY' else 0.05  # Default 5%
        
        return {
            'profile_id': profile.id,
            'annual_household_income': income,
            'filing_status': profile.filing_status,
            'marginal_tax_rate': marginal_rate,
            'marginal_tax_rate_percent': marginal_rate * 100,
            'applicable_brackets': applicable_brackets,
            'niit_applies': niit_applies,
            'niit_rate': 0.038 if niit_applies else 0.0,
            'niit_rate_percent': 3.8 if niit_applies else 0.0,
            'state_of_residence': profile.state_of_residence,
            'state_tax_rate': state_tax_rate,
            'state_tax_rate_percent': state_tax_rate * 100,
            'local_tax_rate': float(profile.local_tax_rate),
            'local_tax_rate_percent': float(profile.local_tax_rate) * 100,
            'combined_rate': marginal_rate + state_tax_rate + float(profile.local_tax_rate) + (0.038 if niit_applies else 0),
            'combined_rate_percent': (marginal_rate + state_tax_rate + float(profile.local_tax_rate) + (0.038 if niit_applies else 0)) * 100
        }
    
    async def calculate_capital_gains_tax(
        self, 
        capital_gains: float,
        is_long_term: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate tax on capital gains
        
        Args:
            capital_gains: Amount of capital gains
            is_long_term: Whether gains are long-term (>1 year)
            
        Returns:
            Dictionary with tax calculation details
        """
        profile = await self.get_or_create_profile()
        base_income = float(profile.annual_household_income)
        
        if is_long_term:
            # Long-term capital gains rates (2025)
            if profile.filing_status == 'married_filing_jointly':
                ltcg_brackets = [
                    {'rate': 0.00, 'min': 0, 'max': 96700},
                    {'rate': 0.15, 'min': 96700, 'max': 600050},
                    {'rate': 0.20, 'min': 600050, 'max': float('inf')}
                ]
            else:
                ltcg_brackets = [
                    {'rate': 0.00, 'min': 0, 'max': 48350},
                    {'rate': 0.15, 'min': 48350, 'max': 533400},
                    {'rate': 0.20, 'min': 533400, 'max': float('inf')}
                ]
            
            # Find applicable LTCG rate
            ltcg_rate = 0.0
            for bracket in ltcg_brackets:
                if base_income < bracket['max']:
                    ltcg_rate = bracket['rate']
                    break
            
            federal_tax = capital_gains * ltcg_rate
            tax_type = 'long_term_capital_gains'
        else:
            # Short-term gains taxed as ordinary income
            tax_brackets = await self.calculate_tax_brackets()
            marginal_rate = tax_brackets['marginal_tax_rate']
            federal_tax = capital_gains * marginal_rate
            ltcg_rate = marginal_rate
            tax_type = 'short_term_capital_gains'
        
        # NIIT calculation
        niit_threshold = 250000 if profile.filing_status == 'married_filing_jointly' else 200000
        niit_tax = capital_gains * 0.038 if base_income > niit_threshold else 0.0
        
        # State tax (using StateTaxService for accuracy)
        from app.services.state_tax_service import StateTaxService
        state_service = StateTaxService(self.db)
        state_tax_data = await state_service.calculate_state_capital_gains_tax(
            capital_gains,
            'long_term' if is_long_term else 'short_term'
        )
        state_tax = state_tax_data['state_tax_owed']
        local_tax = state_tax_data['local_tax_owed']
        
        total_tax = federal_tax + niit_tax + state_tax + local_tax
        after_tax_proceeds = capital_gains - total_tax
        effective_rate = (total_tax / capital_gains) if capital_gains > 0 else 0.0
        
        return {
            'capital_gains_amount': capital_gains,
            'tax_type': tax_type,
            'is_long_term': is_long_term,
            'federal_rate': ltcg_rate,
            'federal_rate_percent': ltcg_rate * 100,
            'federal_tax': federal_tax,
            'niit_tax': niit_tax,
            'state_tax': state_tax,
            'local_tax': local_tax,
            'total_tax': total_tax,
            'after_tax_proceeds': after_tax_proceeds,
            'effective_rate': effective_rate,
            'effective_rate_percent': effective_rate * 100
        }
    
    async def get_state_list(self) -> List[Dict[str, str]]:
        """
        Get list of US states for dropdown
        
        Returns:
            List of state codes and names
        """
        states = [
            {'code': 'AL', 'name': 'Alabama'},
            {'code': 'AK', 'name': 'Alaska'},
            {'code': 'AZ', 'name': 'Arizona'},
            {'code': 'AR', 'name': 'Arkansas'},
            {'code': 'CA', 'name': 'California'},
            {'code': 'CO', 'name': 'Colorado'},
            {'code': 'CT', 'name': 'Connecticut'},
            {'code': 'DE', 'name': 'Delaware'},
            {'code': 'FL', 'name': 'Florida'},
            {'code': 'GA', 'name': 'Georgia'},
            {'code': 'HI', 'name': 'Hawaii'},
            {'code': 'ID', 'name': 'Idaho'},
            {'code': 'IL', 'name': 'Illinois'},
            {'code': 'IN', 'name': 'Indiana'},
            {'code': 'IA', 'name': 'Iowa'},
            {'code': 'KS', 'name': 'Kansas'},
            {'code': 'KY', 'name': 'Kentucky'},
            {'code': 'LA', 'name': 'Louisiana'},
            {'code': 'ME', 'name': 'Maine'},
            {'code': 'MD', 'name': 'Maryland'},
            {'code': 'MA', 'name': 'Massachusetts'},
            {'code': 'MI', 'name': 'Michigan'},
            {'code': 'MN', 'name': 'Minnesota'},
            {'code': 'MS', 'name': 'Mississippi'},
            {'code': 'MO', 'name': 'Missouri'},
            {'code': 'MT', 'name': 'Montana'},
            {'code': 'NE', 'name': 'Nebraska'},
            {'code': 'NV', 'name': 'Nevada'},
            {'code': 'NH', 'name': 'New Hampshire'},
            {'code': 'NJ', 'name': 'New Jersey'},
            {'code': 'NM', 'name': 'New Mexico'},
            {'code': 'NY', 'name': 'New York'},
            {'code': 'NC', 'name': 'North Carolina'},
            {'code': 'ND', 'name': 'North Dakota'},
            {'code': 'OH', 'name': 'Ohio'},
            {'code': 'OK', 'name': 'Oklahoma'},
            {'code': 'OR', 'name': 'Oregon'},
            {'code': 'PA', 'name': 'Pennsylvania'},
            {'code': 'RI', 'name': 'Rhode Island'},
            {'code': 'SC', 'name': 'South Carolina'},
            {'code': 'SD', 'name': 'South Dakota'},
            {'code': 'TN', 'name': 'Tennessee'},
            {'code': 'TX', 'name': 'Texas'},
            {'code': 'UT', 'name': 'Utah'},
            {'code': 'VT', 'name': 'Vermont'},
            {'code': 'VA', 'name': 'Virginia'},
            {'code': 'WA', 'name': 'Washington'},
            {'code': 'WV', 'name': 'West Virginia'},
            {'code': 'WI', 'name': 'Wisconsin'},
            {'code': 'WY', 'name': 'Wyoming'}
        ]
        return states
