"""
InvestorProfile Service for Portfolio Manager Application

Handles all CRUD operations for investor profile management including:
- Tax settings and personal information
- Filing status and income tracking
- State and local tax configuration
- Profile validation and updates
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from datetime import datetime
from decimal import Decimal

from app.models.portfolio_models import InvestorProfile


class InvestorProfileService:
    """Service class for investor profile operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_profile(
        self,
        name: str,
        household_income: Decimal,
        filing_status: str,
        state_of_residence: str,
        local_tax_rate: Decimal = Decimal('0.0')
    ) -> InvestorProfile:
        """
        Create a new investor profile
        
        Args:
            name: Full name of the investor
            household_income: Annual household income
            filing_status: 'single' or 'married_filing_jointly'
            state_of_residence: Two-letter state code (e.g., 'NY', 'CA')
            local_tax_rate: Local tax rate as decimal (e.g., 0.01 for 1%)
            
        Returns:
            Created InvestorProfile object
        """
        # Validate filing status
        valid_filing_statuses = ['single', 'married_filing_jointly', 'married_filing_separately', 'head_of_household']
        if filing_status.lower() not in valid_filing_statuses:
            raise ValueError(f"Filing status must be one of: {', '.join(valid_filing_statuses)}")
        
        # Validate state code (basic check - should be 2 letters)
        if len(state_of_residence) != 2 or not state_of_residence.isalpha():
            raise ValueError("State of residence must be a 2-letter state code (e.g., 'NY', 'CA')")
        
        # Validate income is positive
        if household_income <= 0:
            raise ValueError("Household income must be positive")
        
        # Validate local tax rate is reasonable (0-20%)
        if local_tax_rate < 0 or local_tax_rate > Decimal('0.20'):
            raise ValueError("Local tax rate must be between 0% and 20%")
        
        profile = InvestorProfile(
            name=name,
            annual_household_income=household_income,
            filing_status=filing_status.lower(),
            state_of_residence=state_of_residence.upper(),
            local_tax_rate=local_tax_rate,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    def get_profile(self, profile_id: int) -> Optional[InvestorProfile]:
        """
        Get investor profile by ID
        
        Args:
            profile_id: Profile ID
            
        Returns:
            InvestorProfile object or None if not found
        """
        return self.db.query(InvestorProfile).filter(InvestorProfile.id == profile_id).first()
    
    def get_profile_by_name(self, name: str) -> Optional[InvestorProfile]:
        """
        Get investor profile by name
        
        Args:
            name: Investor name
            
        Returns:
            InvestorProfile object or None if not found
        """
        return self.db.query(InvestorProfile).filter(InvestorProfile.name.ilike(f"%{name}%")).first()
    
    def get_all_profiles(self, order_by: str = 'name') -> List[InvestorProfile]:
        """
        Get all investor profiles
        
        Args:
            order_by: 'name', 'income', 'created' 
            
        Returns:
            List of InvestorProfile objects
        """
        query = self.db.query(InvestorProfile)
        
        if order_by == 'name':
            query = query.order_by(asc(InvestorProfile.name))
        elif order_by == 'income':
            query = query.order_by(desc(InvestorProfile.household_income))
        elif order_by == 'created':
            query = query.order_by(desc(InvestorProfile.created_at))
        
        return query.all()
    
    def update_profile(
        self,
        profile_id: int,
        name: str = None,
        household_income: Decimal = None,
        filing_status: str = None,
        state_of_residence: str = None,
        local_tax_rate: Decimal = None
    ) -> Optional[InvestorProfile]:
        """
        Update investor profile
        
        Args:
            profile_id: Profile ID to update
            name: Updated name (optional)
            household_income: Updated income (optional)
            filing_status: Updated filing status (optional)
            state_of_residence: Updated state (optional)
            local_tax_rate: Updated local tax rate (optional)
            
        Returns:
            Updated InvestorProfile object or None if not found
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        # Update fields if provided
        if name is not None:
            profile.name = name
            
        if household_income is not None:
            if household_income <= 0:
                raise ValueError("Household income must be positive")
            profile.annual_household_income = household_income
            
        if filing_status is not None:
            valid_filing_statuses = ['single', 'married_filing_jointly', 'married_filing_separately', 'head_of_household']
            if filing_status.lower() not in valid_filing_statuses:
                raise ValueError(f"Filing status must be one of: {', '.join(valid_filing_statuses)}")
            profile.filing_status = filing_status.lower()
            
        if state_of_residence is not None:
            if len(state_of_residence) != 2 or not state_of_residence.isalpha():
                raise ValueError("State of residence must be a 2-letter state code")
            profile.state_of_residence = state_of_residence.upper()
            
        if local_tax_rate is not None:
            if local_tax_rate < 0 or local_tax_rate > Decimal('0.20'):
                raise ValueError("Local tax rate must be between 0% and 20%")
            profile.local_tax_rate = local_tax_rate
        
        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    def delete_profile(self, profile_id: int) -> bool:
        """
        Delete investor profile
        
        Args:
            profile_id: Profile ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        profile = self.get_profile(profile_id)
        if profile:
            self.db.delete(profile)
            self.db.commit()
            return True
        return False
    
    def get_profiles_by_state(self, state_code: str) -> List[InvestorProfile]:
        """
        Get all investor profiles in a specific state
        
        Args:
            state_code: Two-letter state code
            
        Returns:
            List of InvestorProfile objects in that state
        """
        return self.db.query(InvestorProfile).filter(
            InvestorProfile.state_of_residence == state_code.upper()
        ).order_by(asc(InvestorProfile.name)).all()
    
    def get_tax_settings(self, profile_id: int) -> Optional[dict]:
        """
        Get tax settings for a specific profile
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Dictionary with tax settings or None if profile not found
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        return {
            'profile_id': profile.id,
            'name': profile.name,
            'household_income': float(profile.annual_household_income),
            'filing_status': profile.filing_status,
            'state_of_residence': profile.state_of_residence,
            'local_tax_rate': float(profile.local_tax_rate),
            'tax_year': datetime.now().year,  # Current tax year
            'created_at': profile.created_at.isoformat(),
            'updated_at': profile.updated_at.isoformat()
        }
    
    def calculate_tax_brackets(self, profile_id: int) -> Optional[dict]:
        """
        Calculate which tax brackets apply to this investor profile
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Dictionary with applicable tax bracket information
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        # 2025 Federal Tax Brackets (these should eventually come from a tax rates table)
        if profile.filing_status == 'single':
            brackets = [
                {'rate': 0.10, 'min': 0, 'max': 11000},
                {'rate': 0.12, 'min': 11000, 'max': 44725},
                {'rate': 0.22, 'min': 44725, 'max': 95375},
                {'rate': 0.24, 'min': 95375, 'max': 182050},
                {'rate': 0.32, 'min': 182050, 'max': 231250},
                {'rate': 0.35, 'min': 231250, 'max': 578125},
                {'rate': 0.37, 'min': 578125, 'max': float('inf')}
            ]
        elif profile.filing_status == 'married_joint':
            brackets = [
                {'rate': 0.10, 'min': 0, 'max': 22000},
                {'rate': 0.12, 'min': 22000, 'max': 89450},
                {'rate': 0.22, 'min': 89450, 'max': 190750},
                {'rate': 0.24, 'min': 190750, 'max': 364200},
                {'rate': 0.32, 'min': 364200, 'max': 462500},
                {'rate': 0.35, 'min': 462500, 'max': 693750},
                {'rate': 0.37, 'min': 693750, 'max': float('inf')}
            ]
        else:
            # Default to single brackets for other filing statuses
            brackets = [
                {'rate': 0.10, 'min': 0, 'max': 11000},
                {'rate': 0.12, 'min': 11000, 'max': 44725},
                {'rate': 0.22, 'min': 44725, 'max': 95375},
                {'rate': 0.24, 'min': 95375, 'max': 182050},
                {'rate': 0.32, 'min': 182050, 'max': 231250},
                {'rate': 0.35, 'min': 231250, 'max': 578125},
                {'rate': 0.37, 'min': 578125, 'max': float('inf')}
            ]
        
        # Find applicable brackets for this income level
        income = float(profile.annual_household_income)
        applicable_brackets = []
        
        for bracket in brackets:
            if income > bracket['min']:
                applicable_brackets.append({
                    'rate': bracket['rate'],
                    'rate_percent': bracket['rate'] * 100,
                    'min_income': bracket['min'],
                    'max_income': bracket['max'] if bracket['max'] != float('inf') else 'unlimited',
                    'applies_to_income': income >= bracket['min']
                })
        
        # Determine marginal tax rate (highest applicable bracket)
        marginal_rate = applicable_brackets[-1]['rate'] if applicable_brackets else 0.10
        
        # NIIT (Net Investment Income Tax) applies to high earners
        niit_threshold = 200000 if profile.filing_status == 'single' else 250000
        niit_applies = income > niit_threshold
        
        return {
            'profile_id': profile.id,
            'household_income': income,
            'filing_status': profile.filing_status,
            'marginal_tax_rate': marginal_rate,
            'marginal_tax_rate_percent': marginal_rate * 100,
            'applicable_brackets': applicable_brackets,
            'niit_applies': niit_applies,
            'niit_rate': 0.038 if niit_applies else 0.0,
            'local_tax_rate': float(profile.local_tax_rate),
            'state_of_residence': profile.state_of_residence,
            'tax_brackets': brackets  # Add full bracket structure for progressive calculations
        }

    def calculate_progressive_tax(
        self, 
        profile_id: int, 
        additional_income: float, 
        is_capital_gains: bool = False,
        is_long_term: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate progressive tax on additional income (like capital gains)
        
        Args:
            profile_id: Investor profile ID
            additional_income: Additional income to tax (e.g., capital gains)
            is_capital_gains: Whether this is capital gains income
            is_long_term: Whether this is long-term capital gains (>1 year)
            
        Returns:
            Dictionary with progressive tax calculation details
        """
        profile = self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
            
        base_income = float(profile.annual_household_income)
        
        if is_capital_gains and is_long_term:
            # Long-term capital gains use separate bracket structure
            return self._calculate_long_term_capital_gains_tax(profile, additional_income)
        else:
            # Short-term capital gains and ordinary income use regular brackets
            return self._calculate_ordinary_income_progressive_tax(profile, base_income, additional_income)
    
    def _calculate_long_term_capital_gains_tax(self, profile, capital_gains: float) -> Dict[str, Any]:
        """Calculate long-term capital gains tax using special LTCG brackets"""
        
        # 2025 Long-term capital gains brackets
        if profile.filing_status == 'married_joint':
            ltcg_brackets = [
                {'rate': 0.00, 'min': 0, 'max': 96700},        # 0% rate
                {'rate': 0.15, 'min': 96700, 'max': 600050},   # 15% rate  
                {'rate': 0.20, 'min': 600050, 'max': float('inf')}  # 20% rate
            ]
        else:  # single
            ltcg_brackets = [
                {'rate': 0.00, 'min': 0, 'max': 48350},        # 0% rate
                {'rate': 0.15, 'min': 48350, 'max': 533400},   # 15% rate
                {'rate': 0.20, 'min': 533400, 'max': float('inf')}  # 20% rate
            ]
        
        base_income = float(profile.annual_household_income)
        total_income = base_income + capital_gains
        
        # Find which bracket applies based on total income
        applicable_rate = 0.0
        for bracket in ltcg_brackets:
            if base_income < bracket['max']:
                applicable_rate = bracket['rate']
                break
        
        federal_tax = capital_gains * applicable_rate
        
        # NIIT (3.8%) applies to high earners
        niit_threshold = 250000 if profile.filing_status == 'married_joint' else 200000
        niit_tax = 0.0
        if base_income > niit_threshold:
            niit_tax = capital_gains * 0.038
        
        total_federal_tax = federal_tax + niit_tax
        
        return {
            'capital_gains_amount': capital_gains,
            'base_income': base_income,
            'ltcg_rate': applicable_rate,
            'ltcg_rate_percent': applicable_rate * 100,
            'federal_ltcg_tax': federal_tax,
            'niit_tax': niit_tax,
            'total_federal_tax': total_federal_tax,
            'effective_rate': (total_federal_tax / capital_gains) if capital_gains > 0 else 0.0,
            'calculation_method': 'long_term_capital_gains'
        }
    
    def _calculate_ordinary_income_progressive_tax(
        self, 
        profile, 
        base_income: float, 
        additional_income: float
    ) -> Dict[str, Any]:
        """Calculate progressive tax on additional ordinary income (short-term gains)"""
        
        # Get tax brackets
        brackets_info = self.calculate_tax_brackets(profile.id)
        brackets = brackets_info['tax_brackets']
        
        # Calculate tax on base income + additional income
        total_income = base_income + additional_income
        
        # Progressive calculation across brackets
        total_tax = 0.0
        tax_breakdown = []
        
        for bracket in brackets:
            bracket_min = bracket['min']
            bracket_max = bracket['max'] if bracket['max'] != float('inf') else total_income
            bracket_rate = bracket['rate']
            
            if total_income > bracket_min:
                # Income in this bracket
                taxable_in_bracket = min(total_income, bracket_max) - bracket_min
                if taxable_in_bracket > 0:
                    tax_in_bracket = taxable_in_bracket * bracket_rate
                    total_tax += tax_in_bracket
                    
                    tax_breakdown.append({
                        'bracket_rate': bracket_rate,
                        'bracket_rate_percent': bracket_rate * 100,
                        'taxable_amount': taxable_in_bracket,
                        'tax_amount': tax_in_bracket
                    })
        
        # Calculate tax on base income only for comparison
        base_tax = 0.0
        for bracket in brackets:
            bracket_min = bracket['min']
            bracket_max = bracket['max'] if bracket['max'] != float('inf') else base_income
            bracket_rate = bracket['rate']
            
            if base_income > bracket_min:
                taxable_in_bracket = min(base_income, bracket_max) - bracket_min
                if taxable_in_bracket > 0:
                    base_tax += taxable_in_bracket * bracket_rate
        
        # Tax attributable to additional income
        additional_income_tax = total_tax - base_tax
        
        # NIIT calculation
        niit_threshold = 250000 if profile.filing_status == 'married_joint' else 200000
        niit_tax = 0.0
        if total_income > niit_threshold:
            niit_tax = additional_income * 0.038
        
        total_federal_tax = additional_income_tax + niit_tax
        
        return {
            'additional_income': additional_income,
            'base_income': base_income,
            'total_income': total_income,
            'progressive_tax_breakdown': tax_breakdown,
            'additional_income_tax': additional_income_tax,
            'niit_tax': niit_tax,
            'total_federal_tax': total_federal_tax,
            'effective_rate': (total_federal_tax / additional_income) if additional_income > 0 else 0.0,
            'calculation_method': 'progressive_ordinary_income'
        }


def get_investor_profile_service(db: Session) -> InvestorProfileService:
    """Dependency injection helper for Flask"""
    return InvestorProfileService(db)