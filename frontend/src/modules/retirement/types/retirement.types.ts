/**
 * Retirement Types
 * Matches backend RetirementCalculator response structures
 */

export interface RetirementSummary {
  yearly_projections: YearlyProjection[];
  asset_growth: AssetGrowth[];
  retirement_analysis: RetirementAnalysis;
  transition_analysis: TransitionAnalysis;
  summary: {
    total_years: number;
    user_retirement_year: number;
    partner_retirement_year: number;
    final_assets: number;
  };
}

export interface YearlyProjection {
  year: number;
  user_salary: number;
  user_bonus: number;
  partner_salary: number;
  partner_bonus: number;
  gross_income: number;
  taxable_income: number;
  federal_tax_rate: number;
  state_tax_rate: number;
  local_tax_rate: number;
  total_effective_rate: number;
  total_taxes: number;
  take_home_pay: number;
  essential_expenses: number;
  discretionary_expenses: number;
  total_expenses: number;
  leftover_money: number;
  monthly_leftover: number;
  monthly_savings: number;
  annual_savings: number;
  total_withdrawals: number;
}

export interface AssetGrowth {
  year: number;
  userAccount401k: number;
  partnerAccount401k: number;
  accountIRA: number;
  accountSavings: number;
  accountTrading: number;
  inheritance: number;
  totalAssets: number;
  annualGrowth: number;
  cumulativeSavings: number;
  uninvestedSurplus: number;
}

export interface RetirementAnalysis {
  finalAssetValues: {
    userAccount401k: number;
    partnerAccount401k: number;
    accountIRA: number;
    accountTrading: number;
    inheritance: number;
    totalAssets: number;
  };
  withdrawalAnalysis: {
    monthlyGrossWithdrawal: number;
    monthlyTax: number;
    monthlyNetWithdrawal: number;
  };
  lifestyleAnalysis: {
    targetMonthlyNeed: number;
    monthlySurplus: number;
    lifestyleMultiple: number;
  };
  statusIndicators: {
    retirementGoal: string;
    savingsTarget: string;
    assetGrowth: string;
  };
}

export interface TransitionAnalysis {
  transitionPeriod: {
    duration: number;
    startYear: number;
    endYear: number;
    userRetirementYear: number;
    partnerRetirementYear: number;
    message?: string;
  };
  incomeAnalysis: {
    partnerSalaryStart: number;
    partnerSalaryMid: number;
    partnerSalaryEnd: number;
  };
  expenseCoverage: {
    expensesStart: number;
    expensesMid: number;
    expensesEnd: number;
  };
}

