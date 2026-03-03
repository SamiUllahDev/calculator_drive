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
            {'name': _('Mortgage Calculator'), 'url': 'mortgage-calculator', 'category': _('Mortgage & Home'), 'description': _('Calculate monthly mortgage payments and total interest'), 'icon': 'fas fa-house'},
            {'name': _('Mortgage Amortization Calculator'), 'url': 'mortgage-amortization-calculator', 'category': _('Mortgage & Home'), 'description': _('View detailed amortization schedule for mortgages'), 'icon': 'fas fa-list-ol'},
            {'name': _('Mortgage Payoff Calculator'), 'url': 'mortgage-payoff-calculator', 'category': _('Mortgage & Home'), 'description': _('Calculate how quickly you can pay off your mortgage'), 'icon': 'fas fa-circle-check'},
            {'name': _('Mortgage Calculator UK'), 'url': 'mortgage-calculator-uk', 'category': _('Mortgage & Home'), 'description': _('UK mortgage calculator with local tax rates'), 'icon': 'fas fa-sterling-sign'},
            {'name': _('Canadian Mortgage Calculator'), 'url': 'canadian-mortgage-calculator', 'category': _('Mortgage & Home'), 'description': _('Canadian mortgage calculations and amortization'), 'icon': 'fas fa-dollar-sign'},
            {'name': _('FHA Loan Calculator'), 'url': 'fha-loan-calculator', 'category': _('Mortgage & Home'), 'description': _('Calculate FHA loan costs and monthly payments'), 'icon': 'fas fa-building-columns'},
            {'name': _('VA Mortgage Calculator'), 'url': 'va-mortgage-calculator', 'category': _('Mortgage & Home'), 'description': _('VA mortgage calculator for military personnel'), 'icon': 'fas fa-shield-halved'},
            {'name': _('House Affordability Calculator'), 'url': 'house-affordability-calculator', 'category': _('Mortgage & Home'), 'description': _('Determine how much house you can afford'), 'icon': 'fas fa-hand-holding-dollar'},
            {'name': _('Down Payment Calculator'), 'url': 'down-payment-calculator', 'category': _('Mortgage & Home'), 'description': _('Calculate required down payment amounts'), 'icon': 'fas fa-piggy-bank'},
            {'name': _('Rent vs Buy Calculator'), 'url': 'rent-vs-buy-calculator', 'category': _('Mortgage & Home'), 'description': _('Compare renting vs buying costs'), 'icon': 'fas fa-scale-balanced'},
            {'name': _('Real Estate Calculator'), 'url': 'real-estate-calculator', 'category': _('Mortgage & Home'), 'description': _('General real estate financial calculations'), 'icon': 'fas fa-city'},
            {'name': _('Rental Property Calculator'), 'url': 'rental-property-calculator', 'category': _('Mortgage & Home'), 'description': _('Analyze rental property investment returns'), 'icon': 'fas fa-key'},
            
            # Loans & Debt
            {'name': _('Loan Calculator'), 'url': 'loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate loan payments and total interest'), 'icon': 'fas fa-money-bill-wave'},
            {'name': _('Auto Loan Calculator'), 'url': 'auto-loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate auto loan payments and costs'), 'icon': 'fas fa-car'},
            {'name': _('Personal Loan Calculator'), 'url': 'personal-loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate personal loan payments'), 'icon': 'fas fa-user'},
            {'name': _('Business Loan Calculator'), 'url': 'business-loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate business loan terms and payments'), 'icon': 'fas fa-briefcase'},
            {'name': _('Student Loan Calculator'), 'url': 'student-loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate student loan repayment plans'), 'icon': 'fas fa-graduation-cap'},
            {'name': _('Boat Loan Calculator'), 'url': 'boat-loan-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate boat financing payments'), 'icon': 'fas fa-sailboat'},
            {'name': _('Debt Payoff Calculator'), 'url': 'debt-payoff-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate how long to pay off debt'), 'icon': 'fas fa-arrow-trend-down'},
            {'name': _('Debt Consolidation Calculator'), 'url': 'debt-consolidation-calculator', 'category': _('Loans & Debt'), 'description': _('Compare debt consolidation options'), 'icon': 'fas fa-compress'},
            {'name': _('Credit Card Calculator'), 'url': 'credit-card-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate credit card payment schedules'), 'icon': 'fas fa-credit-card'},
            {'name': _('Credit Cards Payoff Calculator'), 'url': 'credit-cards-payoff-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate payoff for multiple credit cards'), 'icon': 'far fa-credit-card'},
            {'name': _('Debt to Income Calculator'), 'url': 'debt-to-income-calculator', 'category': _('Loans & Debt'), 'description': _('Calculate your debt-to-income ratio'), 'icon': 'fas fa-percent'},
            
            # Interest & Investment
            {'name': _('Compound Interest Calculator'), 'url': 'compound-interest-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate compound interest earnings'), 'icon': 'fas fa-chart-line'},
            {'name': _('Simple Interest Calculator'), 'url': 'interest-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate simple interest on loans/savings'), 'icon': 'fas fa-percentage'},
            {'name': _('Interest Rate Calculator'), 'url': 'interest-rate-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate interest rates from other values'), 'icon': 'fas fa-arrow-trend-up'},
            {'name': _('Investment Calculator'), 'url': 'investment-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate investment growth over time'), 'icon': 'fas fa-seedling'},
            {'name': _('Future Value Calculator'), 'url': 'future-value-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate future value of investments'), 'icon': 'fas fa-forward'},
            {'name': _('Present Value Calculator'), 'url': 'present-value-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate present value of future cash flows'), 'icon': 'fas fa-backward'},
            {'name': _('Average Return Calculator'), 'url': 'average-return-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate average investment returns'), 'icon': 'fas fa-chart-bar'},
            {'name': _('IRR Calculator'), 'url': 'irr-calculator', 'category': _('Interest & Investment'), 'description': _('Calculate internal rate of return'), 'icon': 'fas fa-rotate'},
            
            # Retirement & Savings
            {'name': _('Retirement Calculator'), 'url': 'retirement-calculator', 'category': _('Retirement & Savings'), 'description': _('Plan for retirement savings goals'), 'icon': 'fas fa-umbrella-beach'},
            {'name': _('401K Calculator'), 'url': '401k-calculator', 'category': _('Retirement & Savings'), 'description': _('Calculate 401K retirement contributions'), 'icon': 'fas fa-vault'},
            {'name': _('IRA Calculator'), 'url': 'ira-calculator', 'category': _('Retirement & Savings'), 'description': _('Calculate IRA savings and growth'), 'icon': 'fas fa-sack-dollar'},
            {'name': _('Roth IRA Calculator'), 'url': 'roth-ira-calculator', 'category': _('Retirement & Savings'), 'description': _('Calculate Roth IRA contributions and growth'), 'icon': 'fas fa-coins'},
            {'name': _('RMD Calculator'), 'url': 'rmd-calculator', 'category': _('Retirement & Savings'), 'description': _('Calculate required minimum distributions'), 'icon': 'fas fa-calendar-check'},
            {'name': _('Pension Calculator'), 'url': 'pension-calculator', 'category': _('Retirement & Savings'), 'description': _('Calculate pension benefits'), 'icon': 'fas fa-landmark'},
            {'name': _('Social Security Calculator'), 'url': 'social-security-calculator', 'category': _('Retirement & Savings'), 'description': _('Estimate social security benefits'), 'icon': 'fas fa-people-roof'},
            {'name': _('Savings Calculator'), 'url': 'savings-calculator', 'category': _('Retirement & Savings'), 'description': _('Track savings growth over time'), 'icon': 'fas fa-piggy-bank'},
            
            # Investments & Income
            {'name': _('Annuity Calculator'), 'url': 'annuity-calculator', 'category': _('Investments & Income'), 'description': _('Calculate annuity payments and values'), 'icon': 'fas fa-money-check-dollar'},
            {'name': _('Annuity Payout Calculator'), 'url': 'annuity-payout-calculator', 'category': _('Investments & Income'), 'description': _('Calculate annuity payout amounts'), 'icon': 'fas fa-money-bill-transfer'},
            {'name': _('Bond Calculator'), 'url': 'bond-calculator', 'category': _('Investments & Income'), 'description': _('Calculate bond values and yields'), 'icon': 'fas fa-file-invoice-dollar'},
            {'name': _('CD Calculator'), 'url': 'cd-calculator', 'category': _('Investments & Income'), 'description': _('Calculate certificate of deposit returns'), 'icon': 'fas fa-lock'},
            {'name': _('Commission Calculator'), 'url': 'commission-calculator', 'category': _('Investments & Income'), 'description': _('Calculate sales commissions'), 'icon': 'fas fa-handshake'},
            {'name': _('Salary Calculator'), 'url': 'salary-calculator', 'category': _('Investments & Income'), 'description': _('Calculate annual salary from hourly rate'), 'icon': 'fas fa-wallet'},
            {'name': _('Take Home Paycheck Calculator'), 'url': 'take-home-paycheck-calculator', 'category': _('Investments & Income'), 'description': _('Calculate net take-home pay'), 'icon': 'fas fa-money-bills'},
            
            # Tax Calculators
            {'name': _('Income Tax Calculator'), 'url': 'income-tax-calculator', 'category': _('Taxes'), 'description': _('Calculate income tax liability'), 'icon': 'fas fa-file-invoice'},
            {'name': _('Sales Tax Calculator'), 'url': 'sales-tax-calculator', 'category': _('Taxes'), 'description': _('Calculate sales tax on purchases'), 'icon': 'fas fa-receipt'},
            {'name': _('Estate Tax Calculator'), 'url': 'estate-tax-calculator', 'category': _('Taxes'), 'description': _('Estimate estate tax obligations'), 'icon': 'fas fa-scroll'},
            {'name': _('Marriage Tax Calculator'), 'url': 'marriage-tax-calculator', 'category': _('Taxes'), 'description': _('Calculate tax implications of marriage'), 'icon': 'fas fa-ring'},
            {'name': _('VAT Calculator'), 'url': 'vat-calculator', 'category': _('Taxes'), 'description': _('Calculate value-added tax'), 'icon': 'fas fa-tag'},
            
            # Payment & Utility
            {'name': _('Payment Calculator'), 'url': 'payment-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate periodic loan payments'), 'icon': 'fas fa-money-bill'},
            {'name': _('Amortization Calculator'), 'url': 'amortization-calculator', 'category': _('Payment & Utility'), 'description': _('Create full amortization schedules'), 'icon': 'fas fa-table-list'},
            {'name': _('APR Calculator'), 'url': 'apr-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate annual percentage rate'), 'icon': 'fas fa-gauge-high'},
            {'name': _('Finance Calculator'), 'url': 'finance-calculator', 'category': _('Payment & Utility'), 'description': _('General financial calculations'), 'icon': 'fas fa-calculator'},
            {'name': _('Repayment Calculator'), 'url': 'repayment-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate loan repayment schedules'), 'icon': 'fas fa-clock-rotate-left'},
            {'name': _('Lease Calculator'), 'url': 'lease-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate lease payment terms'), 'icon': 'fas fa-file-signature'},
            {'name': _('Auto Lease Calculator'), 'url': 'auto-lease-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate vehicle lease payments'), 'icon': 'fas fa-car-side'},
            {'name': _('Refinance Calculator'), 'url': 'refinance-calculator', 'category': _('Payment & Utility'), 'description': _('Evaluate refinancing options'), 'icon': 'fas fa-arrows-spin'},
            {'name': _('Rent Calculator'), 'url': 'rent-calculator', 'category': _('Payment & Utility'), 'description': _('Calculate rent-related finances'), 'icon': 'fas fa-building'},
            
            # Economics & Analysis
            {'name': _('College Cost Calculator'), 'url': 'college-cost-calculator', 'category': _('Economics & Analysis'), 'description': _('Estimate college education costs'), 'icon': 'fas fa-school'},
            {'name': _('Currency Calculator'), 'url': 'currency-calculator', 'category': _('Economics & Analysis'), 'description': _('Convert between currencies'), 'icon': 'fas fa-money-bill-1-wave'},
            {'name': _('Inflation Calculator'), 'url': 'inflation-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate inflation effects on values'), 'icon': 'fas fa-arrow-up-right-dots'},
            {'name': _('Budget Calculator'), 'url': 'budget-calculator', 'category': _('Economics & Analysis'), 'description': _('Create and track budgets'), 'icon': 'fas fa-chart-pie'},
            {'name': _('Margin Calculator'), 'url': 'margin-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate profit margins'), 'icon': 'fas fa-chart-simple'},
            {'name': _('Discount Calculator'), 'url': 'discount-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate discount amounts'), 'icon': 'fas fa-tags'},
            {'name': _('Percent Off Calculator'), 'url': 'percent-off-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate percentage discounts'), 'icon': 'fas fa-percent'},
            {'name': _('Cash Back Calculator'), 'url': 'cash-back-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate cash back rewards'), 'icon': 'fas fa-gift'},
            {'name': _('Depreciation Calculator'), 'url': 'depreciation-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate asset depreciation'), 'icon': 'fas fa-arrow-down-wide-short'},
            {'name': _('Payback Period Calculator'), 'url': 'payback-period-calculator', 'category': _('Economics & Analysis'), 'description': _('Calculate investment payback period'), 'icon': 'fas fa-hourglass-half'},
        ]
        
        context['calculators'] = calculators
        context['total_calculators'] = len(calculators)
        
        # Get unique categories
        categories_set = set(calc['category'] for calc in calculators)
        context['categories'] = sorted(list(categories_set))
        
        return context
