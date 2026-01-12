from django.shortcuts import render
from django.views.generic import TemplateView


class FinanceIndexView(TemplateView):
    template_name = 'financial_calculators/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Comprehensive financial calculators list organized by categories
        calculators = [
            # Mortgage & Home
            {'name': 'Mortgage Calculator', 'url': 'mortgage-calculator', 'category': 'Mortgage & Home', 'description': 'Calculate monthly mortgage payments and total interest'},
            {'name': 'Mortgage Amortization Calculator', 'url': 'mortgage-amortization-calculator', 'category': 'Mortgage & Home', 'description': 'View detailed amortization schedule for mortgages'},
            {'name': 'Mortgage Payoff Calculator', 'url': 'mortgage-payoff-calculator', 'category': 'Mortgage & Home', 'description': 'Calculate how quickly you can pay off your mortgage'},
            {'name': 'Mortgage Calculator UK', 'url': 'mortgage-calculator-uk', 'category': 'Mortgage & Home', 'description': 'UK mortgage calculator with local tax rates'},
            {'name': 'Canadian Mortgage Calculator', 'url': 'canadian-mortgage-calculator', 'category': 'Mortgage & Home', 'description': 'Canadian mortgage calculations and amortization'},
            {'name': 'FHA Loan Calculator', 'url': 'fha-loan-calculator', 'category': 'Mortgage & Home', 'description': 'Calculate FHA loan costs and monthly payments'},
            {'name': 'VA Mortgage Calculator', 'url': 'va-mortgage-calculator', 'category': 'Mortgage & Home', 'description': 'VA mortgage calculator for military personnel'},
            {'name': 'House Affordability Calculator', 'url': 'house-affordability-calculator', 'category': 'Mortgage & Home', 'description': 'Determine how much house you can afford'},
            {'name': 'Down Payment Calculator', 'url': 'down-payment-calculator', 'category': 'Mortgage & Home', 'description': 'Calculate required down payment amounts'},
            {'name': 'Rent vs Buy Calculator', 'url': 'rent-vs-buy-calculator', 'category': 'Mortgage & Home', 'description': 'Compare renting vs buying costs'},
            {'name': 'Real Estate Calculator', 'url': 'real-estate-calculator', 'category': 'Mortgage & Home', 'description': 'General real estate financial calculations'},
            {'name': 'Rental Property Calculator', 'url': 'rental-property-calculator', 'category': 'Mortgage & Home', 'description': 'Analyze rental property investment returns'},
            
            # Loans & Debt
            {'name': 'Loan Calculator', 'url': 'loan-calculator', 'category': 'Loans & Debt', 'description': 'Calculate loan payments and total interest'},
            {'name': 'Auto Loan Calculator', 'url': 'auto-loan-calculator', 'category': 'Loans & Debt', 'description': 'Calculate auto loan payments and costs'},
            {'name': 'Personal Loan Calculator', 'url': 'personal-loan-calculator', 'category': 'Loans & Debt', 'description': 'Calculate personal loan payments'},
            {'name': 'Business Loan Calculator', 'url': 'business-loan-calculator', 'category': 'Loans & Debt', 'description': 'Calculate business loan terms and payments'},
            {'name': 'Student Loan Calculator', 'url': 'student-loan-calculator', 'category': 'Loans & Debt', 'description': 'Calculate student loan repayment plans'},
            {'name': 'Boat Loan Calculator', 'url': 'boat-loan-calculator', 'category': 'Loans & Debt', 'description': 'Calculate boat financing payments'},
            {'name': 'Debt Payoff Calculator', 'url': 'debt-payoff-calculator', 'category': 'Loans & Debt', 'description': 'Calculate how long to pay off debt'},
            {'name': 'Debt Consolidation Calculator', 'url': 'debt-consolidation-calculator', 'category': 'Loans & Debt', 'description': 'Compare debt consolidation options'},
            {'name': 'Credit Card Calculator', 'url': 'credit-card-calculator', 'category': 'Loans & Debt', 'description': 'Calculate credit card payment schedules'},
            {'name': 'Credit Cards Payoff Calculator', 'url': 'credit-cards-payoff-calculator', 'category': 'Loans & Debt', 'description': 'Calculate payoff for multiple credit cards'},
            {'name': 'Debt to Income Calculator', 'url': 'debt-to-income-calculator', 'category': 'Loans & Debt', 'description': 'Calculate your debt-to-income ratio'},
            
            # Interest & Investment
            {'name': 'Compound Interest Calculator', 'url': 'compound-interest-calculator', 'category': 'Interest & Investment', 'description': 'Calculate compound interest earnings'},
            {'name': 'Simple Interest Calculator', 'url': 'interest-calculator', 'category': 'Interest & Investment', 'description': 'Calculate simple interest on loans/savings'},
            {'name': 'Interest Rate Calculator', 'url': 'interest-rate-calculator', 'category': 'Interest & Investment', 'description': 'Calculate interest rates from other values'},
            {'name': 'Investment Calculator', 'url': 'investment-calculator', 'category': 'Interest & Investment', 'description': 'Calculate investment growth over time'},
            {'name': 'Future Value Calculator', 'url': 'future-value-calculator', 'category': 'Interest & Investment', 'description': 'Calculate future value of investments'},
            {'name': 'Present Value Calculator', 'url': 'present-value-calculator', 'category': 'Interest & Investment', 'description': 'Calculate present value of future cash flows'},
            {'name': 'Average Return Calculator', 'url': 'average-return-calculator', 'category': 'Interest & Investment', 'description': 'Calculate average investment returns'},
            {'name': 'IRR Calculator', 'url': 'irr-calculator', 'category': 'Interest & Investment', 'description': 'Calculate internal rate of return'},
            
            # Retirement & Savings
            {'name': 'Retirement Calculator', 'url': 'retirement-calculator', 'category': 'Retirement & Savings', 'description': 'Plan for retirement savings goals'},
            {'name': '401K Calculator', 'url': '401k-calculator', 'category': 'Retirement & Savings', 'description': 'Calculate 401K retirement contributions'},
            {'name': 'IRA Calculator', 'url': 'ira-calculator', 'category': 'Retirement & Savings', 'description': 'Calculate IRA savings and growth'},
            {'name': 'Roth IRA Calculator', 'url': 'roth-ira-calculator', 'category': 'Retirement & Savings', 'description': 'Calculate Roth IRA contributions and growth'},
            {'name': 'RMD Calculator', 'url': 'rmd-calculator', 'category': 'Retirement & Savings', 'description': 'Calculate required minimum distributions'},
            {'name': 'Pension Calculator', 'url': 'pension-calculator', 'category': 'Retirement & Savings', 'description': 'Calculate pension benefits'},
            {'name': 'Social Security Calculator', 'url': 'social-security-calculator', 'category': 'Retirement & Savings', 'description': 'Estimate social security benefits'},
            {'name': 'Savings Calculator', 'url': 'savings-calculator', 'category': 'Retirement & Savings', 'description': 'Track savings growth over time'},
            
            # Investments & Income
            {'name': 'Annuity Calculator', 'url': 'annuity-calculator', 'category': 'Investments & Income', 'description': 'Calculate annuity payments and values'},
            {'name': 'Annuity Payout Calculator', 'url': 'annuity-payout-calculator', 'category': 'Investments & Income', 'description': 'Calculate annuity payout amounts'},
            {'name': 'Bond Calculator', 'url': 'bond-calculator', 'category': 'Investments & Income', 'description': 'Calculate bond values and yields'},
            {'name': 'CD Calculator', 'url': 'cd-calculator', 'category': 'Investments & Income', 'description': 'Calculate certificate of deposit returns'},
            {'name': 'Commission Calculator', 'url': 'commission-calculator', 'category': 'Investments & Income', 'description': 'Calculate sales commissions'},
            {'name': 'Salary Calculator', 'url': 'salary-calculator', 'category': 'Investments & Income', 'description': 'Calculate annual salary from hourly rate'},
            {'name': 'Take Home Paycheck Calculator', 'url': 'take-home-paycheck-calculator', 'category': 'Investments & Income', 'description': 'Calculate net take-home pay'},
            
            # Tax Calculators
            {'name': 'Income Tax Calculator', 'url': 'income-tax-calculator', 'category': 'Taxes', 'description': 'Calculate income tax liability'},
            {'name': 'Sales Tax Calculator', 'url': 'sales-tax-calculator', 'category': 'Taxes', 'description': 'Calculate sales tax on purchases'},
            {'name': 'Estate Tax Calculator', 'url': 'estate-tax-calculator', 'category': 'Taxes', 'description': 'Estimate estate tax obligations'},
            {'name': 'Marriage Tax Calculator', 'url': 'marriage-tax-calculator', 'category': 'Taxes', 'description': 'Calculate tax implications of marriage'},
            {'name': 'VAT Calculator', 'url': 'vat-calculator', 'category': 'Taxes', 'description': 'Calculate value-added tax'},
            
            # Payment & Utility
            {'name': 'Payment Calculator', 'url': 'payment-calculator', 'category': 'Payment & Utility', 'description': 'Calculate periodic loan payments'},
            {'name': 'Amortization Calculator', 'url': 'amortization-calculator', 'category': 'Payment & Utility', 'description': 'Create full amortization schedules'},
            {'name': 'APR Calculator', 'url': 'apr-calculator', 'category': 'Payment & Utility', 'description': 'Calculate annual percentage rate'},
            {'name': 'Finance Calculator', 'url': 'finance-calculator', 'category': 'Payment & Utility', 'description': 'General financial calculations'},
            {'name': 'Repayment Calculator', 'url': 'repayment-calculator', 'category': 'Payment & Utility', 'description': 'Calculate loan repayment schedules'},
            {'name': 'Lease Calculator', 'url': 'lease-calculator', 'category': 'Payment & Utility', 'description': 'Calculate lease payment terms'},
            {'name': 'Auto Lease Calculator', 'url': 'auto-lease-calculator', 'category': 'Payment & Utility', 'description': 'Calculate vehicle lease payments'},
            {'name': 'Refinance Calculator', 'url': 'refinance-calculator', 'category': 'Payment & Utility', 'description': 'Evaluate refinancing options'},
            {'name': 'Rent Calculator', 'url': 'rent-calculator', 'category': 'Payment & Utility', 'description': 'Calculate rent-related finances'},
            
            # Economics & Analysis
            {'name': 'College Cost Calculator', 'url': 'college-cost-calculator', 'category': 'Economics & Analysis', 'description': 'Estimate college education costs'},
            {'name': 'Currency Calculator', 'url': 'currency-calculator', 'category': 'Economics & Analysis', 'description': 'Convert between currencies'},
            {'name': 'Inflation Calculator', 'url': 'inflation-calculator', 'category': 'Economics & Analysis', 'description': 'Calculate inflation effects on values'},
            {'name': 'Budget Calculator', 'url': 'budget-calculator', 'category': 'Economics & Analysis', 'description': 'Create and track budgets'},
            {'name': 'Margin Calculator', 'url': 'margin-calculator', 'category': 'Economics & Analysis', 'description': 'Calculate profit margins'},
            {'name': 'Discount Calculator', 'url': 'discount-calculator', 'category': 'Economics & Analysis', 'description': 'Calculate discount amounts'},
            {'name': 'Percent Off Calculator', 'url': 'percent-off-calculator', 'category': 'Economics & Analysis', 'description': 'Calculate percentage discounts'},
            {'name': 'Cash Back Calculator', 'url': 'cash-back-calculator', 'category': 'Economics & Analysis', 'description': 'Calculate cash back rewards'},
            {'name': 'Depreciation Calculator', 'url': 'depreciation-calculator', 'category': 'Economics & Analysis', 'description': 'Calculate asset depreciation'},
            {'name': 'Payback Period Calculator', 'url': 'payback-period-calculator', 'category': 'Economics & Analysis', 'description': 'Calculate investment payback period'},
        ]
        
        context['calculators'] = calculators
        context['total_calculators'] = len(calculators)
        
        # Get unique categories
        categories_set = set(calc['category'] for calc in calculators)
        context['categories'] = sorted(list(categories_set))
        
        return context
