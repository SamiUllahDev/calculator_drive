from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from scipy import stats
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PValueCalculator(View):
    """
    Enhanced Professional P-Value Calculator
    Calculates p-values for various statistical tests with step-by-step solutions.
    """
    template_name = 'math_calculators/p_value_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'P-Value Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value, name, allow_zero=False):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if not allow_zero and num <= 0:
                return None, f'{name} must be greater than zero.'
            if allow_zero and num < 0:
                return None, f'{name} must be greater than or equal to zero.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_z_test_pvalue(self, z_score, test_type='two-tailed'):
        """Calculate p-value for z-test"""
        try:
            if test_type == 'two-tailed':
                p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
            elif test_type == 'one-tailed-right':
                p_value = 1 - stats.norm.cdf(z_score)
            else:  # one-tailed-left
                p_value = stats.norm.cdf(z_score)
            
            return p_value, None
        except Exception as e:
            return None, str(e)
    
    def _calculate_t_test_pvalue(self, t_score, df, test_type='two-tailed'):
        """Calculate p-value for t-test"""
        try:
            if df <= 0:
                return None, 'Degrees of freedom must be greater than zero.'
            
            if test_type == 'two-tailed':
                p_value = 2 * (1 - stats.t.cdf(abs(t_score), df))
            elif test_type == 'one-tailed-right':
                p_value = 1 - stats.t.cdf(t_score, df)
            else:  # one-tailed-left
                p_value = stats.t.cdf(t_score, df)
            
            return p_value, None
        except Exception as e:
            return None, str(e)
    
    def _calculate_chi_square_pvalue(self, chi_square, df):
        """Calculate p-value for chi-square test"""
        try:
            if df <= 0:
                return None, 'Degrees of freedom must be greater than zero.'
            
            p_value = 1 - stats.chi2.cdf(chi_square, df)
            return p_value, None
        except Exception as e:
            return None, str(e)
    
    def _calculate_f_test_pvalue(self, f_score, df1, df2):
        """Calculate p-value for F-test"""
        try:
            if df1 <= 0 or df2 <= 0:
                return None, 'Degrees of freedom must be greater than zero.'
            
            p_value = 1 - stats.f.cdf(f_score, df1, df2)
            return p_value, None
        except Exception as e:
            return None, str(e)
    
    def _prepare_step_by_step(self, test_type, test_statistic, p_value, **kwargs):
        """Prepare step-by-step solution"""
        steps = []
        
        if test_type == 'z-test':
            z_score = test_statistic
            tail_type = kwargs.get('tail_type', 'two-tailed')
            
            steps.append(f"Given: Z-test")
            steps.append(f"  Z-score: {z_score:.6f}")
            steps.append(f"  Test type: {tail_type.replace('-', ' ').title()}")
            steps.append("")
            steps.append("Step 1: Understand the p-value")
            steps.append("  The p-value is the probability of observing a test statistic")
            steps.append("  as extreme as, or more extreme than, the observed value")
            steps.append("  under the null hypothesis.")
            steps.append("")
            steps.append("Step 2: Calculate p-value")
            if tail_type == 'two-tailed':
                steps.append(f"  For two-tailed test: p = 2 × P(Z ≥ |{z_score:.6f}|)")
                steps.append(f"  p = 2 × (1 - Φ(|{z_score:.6f}|))")
                steps.append(f"  p = 2 × (1 - {stats.norm.cdf(abs(z_score)):.6f})")
                steps.append(f"  p = {p_value:.6f}")
            elif tail_type == 'one-tailed-right':
                steps.append(f"  For right-tailed test: p = P(Z ≥ {z_score:.6f})")
                steps.append(f"  p = 1 - Φ({z_score:.6f})")
                steps.append(f"  p = 1 - {stats.norm.cdf(z_score):.6f}")
                steps.append(f"  p = {p_value:.6f}")
            else:
                steps.append(f"  For left-tailed test: p = P(Z ≤ {z_score:.6f})")
                steps.append(f"  p = Φ({z_score:.6f})")
                steps.append(f"  p = {stats.norm.cdf(z_score):.6f}")
                steps.append(f"  p = {p_value:.6f}")
            steps.append("")
            steps.append("Step 3: Interpretation")
            if p_value < 0.01:
                steps.append(f"  p-value = {p_value:.6f} < 0.01: Very strong evidence against H₀")
            elif p_value < 0.05:
                steps.append(f"  p-value = {p_value:.6f} < 0.05: Strong evidence against H₀")
            elif p_value < 0.10:
                steps.append(f"  p-value = {p_value:.6f} < 0.10: Weak evidence against H₀")
            else:
                steps.append(f"  p-value = {p_value:.6f} ≥ 0.10: Little to no evidence against H₀")
        
        elif test_type == 't-test':
            t_score = test_statistic
            df = kwargs.get('df')
            tail_type = kwargs.get('tail_type', 'two-tailed')
            
            steps.append(f"Given: t-test")
            steps.append(f"  t-score: {t_score:.6f}")
            steps.append(f"  Degrees of freedom (df): {df}")
            steps.append(f"  Test type: {tail_type.replace('-', ' ').title()}")
            steps.append("")
            steps.append("Step 1: Understand the p-value")
            steps.append("  The p-value is calculated using the t-distribution")
            steps.append("  with the given degrees of freedom.")
            steps.append("")
            steps.append("Step 2: Calculate p-value")
            if tail_type == 'two-tailed':
                steps.append(f"  For two-tailed test: p = 2 × P(t ≥ |{t_score:.6f}|)")
                steps.append(f"  p = 2 × (1 - t_cdf(|{t_score:.6f}|, df={df}))")
                steps.append(f"  p = {p_value:.6f}")
            elif tail_type == 'one-tailed-right':
                steps.append(f"  For right-tailed test: p = P(t ≥ {t_score:.6f})")
                steps.append(f"  p = 1 - t_cdf({t_score:.6f}, df={df})")
                steps.append(f"  p = {p_value:.6f}")
            else:
                steps.append(f"  For left-tailed test: p = P(t ≤ {t_score:.6f})")
                steps.append(f"  p = t_cdf({t_score:.6f}, df={df})")
                steps.append(f"  p = {p_value:.6f}")
            steps.append("")
            steps.append("Step 3: Interpretation")
            if p_value < 0.01:
                steps.append(f"  p-value = {p_value:.6f} < 0.01: Very strong evidence against H₀")
            elif p_value < 0.05:
                steps.append(f"  p-value = {p_value:.6f} < 0.05: Strong evidence against H₀")
            elif p_value < 0.10:
                steps.append(f"  p-value = {p_value:.6f} < 0.10: Weak evidence against H₀")
            else:
                steps.append(f"  p-value = {p_value:.6f} ≥ 0.10: Little to no evidence against H₀")
        
        elif test_type == 'chi-square':
            chi_square = test_statistic
            df = kwargs.get('df')
            
            steps.append(f"Given: Chi-square test")
            steps.append(f"  Chi-square statistic: {chi_square:.6f}")
            steps.append(f"  Degrees of freedom (df): {df}")
            steps.append("")
            steps.append("Step 1: Understand the p-value")
            steps.append("  The p-value is calculated using the chi-square distribution")
            steps.append("  with the given degrees of freedom.")
            steps.append("")
            steps.append("Step 2: Calculate p-value")
            steps.append(f"  p = P(χ² ≥ {chi_square:.6f})")
            steps.append(f"  p = 1 - χ²_cdf({chi_square:.6f}, df={df})")
            steps.append(f"  p = {p_value:.6f}")
            steps.append("")
            steps.append("Step 3: Interpretation")
            if p_value < 0.01:
                steps.append(f"  p-value = {p_value:.6f} < 0.01: Very strong evidence against H₀")
            elif p_value < 0.05:
                steps.append(f"  p-value = {p_value:.6f} < 0.05: Strong evidence against H₀")
            elif p_value < 0.10:
                steps.append(f"  p-value = {p_value:.6f} < 0.10: Weak evidence against H₀")
            else:
                steps.append(f"  p-value = {p_value:.6f} ≥ 0.10: Little to no evidence against H₀")
        
        elif test_type == 'f-test':
            f_score = test_statistic
            df1 = kwargs.get('df1')
            df2 = kwargs.get('df2')
            
            steps.append(f"Given: F-test")
            steps.append(f"  F-statistic: {f_score:.6f}")
            steps.append(f"  Degrees of freedom (df1): {df1}")
            steps.append(f"  Degrees of freedom (df2): {df2}")
            steps.append("")
            steps.append("Step 1: Understand the p-value")
            steps.append("  The p-value is calculated using the F-distribution")
            steps.append("  with the given degrees of freedom.")
            steps.append("")
            steps.append("Step 2: Calculate p-value")
            steps.append(f"  p = P(F ≥ {f_score:.6f})")
            steps.append(f"  p = 1 - F_cdf({f_score:.6f}, df1={df1}, df2={df2})")
            steps.append(f"  p = {p_value:.6f}")
            steps.append("")
            steps.append("Step 3: Interpretation")
            if p_value < 0.01:
                steps.append(f"  p-value = {p_value:.6f} < 0.01: Very strong evidence against H₀")
            elif p_value < 0.05:
                steps.append(f"  p-value = {p_value:.6f} < 0.05: Strong evidence against H₀")
            elif p_value < 0.10:
                steps.append(f"  p-value = {p_value:.6f} < 0.10: Weak evidence against H₀")
            else:
                steps.append(f"  p-value = {p_value:.6f} ≥ 0.10: Little to no evidence against H₀")
        
        return steps
    
    def _prepare_chart_data(self, test_type, test_statistic, p_value, **kwargs):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            if test_type == 'z-test':
                # Normal distribution curve
                z_score = test_statistic
                x = np.linspace(-4, 4, 100)
                y = stats.norm.pdf(x, 0, 1)
                
                chart_data['distribution_chart'] = {
                    'type': 'line',
                    'data': {
                        'labels': [f'{val:.2f}' for val in x],
                        'datasets': [{
                            'label': 'Standard Normal Distribution',
                            'data': y.tolist(),
                            'borderColor': '#3b82f6',
                            'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                            'borderWidth': 2,
                            'fill': True,
                            'tension': 0.4
                        }]
                    }
                }
            elif test_type == 't-test':
                # t-distribution curve
                t_score = test_statistic
                df = kwargs.get('df', 10)
                x = np.linspace(-4, 4, 100)
                y = stats.t.pdf(x, df)
                
                chart_data['distribution_chart'] = {
                    'type': 'line',
                    'data': {
                        'labels': [f'{val:.2f}' for val in x],
                        'datasets': [{
                            'label': f't-distribution (df={df})',
                            'data': y.tolist(),
                            'borderColor': '#10b981',
                            'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                            'borderWidth': 2,
                            'fill': True,
                            'tension': 0.4
                        }]
                    }
                }
        except Exception as e:
            import traceback
            print(f"Chart data preparation error: {traceback.format_exc()}")
            chart_data = {}
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            test_type = data.get('test_type', 'z-test')
            tail_type = data.get('tail_type', 'two-tailed')
            
            if test_type == 'z-test':
                z_score, error = self._validate_number(data.get('z_score'), 'Z-score', allow_zero=True)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                p_value, error = self._calculate_z_test_pvalue(z_score, tail_type)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('z-test', z_score, p_value, tail_type=tail_type)
                chart_data = self._prepare_chart_data('z-test', z_score, p_value)
                
                response = {
                    'success': True,
                    'test_type': test_type,
                    'z_score': z_score,
                    'tail_type': tail_type,
                    'p_value': p_value,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            elif test_type == 't-test':
                t_score, error = self._validate_number(data.get('t_score'), 't-score', allow_zero=True)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                df, error = self._validate_number(data.get('df'), 'Degrees of freedom')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                p_value, error = self._calculate_t_test_pvalue(t_score, df, tail_type)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('t-test', t_score, p_value, df=df, tail_type=tail_type)
                chart_data = self._prepare_chart_data('t-test', t_score, p_value, df=df)
                
                response = {
                    'success': True,
                    'test_type': test_type,
                    't_score': t_score,
                    'df': df,
                    'tail_type': tail_type,
                    'p_value': p_value,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            elif test_type == 'chi-square':
                chi_square, error = self._validate_number(data.get('chi_square'), 'Chi-square statistic')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                df, error = self._validate_number(data.get('df'), 'Degrees of freedom')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                p_value, error = self._calculate_chi_square_pvalue(chi_square, df)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('chi-square', chi_square, p_value, df=df)
                chart_data = {}
                
                response = {
                    'success': True,
                    'test_type': test_type,
                    'chi_square': chi_square,
                    'df': df,
                    'p_value': p_value,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            elif test_type == 'f-test':
                f_score, error = self._validate_number(data.get('f_score'), 'F-statistic')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                df1, error = self._validate_number(data.get('df1'), 'Degrees of freedom (df1)')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                df2, error = self._validate_number(data.get('df2'), 'Degrees of freedom (df2)')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                p_value, error = self._calculate_f_test_pvalue(f_score, df1, df2)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('f-test', f_score, p_value, df1=df1, df2=df2)
                chart_data = {}
                
                response = {
                    'success': True,
                    'test_type': test_type,
                    'f_score': f_score,
                    'df1': df1,
                    'df2': df2,
                    'p_value': p_value,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid test type.'}, status=400)
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"P-Value Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
