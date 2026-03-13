from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.translation import gettext as _


class FinanceIndexView(TemplateView):
    template_name = 'financial_calculators/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Comprehensive financial calculators list organized by categories
        calculators = [
            # Mortgage & Home
            {'name': _('Mortgage Calculator'), 'url': 'mortgage-calculator', 'category': _('Mortgage & Home'), 'description': _('Calculate monthly mortgage payments and total interest'), },
            {'name': _('Mortgage Amortization Calculator'), 'url': 'mortgage-amortization-calculator', 'category': _('Mortgage & Home'), 'description': _('View detailed amortization schedule for mortgages'), },
            {'name': _('Mortgage Payoff Calculator'), 'url': 'mortgage-payoff-calculator', 'category': _('Mortgage & Home'), 'description': _('Calculate how quickly you can pay off your mortgage'), },
            {'name': _('Mortgage Calculator UK'), 'url': 'mortgage-calculator-uk', 'category': _('Mortgage & Home'), 'description': _('UK mortgage calculator with local tax rates'), },
            {'name': _('Canadian Mortgage Calculator'), 'url': 'canadian-mortgage-calculator', 'category': _('Mortgage & Home'), 'description': _('Canadian mortgage calculations and amortization'), },
            {'name': _('FHA Loan Calculator'), 'url': 'fha-loan-calculator', 'category': _('Mortgage & Home'), 'description': _('Calculate FHA loan costs and monthly payments'), },
            {'name': _('VA Mortgage Calculator'), 'url': 'va-mortgage-calculator', 'category': _('Mortgage & Home'), 'description': _('VA mortgage calculator for military personnel'), },
            {'name': _('House Affordability Calculator'), 'url': 'house-affordability-calculator', 'category': _('Mortgage & Home'), 'description': _('Determine how much house you can afford'), },
            {'name': _('Down Payment Calculator'), 'url': 'down-payment-calculator', 'category': _('Mortgage & Home'), 'description': _('Calculate required down payment amounts'), },
            {'name': _('Rent vs Buy Calculator'), 'url': 'rent-vs-buy-calculator', 'category': _('Mortgage & Home'), 'description': _('Compare renting vs buying costs'), },
            {'name': _('Real Estate Calculator'), 'url': 'real-estate-calculator', 'category': _('Mortgage & Home'), 'description': _('General real estate financial calculations'), },
            {'name': _('Rental Property Calculator'), 'url': 'rental-property-calculator', 'category': _('Mortgage & Home'), 'description': _('Analyze rental property investment returns'), },
            
            # Loans & Debt
            {'name': _('Loan Calculator'), 'url': 'loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate loan payments and total interest'), },
            {'name': _('Auto Loan Calculator'), 'url': 'auto-loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate auto loan payments and costs'), },
            {'name': _('Personal Loan Calculator'), 'url': 'personal-loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate personal loan payments'), },
            {'name': _('Business Loan Calculator'), 'url': 'business-loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate business loan terms and payments'), },
            {'name': _('Student Loan Calculator'), 'url': 'student-loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate student loan repayment plans'), },
            {'name': _('Boat Loan Calculator'), 'url': 'boat-loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate boat financing payments'), },
            {'name': _('Debt Payoff Calculator'), 'url': 'debt-payoff-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate how long to pay off debt'), },
            {'name': _('Debt Consolidation Calculator'), 'url': 'debt-consolidation-calculator', 'category': _('Loans & Debt'), 'description': _('Compare debt consolidation options'), },
            {'name': _('Credit Card Calculator'), 'url': 'credit-card-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate credit card payment schedules'), },
            {'name': _('Credit Cards Payoff Calculator'), 'url': 'credit-cards-payoff-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate payoff for multiple credit cards'), },
            {'name': _('Debt to Income Calculator'), 'url': 'debt-to-income-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate your debt-to-income ratio'), },
            
            # Interest & Investment
            {'name': _('Compound Interest Calculator'), 'url': 'compound-interest-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate compound interest earnings'), },
            {'name': _('Simple Interest Calculator'), 'url': 'interest-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate simple interest on loans/savings'), },
            {'name': _('Interest Rate Calculator'), 'url': 'interest-rate-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate interest rates from other values'), },
            {'name': _('Investment Calculator'), 'url': 'investment-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate investment growth over time'), },
            {'name': _('Future Value Calculator'), 'url': 'future-value-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate future value of investments'), },
            {'name': _('Present Value Calculator'), 'url': 'present-value-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate present value of future cash flows'), },
            {'name': _('Average Return Calculator'), 'url': 'average-return-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate average investment returns'), },
            {'name': _('IRR Calculator'), 'url': 'irr-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate internal rate of return'), },
            
            # Retirement & Savings
            {'name': _('Retirement Calculator'), 'url': 'retirement-calculator', 'category': _('Retirement & Savings'), 'description': _('Plan for retirement savings goals'), },
            {'name': _('401K Calculator'), 'url': '401k-calculator', 'category': _('Retirement & Savings'), 'description': _('Calculate 401K retirement contributions'), },
            {'name': _('IRA Calculator'), 'url': 'ira-calculator', 'category': _('Retirement & Savings'), 'description': _('Calculate IRA savings and growth'), },
            {'name': _('Roth IRA Calculator'), 'url': 'roth-ira-calculator', 'category': _('Retirement & Savings'), 'description': _('Calculate Roth IRA contributions and growth'), },
            {'name': _('RMD Calculator'), 'url': 'rmd-calculator', 'category': _('Retirement & Savings'), 'description': _('Calculate required minimum distributions'), },
            {'name': _('Pension Calculator'), 'url': 'pension-calculator', 'category': _('Retirement & Savings'), 'description': _('Calculate pension benefits'), },
            {'name': _('Social Security Calculator'), 'url': 'social-security-calculator', 'category': _('Retirement & Savings'), 'description': _('Estimate social security benefits'), },
            {'name': _('Savings Calculator'), 'url': 'savings-calculator', 'category': _('Retirement & Savings'), 'description': _('Track savings growth over time'), },
            
            # Investments & Income
            {'name': _('Annuity Calculator'), 'url': 'annuity-calculator', 'category': _('Investments & Income'), 'description': _('Calculate annuity payments and values'), },
            {'name': _('Annuity Payout Calculator'), 'url': 'annuity-payout-calculator', 'category': _('Investments & Income'), 'description': _('Calculate annuity payout amounts'), },
            {'name': _('Bond Calculator'), 'url': 'bond-calculator', 'category': _('Investments & Income'), 'description': _('Calculate bond values and yields'), },
            {'name': _('CD Calculator'), 'url': 'cd-calculator', 'category': _('Investments & Income'), 'description': _('Calculate certificate of deposit returns'), },
            {'name': _('Commission Calculator'), 'url': 'commission-calculator', 'category': _('Investments & Income'), 'description': _('Calculate sales commissions'), },
            {'name': _('Salary Calculator'), 'url': 'salary-calculator', 'category': _('Investments & Income'), 'description': _('Calculate annual salary from hourly rate'), },
            {'name': _('Take Home Paycheck Calculator'), 'url': 'take-home-paycheck-calculator', 'category': _('Investments & Income'), 'description': _('Calculate net take-home pay'), },
            
            # Tax Calculators
            {'name': _('Income Tax Calculator'), 'url': 'income-tax-calculator', 'category': _('Taxes'), 'description': _('Calculate income tax liability'), },
            {'name': _('Sales Tax Calculator'), 'url': 'sales-tax-calculator', 'category': _('Taxes'), 'description': _('Calculate sales tax on purchases'), },
            {'name': _('Estate Tax Calculator'), 'url': 'estate-tax-calculator', 'category': _('Taxes'), 'description': _('Estimate estate tax obligations'), },
            {'name': _('Marriage Tax Calculator'), 'url': 'marriage-tax-calculator', 'category': _('Taxes'), 'description': _('Calculate tax implications of marriage'), },
            {'name': _('VAT Calculator'), 'url': 'vat-calculator', 'category': _('Taxes'), 'description': _('Calculate value-added tax'), },
            
            # Payment & Utility
            {'name': _('Payment Calculator'), 'url': 'payment-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate periodic loan payments'), },
            {'name': _('Amortization Calculator'), 'url': 'amortization-calculator', 'category': _('Payment & Utility'), 'description': _('Create full amortization schedules'), },
            {'name': _('APR Calculator'), 'url': 'apr-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate annual percentage rate'), },
            {'name': _('Finance Calculator'), 'url': 'finance-calculator', 'category': _('Payment & Utility'), 'description': _('General financial calculations'), },
            {'name': _('Repayment Calculator'), 'url': 'repayment-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate loan repayment schedules'), },
            {'name': _('Lease Calculator'), 'url': 'lease-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate lease payment terms'), },
            {'name': _('Auto Lease Calculator'), 'url': 'auto-lease-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate vehicle lease payments'), },
            {'name': _('Refinance Calculator'), 'url': 'refinance-calculator', 'category': _('Payment & Utility'), 'description': _('Evaluate refinancing options'), },
            {'name': _('Rent Calculator'), 'url': 'rent-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate rent-related finances'), },
            
            # Economics & Analysis
            {'name': _('College Cost Calculator'), 'url': 'college-cost-calculator', 'category': _('Economics & Analysis'), 'description': _('Estimate college education costs'), },
            {'name': _('Currency Calculator'), 'url': 'currency-calculator', 'category': _('Economics & Analysis'), 'description': _('Convert between currencies'), },
            {'name': _('Inflation Calculator'), 'url': 'inflation-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate inflation effects on values'), },
            {'name': _('Budget Calculator'), 'url': 'budget-calculator', 'category': _('Economics & Analysis'), 'description': _('Create and track budgets'), },
            {'name': _('Margin Calculator'), 'url': 'margin-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate profit margins'), },
            {'name': _('Discount Calculator'), 'url': 'discount-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate discount amounts'), },
            {'name': _('Percent Off Calculator'), 'url': 'percent-off-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate percentage discounts'), },
            {'name': _('Cash Back Calculator'), 'url': 'cash-back-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate cash back rewards'), },
            {'name': _('Depreciation Calculator'), 'url': 'depreciation-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate asset depreciation'), },
            {'name': _('Payback Period Calculator'), 'url': 'payback-period-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate investment payback period'), },
        ]
        
        context['calculators'] = calculators
        context['total_calculators'] = len(calculators)
        
        # Get unique categories
        categories_set = set(calc['category'] for calc in calculators)
        context['categories'] = sorted(list(categories_set))
        
        return context
