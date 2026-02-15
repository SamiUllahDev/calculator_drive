from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np
from datetime import datetime

try:
    from dateutil.relativedelta import relativedelta
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False


def add_months(source_date, months):
    """Add months to a date"""
    if HAS_DATEUTIL:
        return source_date + relativedelta(months=months)
    else:
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return datetime(year, month, day)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class InvestmentCalculator(View):
    """
    Professional Investment Calculator with comprehensive features.
    
    Features:
    - Future value projection
    - Return on investment (ROI)
    - Inflation-adjusted returns
    - Tax impact analysis
    - Portfolio growth visualization
    - Multiple scenario comparison
    """
    template_name = 'financial_calculators/investment_calculator.html'
    
    # Validation limits
    MIN_AMOUNT = 0
    MAX_AMOUNT = 1000000000
    MIN_RATE = -50
    MAX_RATE = 100
    MIN_YEARS = 1
    MAX_YEARS = 50
    
    def _get_data(self, request):
        """Parse JSON or form POST into a dict."""
        if request.content_type and 'application/json' in request.content_type:
            return json.loads(request.body)
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Investment Calculator'),
            'page_title': _('Investment Calculator - ROI & Portfolio Growth Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations (JSON or form)."""
        try:
            data = self._get_data(request)
            
            # Get inputs
            initial_investment = self._get_float(data, 'initial_investment', 0)
            monthly_contribution = self._get_float(data, 'monthly_contribution', 0)
            annual_return = self._get_float(data, 'annual_return', 0)
            years = self._get_int(data, 'years', 0)
            inflation_rate = self._get_float(data, 'inflation_rate', 0)
            tax_rate = self._get_float(data, 'tax_rate', 0)
            
            # Validation
            errors = []
            
            if initial_investment < self.MIN_AMOUNT:
                errors.append(_('Initial investment cannot be negative.'))
            elif initial_investment > self.MAX_AMOUNT:
                errors.append(_('Initial investment cannot exceed %(max)s.') % {'max': f'${self.MAX_AMOUNT:,}'})
            
            if monthly_contribution < self.MIN_AMOUNT:
                errors.append(_('Monthly contribution cannot be negative.'))
            elif monthly_contribution > self.MAX_AMOUNT / 12:
                errors.append(_('Monthly contribution is too large.'))
            
            if annual_return < self.MIN_RATE:
                errors.append(_('Annual return cannot be less than %(min)s%%.') % {'min': self.MIN_RATE})
            elif annual_return > self.MAX_RATE:
                errors.append(_('Annual return cannot exceed %(max)s%%.') % {'max': self.MAX_RATE})
            
            if years < self.MIN_YEARS:
                errors.append(_('Investment period must be at least %(min)s year.') % {'min': self.MIN_YEARS})
            elif years > self.MAX_YEARS:
                errors.append(_('Investment period cannot exceed %(max)s years.') % {'max': self.MAX_YEARS})
            
            if inflation_rate < 0:
                errors.append(_('Inflation rate cannot be negative.'))
            elif inflation_rate > 30:
                errors.append(_('Inflation rate cannot exceed 30%%.'))
            
            if tax_rate < 0 or tax_rate > 100:
                errors.append(_('Tax rate must be between 0%% and 100%%.'))
            
            if initial_investment == 0 and monthly_contribution == 0:
                errors.append(_('Please enter either an initial investment or monthly contribution.'))
            
            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)
            
            # Calculate investment growth
            result = self._calculate_investment(
                initial_investment,
                monthly_contribution,
                annual_return,
                years,
                inflation_rate,
                tax_rate
            )
            
            return JsonResponse({
                'success': True,
                **result
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: %(detail)s') % {'detail': str(e)}}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
    
    def _get_float(self, data, key, default=0):
        """Safely get float value (handles list from form POST)."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default
    
    def _get_int(self, data, key, default=0):
        """Safely get int value (handles list from form POST)."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default
    
    def _calculate_investment(self, initial, monthly, annual_return, years, inflation_rate, tax_rate):
        """Calculate investment growth with comprehensive analysis"""
        
        months = years * 12
        monthly_rate = annual_return / 100 / 12
        inflation_monthly = inflation_rate / 100 / 12
        
        # Track values
        balance = initial
        total_contributions = initial
        total_gains = 0
        
        yearly_breakdown = []
        chart_labels = ['Start']
        chart_balance = [initial]
        chart_contributions = [initial]
        chart_inflation_adjusted = [initial]
        
        current_year = datetime.now().year
        year_start_balance = initial
        year_contributions = 0
        year_gains = 0
        
        for month in range(1, months + 1):
            # Add monthly contribution
            balance += monthly
            total_contributions += monthly
            year_contributions += monthly
            
            # Calculate gains
            gains = balance * monthly_rate
            balance += gains
            total_gains += gains
            year_gains += gains
            
            # Year end summary
            if month % 12 == 0:
                year_num = month // 12
                
                # Calculate inflation-adjusted value
                inflation_factor = np.power(1 + inflation_rate / 100, year_num)
                inflation_adjusted = balance / inflation_factor
                
                yearly_breakdown.append({
                    'year': current_year + year_num,
                    'year_num': year_num,
                    'contributions': round(year_contributions, 2),
                    'gains': round(year_gains, 2),
                    'end_balance': round(balance, 2),
                    'inflation_adjusted': round(inflation_adjusted, 2),
                })
                
                chart_labels.append(f'Year {year_num}')
                chart_balance.append(round(balance, 2))
                chart_contributions.append(round(total_contributions, 2))
                chart_inflation_adjusted.append(round(inflation_adjusted, 2))
                
                year_start_balance = balance
                year_contributions = 0
                year_gains = 0
        
        # Final calculations
        final_balance = balance
        
        # Inflation-adjusted final value
        inflation_factor = np.power(1 + inflation_rate / 100, years)
        inflation_adjusted_value = final_balance / inflation_factor
        
        # Tax impact (on gains only)
        taxable_gains = total_gains
        taxes_owed = taxable_gains * (tax_rate / 100)
        after_tax_value = final_balance - taxes_owed
        
        # ROI calculation
        roi = ((final_balance - total_contributions) / total_contributions * 100) if total_contributions > 0 else 0
        
        # Annualized return (CAGR)
        if initial > 0 and years > 0:
            cagr = (np.power(final_balance / initial, 1 / years) - 1) * 100
        else:
            cagr = annual_return
        
        # Compare scenarios (what if different returns)
        scenarios = []
        for rate in [annual_return - 2, annual_return, annual_return + 2]:
            scenario_balance = self._simple_fv(initial, monthly, rate / 100, years)
            scenarios.append({
                'rate': rate,
                'final_balance': round(scenario_balance, 2),
            })
        
        # End date
        end_date = add_months(datetime.now(), months)
        
        return {
            'summary': {
                'final_balance': round(final_balance, 2),
                'total_contributions': round(total_contributions, 2),
                'total_gains': round(total_gains, 2),
                'roi': round(roi, 2),
                'cagr': round(cagr, 2),
            },
            'inflation_adjusted': {
                'value': round(inflation_adjusted_value, 2),
                'purchasing_power_lost': round(final_balance - inflation_adjusted_value, 2),
            },
            'tax_impact': {
                'taxable_gains': round(taxable_gains, 2),
                'taxes_owed': round(taxes_owed, 2),
                'after_tax_value': round(after_tax_value, 2),
            },
            'scenarios': scenarios,
            'yearly_breakdown': yearly_breakdown,
            'chart_data': {
                'labels': chart_labels,
                'balance': chart_balance,
                'contributions': chart_contributions,
                'inflation_adjusted': chart_inflation_adjusted,
            },
            'end_date': end_date.strftime('%B %Y'),
            'input': {
                'initial': initial,
                'monthly': monthly,
                'annual_return': annual_return,
                'years': years,
            }
        }
    
    def _simple_fv(self, initial, monthly, annual_rate, years):
        """Calculate simple future value for scenarios"""
        monthly_rate = annual_rate / 12
        months = years * 12
        
        balance = initial
        for _ in range(months):
            balance += monthly
            balance *= (1 + monthly_rate)
        
        return balance
