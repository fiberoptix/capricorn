"""
Profile Service
Manages user profile data - single source of truth for all modules
"""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_profile import UserProfile
from app.core.constants import SINGLE_USER_ID
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profile (single-user system)"""
    
    @staticmethod
    async def get_profile(db: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        Get the user profile (id=1 always for single-user system)
        Auto-creates if doesn't exist
        """
        try:
            # Query for user_id = 1
            result = await db.execute(
                select(UserProfile).where(UserProfile.id == SINGLE_USER_ID)
            )
            profile = result.scalar_one_or_none()
            
            if not profile:
                logger.info("Profile not found, creating default profile")
                profile = await ProfileService._create_default_profile(db)
            
            return ProfileService._to_dict(profile)
            
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            raise
    
    @staticmethod
    async def update_profile(db: AsyncSession, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile with provided data
        Only updates fields that are provided
        """
        try:
            # Get existing profile
            result = await db.execute(
                select(UserProfile).where(UserProfile.id == SINGLE_USER_ID)
            )
            profile = result.scalar_one_or_none()
            
            if not profile:
                profile = await ProfileService._create_default_profile(db)
            
            # Update fields
            for key, value in data.items():
                if hasattr(profile, key) and key != 'id':  # Don't allow id changes
                    setattr(profile, key, value)
            
            await db.commit()
            await db.refresh(profile)
            
            logger.info(f"Profile updated with {len(data)} fields")
            return ProfileService._to_dict(profile)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating profile: {e}")
            raise
    
    @staticmethod
    async def update_section(
        db: AsyncSession, 
        section: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a specific section of the profile
        Sections: personal, income, expenses, 401k, investments, tax, retirement, savings
        """
        # Map section to field prefixes
        section_fields = {
            'personal': ['user', 'partner', 'user_age', 'partner_age', 'years_of_retirement', 
                        'user_years_to_retirement', 'partner_years_to_retirement'],
            'income': ['user_salary', 'user_bonus_rate', 'user_raise_rate', 
                      'partner_salary', 'partner_bonus_rate', 'partner_raise_rate'],
            'expenses': ['monthly_living_expenses', 'annual_discretionary_spending', 
                        'annual_inflation_rate'],
            '401k': ['user_401k_contribution', 'partner_401k_contribution', 
                    'user_employer_match', 'partner_employer_match',
                    'user_current_401k_balance', 'partner_current_401k_balance',
                    'user_401k_growth_rate', 'partner_401k_growth_rate'],
            'investments': ['current_ira_balance', 'ira_return_rate', 
                          'current_trading_balance', 'trading_return_rate',
                          'current_savings_balance', 'savings_return_rate',
                          'expected_inheritance', 'inheritance_year'],
            'tax': ['state', 'local_tax_rate', 'filing_status',
                   'calculated_federal_rate', 'calculated_state_rate', 'calculated_total_rate'],
            'retirement': ['retirement_growth_rate', 'withdrawal_rate'],
            'savings': ['fixed_monthly_savings', 'percentage_of_leftover', 'savings_destination']
        }
        
        # Filter data to only include fields for this section
        if section in section_fields:
            section_data = {
                k: v for k, v in data.items() 
                if k in section_fields[section]
            }
            return await ProfileService.update_profile(db, section_data)
        else:
            raise ValueError(f"Unknown section: {section}")
    
    @staticmethod
    async def _create_default_profile(db: AsyncSession) -> UserProfile:
        """Create default profile with id=1"""
        profile = UserProfile(id=SINGLE_USER_ID)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        logger.info("Created default profile")
        return profile
    
    @staticmethod
    def get_annual_household_income(profile: UserProfile) -> float:
        """
        Calculate annual household income for tax purposes
        Includes salaries + bonuses for both user and partner
        """
        user_salary = float(profile.user_salary) if profile.user_salary else 0.0
        user_bonus = user_salary * (float(profile.user_bonus_rate) if profile.user_bonus_rate else 0.0)
        
        partner_salary = float(profile.partner_salary) if profile.partner_salary else 0.0
        partner_bonus = partner_salary * (float(profile.partner_bonus_rate) if profile.partner_bonus_rate else 0.0)
        
        return user_salary + user_bonus + partner_salary + partner_bonus
    
    @staticmethod
    def _to_dict(profile: UserProfile) -> Dict[str, Any]:
        """Convert UserProfile model to dictionary"""
        # Helper to convert Decimal to float, handling None and 0 correctly
        def to_float(val):
            return float(val) if val is not None else None
        
        return {
            'id': profile.id,
            'email': profile.email,
            'first_name': profile.first_name,
            'last_name': profile.last_name,
            # Section 1: Personal
            'user': profile.user,
            'partner': profile.partner,
            'user_age': profile.user_age,
            'partner_age': profile.partner_age,
            'years_of_retirement': profile.years_of_retirement,
            'user_years_to_retirement': profile.user_years_to_retirement,
            'partner_years_to_retirement': profile.partner_years_to_retirement,
            # Section 2: Income
            'user_salary': to_float(profile.user_salary),
            'user_bonus_rate': to_float(profile.user_bonus_rate),
            'user_raise_rate': to_float(profile.user_raise_rate),
            'partner_salary': to_float(profile.partner_salary),
            'partner_bonus_rate': to_float(profile.partner_bonus_rate),
            'partner_raise_rate': to_float(profile.partner_raise_rate),
            # Section 3: Expenses
            'monthly_living_expenses': to_float(profile.monthly_living_expenses),
            'annual_discretionary_spending': to_float(profile.annual_discretionary_spending),
            'annual_inflation_rate': to_float(profile.annual_inflation_rate),
            # Section 4: 401K
            'user_401k_contribution': to_float(profile.user_401k_contribution),
            'partner_401k_contribution': to_float(profile.partner_401k_contribution),
            'user_employer_match': to_float(profile.user_employer_match),
            'partner_employer_match': to_float(profile.partner_employer_match),
            'user_current_401k_balance': to_float(profile.user_current_401k_balance),
            'partner_current_401k_balance': to_float(profile.partner_current_401k_balance),
            'user_401k_growth_rate': to_float(profile.user_401k_growth_rate),
            'partner_401k_growth_rate': to_float(profile.partner_401k_growth_rate),
            # Section 5: Investments
            'current_ira_balance': to_float(profile.current_ira_balance),
            'ira_return_rate': to_float(profile.ira_return_rate),
            'current_trading_balance': to_float(profile.current_trading_balance),
            'trading_return_rate': to_float(profile.trading_return_rate),
            'current_savings_balance': to_float(profile.current_savings_balance),
            'savings_return_rate': to_float(profile.savings_return_rate),
            'expected_inheritance': to_float(profile.expected_inheritance),
            'inheritance_year': profile.inheritance_year,
            # Section 6: Tax
            'state': profile.state,
            'local_tax_rate': to_float(profile.local_tax_rate),
            'filing_status': profile.filing_status,
            'calculated_federal_rate': to_float(profile.calculated_federal_rate),
            'calculated_state_rate': to_float(profile.calculated_state_rate),
            'calculated_total_rate': to_float(profile.calculated_total_rate),
            # Section 7: Retirement
            'retirement_growth_rate': to_float(profile.retirement_growth_rate),
            'withdrawal_rate': to_float(profile.withdrawal_rate),
            # Section 8: Savings Strategy
            'fixed_monthly_savings': to_float(profile.fixed_monthly_savings),
            'percentage_of_leftover': to_float(profile.percentage_of_leftover),
            'savings_destination': profile.savings_destination,
            # Metadata
            'created_at': profile.created_at.isoformat() if profile.created_at else None,
            'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
        }

