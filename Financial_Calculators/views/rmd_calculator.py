from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
from datetime import date


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RmdCalculator(View):
    """
    Class-based view for Required Minimum Distribution (RMD) Calculator.
    Calculates RMDs based on IRS Uniform Lifetime Table and SECURE Act 2.0 rules.
    """
    template_name = 'financial_calculators/rmd_calculator.html'

    UNIFORM_LIFETIME_TABLE = {
        72: 27.4, 73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0,
        79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0,
        86: 15.2, 87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8,
        93: 10.1, 94: 9.5, 95: 8.9, 96: 8.4, 97: 7.8, 98: 7.3, 99: 6.8,
        100: 6.4, 101: 6.0, 102: 5.6, 103: 5.2, 104: 4.9, 105: 4.6, 106: 4.3,
        107: 4.1, 108: 3.9, 109: 3.7, 110: 3.5, 111: 3.4, 112: 3.3, 113: 3.1,
        114: 3.0, 115: 2.9, 116: 2.8, 117: 2.7, 118: 2.5, 119: 2.3, 120: 2.0
    }

    RMD_START_AGE_2023 = 73
    RMD_START_AGE_2033 = 75

    def _get_data(self, request):
        """Parse JSON or form POST into a dict."""
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = request.body
                if not body:
                    return {}
                return json.loads(body)
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('RMD Calculator'),
            'page_title': _('RMD Calculator - Required Minimum Distribution Calculator'),
            'current_year': date.today().year,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = self._get_data(request)

            birth_year = self._get_int(data, 'birth_year', 1955)
            account_balance = self._get_float(data, 'account_balance', 500000)
            expected_return = self._get_float(data, 'expected_return', 5) / 100
            spouse_age = self._get_int(data, 'spouse_age', 0)

            account_type = data.get('account_type', 'traditional_ira')
            if isinstance(account_type, list):
                account_type = account_type[0] if account_type else 'traditional_ira'

            spouse_sole_beneficiary = data.get('spouse_sole_beneficiary')
            if isinstance(spouse_sole_beneficiary, str):
                spouse_sole_beneficiary = spouse_sole_beneficiary.lower() in ('true', '1', 'yes')
            elif spouse_sole_beneficiary is None:
                spouse_sole_beneficiary = False

            current_year = date.today().year
            current_age = current_year - birth_year

            errors = self._validate_inputs(birth_year, account_balance, current_age)
            if errors:
                return JsonResponse({'success': False, 'error': str(errors[0])}, status=400)

            result = self._calculate_rmd_projection(
                birth_year=birth_year,
                current_age=current_age,
                account_balance=account_balance,
                account_type=account_type,
                spouse_age=spouse_age,
                spouse_sole_beneficiary=spouse_sole_beneficiary,
                expected_return=expected_return
            )

            # Backend-controlled status styling (BMI-style)
            status_key = 'required' if result['rmd_has_started'] else 'not_required'
            result['status_info'] = {
                'status': status_key,
                'title': str(_('RMDs Are Required')) if result['rmd_has_started'] else str(_('RMDs Not Yet Required')),
                'message': (
                    str(_('At age %(age)s, you must take Required Minimum Distributions each year.')) % {'age': result['current_age']}
                    if result['rmd_has_started'] else
                    str(_('You have %(years)s years until RMDs begin at age %(age)s.')) % {'years': result['years_until_rmd'], 'age': result['rmd_start_age']}
                ),
                'color_info': self.get_color_info(status_key)
            }

            # Chart.js-ready chart data (backend-controlled, BMI-style)
            result['chart_data'] = self.prepare_chart_data(
                result.get('chart_data_raw'),
                result['rmd_has_started']
            )
            result.pop('chart_data_raw', None)

            return JsonResponse({'success': True, **result})

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': str(_('Invalid input: %(detail)s') % {'detail': str(e)})}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _get_float(self, data, key, default=0.0):
        """Safely get float (handles list, strips % and commas)."""
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
        """Safely get int value."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return int(float(str(value).replace(',', '').replace('$', '')))
        except (ValueError, TypeError):
            return default

    def _validate_inputs(self, birth_year, account_balance, current_age):
        """Validate calculator inputs"""
        errors = []
        current_year = date.today().year

        if birth_year < 1920 or birth_year > current_year - 18:
            errors.append(str(_('Please enter a valid birth year.')))
        if account_balance < 0:
            errors.append(str(_('Account balance must be 0 or greater.')))
        if current_age < 18 or current_age > 120:
            errors.append(str(_('Age must be between 18 and 120.')))

        return errors
    
    def _get_rmd_start_age(self, birth_year):
        """Determine RMD start age based on birth year per SECURE Act 2.0"""
        if birth_year <= 1950:
            return 72  # Already started RMDs under old rules
        elif birth_year <= 1959:
            return 73  # SECURE 2.0 for 1951-1959
        else:
            return 75  # SECURE 2.0 for 1960+
    
    def _get_distribution_period(self, age, spouse_age=0, spouse_sole_beneficiary=False):
        """Get the distribution period (life expectancy factor) for RMD calculation"""
        # If spouse is sole beneficiary and more than 10 years younger,
        # use Joint Life and Last Survivor table (not implemented here for simplicity)
        # Otherwise use Uniform Lifetime Table
        
        age = max(72, min(120, age))  # Clamp to table range
        return self.UNIFORM_LIFETIME_TABLE.get(age, 2.0)
    
    def _calculate_rmd_projection(self, birth_year, current_age, account_balance,
                                   account_type, spouse_age, spouse_sole_beneficiary,
                                   expected_return):
        """Calculate RMD projections year by year"""
        
        current_year = date.today().year
        rmd_start_age = self._get_rmd_start_age(birth_year)
        
        # Check if RMDs have started
        rmd_has_started = current_age >= rmd_start_age
        years_until_rmd = max(0, rmd_start_age - current_age)
        
        # Calculate current year RMD if applicable
        current_rmd = 0
        current_distribution_period = 0
        if rmd_has_started:
            current_distribution_period = self._get_distribution_period(
                current_age, spouse_age, spouse_sole_beneficiary
            )
            current_rmd = account_balance / current_distribution_period
        
        # Project RMDs for the next 20 years (or until account depleted); use NumPy for arrays
        balance = float(account_balance)
        yearly_breakdown = []
        labels_list = []
        rmd_amounts_list = []
        balances_list = []

        total_rmds = 0.0

        for year_offset in range(20):
            year = current_year + year_offset
            age = current_age + year_offset

            if age < rmd_start_age:
                balance *= (1 + expected_return)
                rmd = 0.0
                distribution_period = 0.0
            else:
                distribution_period = self._get_distribution_period(
                    age, spouse_age + year_offset if spouse_age else 0,
                    spouse_sole_beneficiary
                )
                rmd = balance / distribution_period if distribution_period > 0 else 0.0
                balance -= rmd
                if balance > 0:
                    balance *= (1 + expected_return)
                else:
                    balance = 0.0
                total_rmds += rmd

            starting_balance = round(balance + rmd if rmd else balance / (1 + expected_return), 2)
            yearly_breakdown.append({
                'year': year,
                'age': age,
                'starting_balance': starting_balance,
                'distribution_period': round(distribution_period, 1),
                'rmd': round(rmd, 2),
                'ending_balance': round(balance, 2)
            })
            labels_list.append(str(year))
            rmd_amounts_list.append(round(rmd, 2))
            balances_list.append(round(balance, 2))
            if balance <= 0:
                break

        chart_data_raw = {
            'labels': labels_list,
            'rmd_amounts': rmd_amounts_list,
            'balances': balances_list
        }

        estimated_tax_rate = 0.22
        current_rmd_tax = current_rmd * estimated_tax_rate
        monthly_rmd = current_rmd / 12 if current_rmd > 0 else 0

        return {
            'current_age': current_age,
            'rmd_start_age': rmd_start_age,
            'rmd_has_started': rmd_has_started,
            'years_until_rmd': years_until_rmd,
            'account_balance': round(account_balance, 2),
            'current_rmd': round(current_rmd, 2),
            'monthly_rmd': round(monthly_rmd, 2),
            'distribution_period': round(current_distribution_period, 1),
            'current_rmd_tax': round(current_rmd_tax, 2),
            'total_projected_rmds': round(total_rmds, 2),
            'chart_data_raw': chart_data_raw,
            'yearly_breakdown': yearly_breakdown
        }

    def get_color_info(self, status):
        """Return color info for status alert (backend-controlled, BMI-style)."""
        color_map = {
            'required': {
                'hex': '#2563eb',
                'rgb': 'rgb(37, 99, 235)',
                'tailwind_classes': 'bg-blue-50 border-blue-200 text-blue-800',
                'icon_classes': 'text-blue-600'
            },
            'not_required': {
                'hex': '#059669',
                'rgb': 'rgb(5, 150, 105)',
                'tailwind_classes': 'bg-green-50 border-green-200 text-green-800',
                'icon_classes': 'text-green-600'
            }
        }
        return color_map.get(status, color_map['required'])

    def prepare_chart_data(self, raw, rmd_has_started):
        """Build Chart.js-ready config for RMD and balance charts (backend-controlled)."""
        if not raw or not raw.get('labels'):
            return {'rmd_chart': None, 'balance_chart': None}

        labels = raw['labels']
        rmd_amounts = raw.get('rmd_amounts', [])
        balances = raw.get('balances', [])

        rmd_chart = {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'RMD Amount',
                    'data': rmd_amounts,
                    'backgroundColor': '#3b82f6',
                    'borderRadius': 8
                }]
            }
        }

        balance_chart = {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Account Balance',
                    'data': balances,
                    'borderColor': '#10b981',
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                    'fill': True,
                    'tension': 0.4
                }]
            }
        }

        return {'rmd_chart': rmd_chart, 'balance_chart': balance_chart}
