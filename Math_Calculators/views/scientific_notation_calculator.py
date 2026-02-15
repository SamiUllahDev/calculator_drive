from django.views import View
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import re
import math
import logging

logger = logging.getLogger(__name__)


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ScientificNotationCalculator(View):
    """
    Class-based view for Scientific Notation Calculator.
    Converts numbers to/from scientific notation and performs basic operations. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'math_calculators/scientific_notation_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Scientific Notation Calculator'))}
        return render(request, self.template_name, context)

    def _get_data(self, request):
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = request.body
                if not body:
                    return {}
                return json.loads(body)
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        if request.body:
            try:
                return json.loads(request.body)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _parse_number(self, s):
        """Parse decimal or scientific notation string to float. Returns (float, error_msg)."""
        if s is None or (isinstance(s, str) and not s.strip()):
            return None, str(_('No value provided.'))
        s = str(s).strip().replace(',', '')
        # Already a number
        try:
            return float(s), None
        except ValueError:
            pass
        # Scientific: 1.5e10, 1.5E-3, 1.5×10^6, 1.5*10^6, 1.5 10^6
        s_lower = s.replace('×', '*').replace(' ', '')
        m = re.match(r'^([+-]?\d*\.?\d+)\*?10\^?([+-]?\d+)$', s_lower, re.I)
        if m:
            try:
                mantissa = float(m.group(1))
                exponent = int(m.group(2))
                return mantissa * (10 ** exponent), None
            except (ValueError, OverflowError):
                return None, str(_('Invalid scientific notation.'))
        # Try e-notation again with explicit e
        if 'e' in s_lower or 'E' in s_lower:
            try:
                return float(s_lower), None
            except ValueError:
                return None, str(_('Invalid e-notation.'))
        return None, str(_('Could not parse number. Use decimal (e.g. 1500) or scientific (e.g. 1.5e3 or 1.5×10^3).'))

    def _to_scientific(self, x):
        """Convert float to scientific notation string (mantissa × 10^exponent)."""
        if x == 0:
            return '0', 0, 0.0
        sign = -1 if x < 0 else 1
        x = abs(x)
        try:
            exponent = math.floor(math.log10(x))
        except (ValueError, OverflowError):
            return str(x), 0, x
        mantissa = sign * (x / (10 ** exponent))
        if mantissa >= 10 or (mantissa < 1 and mantissa > 0):
            mantissa = mantissa / 10
            exponent = exponent + 1
        elif mantissa <= -10 or (mantissa > -1 and mantissa < 0):
            mantissa = mantissa / 10
            exponent = exponent + 1
        mantissa = round(mantissa, 10)
        if exponent == 0:
            s = str(mantissa)
        else:
            s = str(mantissa) + ' × 10^' + str(exponent)
        return s, exponent, mantissa

    def _prepare_chart_data(self, exponents_data):
        """Bar chart of exponents (e.g. value 1, value 2, result)."""
        if not exponents_data or not any(e is not None for e in exponents_data):
            return {}
        labels = []
        values = []
        for item in exponents_data:
            if isinstance(item, dict):
                labels.append(item.get('label', ''))
                values.append(item.get('exponent', 0))
            else:
                values.append(item)
        if not labels and values:
            labels = [str(_('Value 1')), str(_('Value 2')), str(_('Result'))][: len(values)]
        elif not labels:
            return {}
        return {
            'magnitude_chart': {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': str(_('Exponent (power of 10)')),
                        'data': values,
                        'backgroundColor': '#6366f1',
                        'borderRadius': 4,
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'scales': {
                        'x': {'grid': {'display': False}},
                        'y': {'ticks': {'precision': 0}}
                    },
                    'plugins': {'legend': {'display': False}}
                }
            }
        }

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            calc_type = data.get('calc_type', 'to_scientific')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'to_scientific'

            value_raw = data.get('value') or data.get('input1')
            if isinstance(value_raw, list):
                value_raw = value_raw[0] if value_raw else ''

            if calc_type == 'to_scientific':
                num, err = self._parse_number(value_raw)
                if err:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                if num is None:
                    return JsonResponse({'success': False, 'error': str(_('Could not parse number.'))}, status=400)
                sci_str, exponent, mantissa = self._to_scientific(num)
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'input_decimal': num,
                    'result_scientific': sci_str,
                    'mantissa': round(mantissa, 10),
                    'exponent': exponent,
                    'summary': {
                        'input': num,
                        'result_scientific': sci_str,
                        'exponent': exponent,
                        'mantissa': round(mantissa, 10)
                    }
                }
                result['chart_data'] = self._prepare_chart_data([{'label': str(_('Exponent')), 'exponent': exponent}])

            elif calc_type == 'from_scientific':
                num, err = self._parse_number(value_raw)
                if err:
                    return JsonResponse({'success': False, 'error': err}, status=400)
                if num is None:
                    return JsonResponse({'success': False, 'error': str(_('Could not parse number.'))}, status=400)
                sci_str, exponent, mantissa = self._to_scientific(num)
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'input_scientific': value_raw,
                    'result_decimal': num,
                    'result_scientific': sci_str,
                    'exponent': exponent,
                    'mantissa': round(mantissa, 10),
                    'summary': {
                        'result_decimal': num,
                        'result_scientific': sci_str,
                        'exponent': exponent
                    }
                }
                result['chart_data'] = self._prepare_chart_data([{'label': str(_('Exponent')), 'exponent': exponent}])

            elif calc_type in ('add', 'subtract', 'multiply', 'divide'):
                value2_raw = data.get('value2') or data.get('input2')
                if isinstance(value2_raw, list):
                    value2_raw = value2_raw[0] if value2_raw else ''
                num1, err1 = self._parse_number(value_raw)
                num2, err2 = self._parse_number(value2_raw)
                if err1:
                    return JsonResponse({'success': False, 'error': err1}, status=400)
                if err2:
                    return JsonResponse({'success': False, 'error': str(_('Second value: ')) + err2}, status=400)
                if num1 is None:
                    return JsonResponse({'success': False, 'error': str(_('Could not parse first number.'))}, status=400)
                if num2 is None:
                    return JsonResponse({'success': False, 'error': str(_('Could not parse second number.'))}, status=400)
                if calc_type == 'divide' and num2 == 0:
                    return JsonResponse({'success': False, 'error': str(_('Cannot divide by zero.'))}, status=400)
                if calc_type == 'add':
                    res = num1 + num2
                elif calc_type == 'subtract':
                    res = num1 - num2
                elif calc_type == 'multiply':
                    res = num1 * num2
                else:
                    res = num1 / num2
                res_sci, res_exp, res_mant = self._to_scientific(res)
                s1, e1, _ = self._to_scientific(num1)
                s2, e2, _ = self._to_scientific(num2)
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'value1': num1,
                    'value2': num2,
                    'value1_scientific': s1,
                    'value2_scientific': s2,
                    'result_decimal': res,
                    'result_scientific': res_sci,
                    'exponent': res_exp,
                    'mantissa': round(res_mant, 10),
                    'summary': {
                        'value1': num1,
                        'value2': num2,
                        'result_decimal': res,
                        'result_scientific': res_sci,
                        'exponent': res_exp
                    }
                }
                result['chart_data'] = self._prepare_chart_data([
                    {'label': str(_('Value 1')), 'exponent': e1},
                    {'label': str(_('Value 2')), 'exponent': e2},
                    {'label': str(_('Result')), 'exponent': res_exp}
                ])

            else:
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Scientific notation JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError, OverflowError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Scientific notation calculation failed: %s", e)
            from django.conf import settings
            err_msg = str(_("An error occurred during calculation."))
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )
