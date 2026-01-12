from django.urls import path
from .views.index import FinanceIndexView
from .views.mortgage_calculator import MortgageCalculator
from .views.loan_calculator import LoanCalculator
from .views.auto_loan_calculator import AutoLoanCalculator
from .views.interest_calculator import InterestCalculator
from .views.payment_calculator import PaymentCalculator
from .views.retirement_calculator import RetirementCalculator
from .views.amortization_calculator import AmortizationCalculator
from .views.investment_calculator import InvestmentCalculator
from .views.currency_calculator import CurrencyCalculator
from .views.inflation_calculator import InflationCalculator
from .views.finance_calculator import FinanceCalculator
from .views.mortgage_payoff_calculator import MortgagePayoffCalculator
from .views.income_tax_calculator import IncomeTaxCalculator
from .views.compound_interest_calculator import CompoundInterestCalculator
from .views.salary_calculator import SalaryCalculator
from .views.k401_calculator import K401Calculator
from .views.interest_rate_calculator import InterestRateCalculator
from .views.sales_tax_calculator import SalesTaxCalculator
from .views.house_affordability_calculator import HouseAffordabilityCalculator
from .views.savings_calculator import SavingsCalculator
from .views.rent_calculator import RentCalculator
from .views.marriage_tax_calculator import MarriageTaxCalculator
from .views.estate_tax_calculator import EstateTaxCalculator
from .views.pension_calculator import PensionCalculator
from .views.social_security_calculator import SocialSecurityCalculator
from .views.annuity_calculator import AnnuityCalculator
from .views.annuity_payout_calculator import AnnuityPayoutCalculator
from .views.credit_card_calculator import CreditCardCalculator
from .views.credit_cards_payoff_calculator import CreditCardsPayoffCalculator
from .views.debt_payoff_calculator import DebtPayoffCalculator
from .views.debt_consolidation_calculator import DebtConsolidationCalculator
from .views.repayment_calculator import RepaymentCalculator
from .views.student_loan_calculator import StudentLoanCalculator
from .views.college_cost_calculator import CollegeCostCalculator
from .views.cd_calculator import CdCalculator
from .views.bond_calculator import BondCalculator
from .views.roth_ira_calculator import RothIraCalculator
from .views.ira_calculator import IraCalculator
from .views.rmd_calculator import RmdCalculator
from .views.vat_calculator import VatCalculator
from .views.cash_back_calculator import CashBackCalculator
from .views.auto_lease_calculator import AutoLeaseCalculator
from .views.depreciation_calculator import DepreciationCalculator
from .views.average_return_calculator import AverageReturnCalculator
from .views.margin_calculator import MarginCalculator
from .views.discount_calculator import DiscountCalculator
from .views.business_loan_calculator import BusinessLoanCalculator
from .views.debt_to_income_calculator import DebtToIncomeCalculator
from .views.real_estate_calculator import RealEstateCalculator
from .views.take_home_paycheck_calculator import TakeHomePaycheckCalculator
from .views.personal_loan_calculator import PersonalLoanCalculator
from .views.boat_loan_calculator import BoatLoanCalculator
from .views.lease_calculator import LeaseCalculator
from .views.refinance_calculator import RefinanceCalculator
from .views.budget_calculator import BudgetCalculator
from .views.rental_property_calculator import RentalPropertyCalculator
from .views.irr_calculator import IrrCalculator
from .views.apr_calculator import AprCalculator
from .views.fha_loan_calculator import FhaLoanCalculator
from .views.va_mortgage_calculator import VaMortgageCalculator
from .views.down_payment_calculator import DownPaymentCalculator
from .views.rent_vs_buy_calculator import RentVsBuyCalculator
from .views.payback_period_calculator import PaybackPeriodCalculator
from .views.present_value_calculator import PresentValueCalculator
from .views.future_value_calculator import FutureValueCalculator
from .views.commission_calculator import CommissionCalculator
from .views.mortgage_calculator_uk import MortgageCalculatorUk
from .views.canadian_mortgage_calculator import CanadianMortgageCalculator
from .views.mortgage_amortization_calculator import MortgageAmortizationCalculator
from .views.percent_off_calculator import PercentOffCalculator

urlpatterns = [
    path('', FinanceIndexView.as_view(), name='index'),
    path('mortgage-calculator/', MortgageCalculator.as_view(), name='mortgage_calculator'),
    path('loan-calculator/', LoanCalculator.as_view(), name='loan_calculator'),
    path('auto-loan-calculator/', AutoLoanCalculator.as_view(), name='auto_loan_calculator'),
    path('interest-calculator/', InterestCalculator.as_view(), name='interest_calculator'),
    path('payment-calculator/', PaymentCalculator.as_view(), name='payment_calculator'),
    path('retirement-calculator/', RetirementCalculator.as_view(), name='retirement_calculator'),
    path('amortization-calculator/', AmortizationCalculator.as_view(), name='amortization_calculator'),
    path('investment-calculator/', InvestmentCalculator.as_view(), name='investment_calculator'),
    path('currency-calculator/', CurrencyCalculator.as_view(), name='currency_calculator'),
    path('inflation-calculator/', InflationCalculator.as_view(), name='inflation_calculator'),
    path('finance-calculator/', FinanceCalculator.as_view(), name='finance_calculator'),
    path('mortgage-payoff-calculator/', MortgagePayoffCalculator.as_view(), name='mortgage_payoff_calculator'),
    path('income-tax-calculator/', IncomeTaxCalculator.as_view(), name='income_tax_calculator'),
    path('compound-interest-calculator/', CompoundInterestCalculator.as_view(), name='compound_interest_calculator'),
    path('salary-calculator/', SalaryCalculator.as_view(), name='salary_calculator'),
    path('401k-calculator/', K401Calculator.as_view(), name='401k_calculator'),
    path('interest-rate-calculator/', InterestRateCalculator.as_view(), name='interest_rate_calculator'),
    path('sales-tax-calculator/', SalesTaxCalculator.as_view(), name='sales_tax_calculator'),
    path('house-affordability-calculator/', HouseAffordabilityCalculator.as_view(), name='house_affordability_calculator'),
    path('savings-calculator/', SavingsCalculator.as_view(), name='savings_calculator'),
    path('rent-calculator/', RentCalculator.as_view(), name='rent_calculator'),
    path('marriage-tax-calculator/', MarriageTaxCalculator.as_view(), name='marriage_tax_calculator'),
    path('estate-tax-calculator/', EstateTaxCalculator.as_view(), name='estate_tax_calculator'),
    path('pension-calculator/', PensionCalculator.as_view(), name='pension_calculator'),
    path('social-security-calculator/', SocialSecurityCalculator.as_view(), name='social_security_calculator'),
    path('annuity-calculator/', AnnuityCalculator.as_view(), name='annuity_calculator'),
    path('annuity-payout-calculator/', AnnuityPayoutCalculator.as_view(), name='annuity_payout_calculator'),
    path('credit-card-calculator/', CreditCardCalculator.as_view(), name='credit_card_calculator'),
    path('credit-cards-payoff-calculator/', CreditCardsPayoffCalculator.as_view(), name='credit_cards_payoff_calculator'),
    path('debt-payoff-calculator/', DebtPayoffCalculator.as_view(), name='debt_payoff_calculator'),
    path('debt-consolidation-calculator/', DebtConsolidationCalculator.as_view(), name='debt_consolidation_calculator'),
    path('repayment-calculator/', RepaymentCalculator.as_view(), name='repayment_calculator'),
    path('student-loan-calculator/', StudentLoanCalculator.as_view(), name='student_loan_calculator'),
    path('college-cost-calculator/', CollegeCostCalculator.as_view(), name='college_cost_calculator'),
    path('cd-calculator/', CdCalculator.as_view(), name='cd_calculator'),
    path('bond-calculator/', BondCalculator.as_view(), name='bond_calculator'),
    path('roth-ira-calculator/', RothIraCalculator.as_view(), name='roth_ira_calculator'),
    path('ira-calculator/', IraCalculator.as_view(), name='ira_calculator'),
    path('rmd-calculator/', RmdCalculator.as_view(), name='rmd_calculator'),
    path('vat-calculator/', VatCalculator.as_view(), name='vat_calculator'),
    path('cash-back-calculator/', CashBackCalculator.as_view(), name='cash_back_calculator'),
    path('auto-lease-calculator/', AutoLeaseCalculator.as_view(), name='auto_lease_calculator'),
    path('depreciation-calculator/', DepreciationCalculator.as_view(), name='depreciation_calculator'),
    path('average-return-calculator/', AverageReturnCalculator.as_view(), name='average_return_calculator'),
    path('margin-calculator/', MarginCalculator.as_view(), name='margin_calculator'),
    path('discount-calculator/', DiscountCalculator.as_view(), name='discount_calculator'),
    path('business-loan-calculator/', BusinessLoanCalculator.as_view(), name='business_loan_calculator'),
    path('debt-to-income-calculator/', DebtToIncomeCalculator.as_view(), name='debt_to_income_calculator'),
    path('real-estate-calculator/', RealEstateCalculator.as_view(), name='real_estate_calculator'),
    path('take-home-paycheck-calculator/', TakeHomePaycheckCalculator.as_view(), name='take_home_paycheck_calculator'),
    path('personal-loan-calculator/', PersonalLoanCalculator.as_view(), name='personal_loan_calculator'),
    path('boat-loan-calculator/', BoatLoanCalculator.as_view(), name='boat_loan_calculator'),
    path('lease-calculator/', LeaseCalculator.as_view(), name='lease_calculator'),
    path('refinance-calculator/', RefinanceCalculator.as_view(), name='refinance_calculator'),
    path('budget-calculator/', BudgetCalculator.as_view(), name='budget_calculator'),
    path('rental-property-calculator/', RentalPropertyCalculator.as_view(), name='rental_property_calculator'),
    path('irr-calculator/', IrrCalculator.as_view(), name='irr_calculator'),
    path('apr-calculator/', AprCalculator.as_view(), name='apr_calculator'),
    path('fha-loan-calculator/', FhaLoanCalculator.as_view(), name='fha_loan_calculator'),
    path('va-mortgage-calculator/', VaMortgageCalculator.as_view(), name='va_mortgage_calculator'),
    path('down-payment-calculator/', DownPaymentCalculator.as_view(), name='down_payment_calculator'),
    path('rent-vs-buy-calculator/', RentVsBuyCalculator.as_view(), name='rent_vs_buy_calculator'),
    path('payback-period-calculator/', PaybackPeriodCalculator.as_view(), name='payback_period_calculator'),
    path('present-value-calculator/', PresentValueCalculator.as_view(), name='present_value_calculator'),
    path('future-value-calculator/', FutureValueCalculator.as_view(), name='future_value_calculator'),
    path('commission-calculator/', CommissionCalculator.as_view(), name='commission_calculator'),
    path('mortgage-calculator-uk/', MortgageCalculatorUk.as_view(), name='mortgage_calculator_uk'),
    path('canadian-mortgage-calculator/', CanadianMortgageCalculator.as_view(), name='canadian_mortgage_calculator'),
    path('mortgage-amortization-calculator/', MortgageAmortizationCalculator.as_view(), name='mortgage_amortization_calculator'),
    path('percent-off-calculator/', PercentOffCalculator.as_view(), name='percent_off_calculator'),
]

app_name = 'financial_calculators'
