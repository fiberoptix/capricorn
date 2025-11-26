/**
 * Profile Types
 * Matches backend user_profile table and API response
 */

export interface Profile {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  
  // Section 1: Personal Information
  user: string;
  partner: string;
  user_age: number;
  partner_age: number;
  years_of_retirement: number;
  user_years_to_retirement: number;
  partner_years_to_retirement: number;
  
  // Section 2: Income Parameters
  user_salary: number;
  user_bonus_rate: number;
  user_raise_rate: number;
  partner_salary: number;
  partner_bonus_rate: number;
  partner_raise_rate: number;
  
  // Section 3: Expense Parameters
  monthly_living_expenses: number;
  annual_discretionary_spending: number;
  annual_inflation_rate: number;
  
  // Section 4: 401K Parameters
  user_401k_contribution: number;
  partner_401k_contribution: number;
  user_employer_match: number;
  partner_employer_match: number;
  user_current_401k_balance: number;
  partner_current_401k_balance: number;
  user_401k_growth_rate: number;
  partner_401k_growth_rate: number;
  
  // Section 5: Investment Accounts
  current_ira_balance: number;
  ira_return_rate: number;
  current_trading_balance: number;
  trading_return_rate: number;
  current_savings_balance: number;
  savings_return_rate: number;
  expected_inheritance: number;
  inheritance_year: number;
  
  // Section 6: Tax Parameters
  state: string;
  local_tax_rate: number;
  filing_status: string;
  calculated_federal_rate?: number;
  calculated_state_rate?: number;
  calculated_total_rate?: number;
  
  // Section 7: Retirement Parameters
  retirement_growth_rate: number;
  withdrawal_rate: number;
  
  // Section 8: Savings Strategy
  fixed_monthly_savings: number;
  percentage_of_leftover: number;
  savings_destination: string;
  
  // Metadata
  created_at: string;
  updated_at: string;
}

export interface ProfileUpdateRequest {
  // All fields optional for partial updates
  user?: string;
  partner?: string;
  user_age?: number;
  partner_age?: number;
  years_of_retirement?: number;
  user_years_to_retirement?: number;
  partner_years_to_retirement?: number;
  user_salary?: number;
  user_bonus_rate?: number;
  user_raise_rate?: number;
  partner_salary?: number;
  partner_bonus_rate?: number;
  partner_raise_rate?: number;
  monthly_living_expenses?: number;
  annual_discretionary_spending?: number;
  annual_inflation_rate?: number;
  user_401k_contribution?: number;
  partner_401k_contribution?: number;
  user_employer_match?: number;
  partner_employer_match?: number;
  user_current_401k_balance?: number;
  partner_current_401k_balance?: number;
  user_401k_growth_rate?: number;
  partner_401k_growth_rate?: number;
  current_ira_balance?: number;
  ira_return_rate?: number;
  current_trading_balance?: number;
  trading_return_rate?: number;
  current_savings_balance?: number;
  savings_return_rate?: number;
  expected_inheritance?: number;
  inheritance_year?: number;
  state?: string;
  local_tax_rate?: number;
  filing_status?: string;
  retirement_growth_rate?: number;
  withdrawal_rate?: number;
  fixed_monthly_savings?: number;
  percentage_of_leftover?: number;
  savings_destination?: string;
}

export type ProfileSection = 
  | 'personal' 
  | 'income' 
  | 'expenses' 
  | '401k' 
  | 'investments' 
  | 'tax' 
  | 'retirement' 
  | 'savings';

