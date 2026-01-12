from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
from datetime import datetime, timedelta
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PeriodCalculator(View):
    """
    Class-based view for Period Calculator
    Predicts next period dates and cycle tracking.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/period_calculator.html'
    
    # Constants using SymPy Float for precision
    STANDARD_LUTEAL_PHASE = Float('14', 15)  # Days
    FERTILE_WINDOW_BEFORE = Float('5', 15)  # Days before ovulation
    FERTILE_WINDOW_AFTER = Float('1', 15)  # Days after ovulation
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Period Calculator',
            'page_title': 'Period Calculator - Menstrual Cycle Tracker',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            last_period_str = data.get('last_period')
            cycle_length = int(data.get('cycle_length', 28))
            period_length = int(data.get('period_length', 5))
            
            try:
                last_period = datetime.strptime(last_period_str, '%Y-%m-%d')
            except:
                return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
            
            # Validation using NumPy
            cycle_length_array = np.array([cycle_length])
            period_length_array = np.array([period_length])
            
            if np.any(cycle_length_array < 21) or np.any(cycle_length_array > 35):
                return JsonResponse({'success': False, 'error': 'Cycle length should be between 21 and 35 days.'}, status=400)
            if np.any(period_length_array < 2) or np.any(period_length_array > 7):
                return JsonResponse({'success': False, 'error': 'Period length should be between 2 and 7 days.'}, status=400)
            
            # Check if date is not in the future
            if last_period > datetime.now():
                return JsonResponse({'success': False, 'error': 'Last period date cannot be in the future.'}, status=400)
            
            # Calculate next period dates using SymPy
            cycle_length_sympy = Float(cycle_length, 15)
            period_length_sympy = Float(period_length, 15)
            
            next_period_start = last_period + timedelta(days=int(float(N(cycle_length_sympy, 10))))
            next_period_end = next_period_start + timedelta(days=int(float(N(period_length_sympy - Float('1', 15), 10))))
            
            # Ovulation date (typically 14 days before next period) using SymPy
            ovulation_date = next_period_start - timedelta(days=int(float(N(self.STANDARD_LUTEAL_PHASE, 10))))
            
            # Fertile window using SymPy
            fertile_start = ovulation_date - timedelta(days=int(float(N(self.FERTILE_WINDOW_BEFORE, 10))))
            fertile_end = ovulation_date + timedelta(days=int(float(N(self.FERTILE_WINDOW_AFTER, 10))))
            
            # Calculate current cycle day
            today = datetime.now().date()
            last_period_date_only = last_period.date()
            days_since_last_period = (today - last_period_date_only).days + 1
            current_cycle_day = days_since_last_period if days_since_last_period <= cycle_length else 0
            
            # Determine current cycle phase
            cycle_phase, phase_color, phase_description = self.get_cycle_phase(
                today, last_period_date_only, next_period_start.date(), ovulation_date.date(), fertile_start.date(), fertile_end.date(), period_length
            )
            
            # Calculate next 3 cycles
            cycles = []
            current_date = last_period
            for i in range(3):
                cycle_start = current_date + timedelta(days=int(float(N(cycle_length_sympy * Float(i, 15), 10))))
                cycle_end = cycle_start + timedelta(days=int(float(N(period_length_sympy - Float('1', 15), 10))))
                ov_date = cycle_start + timedelta(days=int(float(N(cycle_length_sympy - self.STANDARD_LUTEAL_PHASE, 10))))
                fert_start = ov_date - timedelta(days=int(float(N(self.FERTILE_WINDOW_BEFORE, 10))))
                fert_end = ov_date + timedelta(days=int(float(N(self.FERTILE_WINDOW_AFTER, 10))))
                
                cycles.append({
                    'cycle_number': i + 1,
                    'period_start': cycle_start.strftime('%Y-%m-%d'),
                    'period_end': cycle_end.strftime('%Y-%m-%d'),
                    'period_start_display': cycle_start.strftime('%B %d, %Y'),
                    'period_end_display': cycle_end.strftime('%B %d, %Y'),
                    'ovulation_date': ov_date.strftime('%Y-%m-%d'),
                    'ovulation_date_display': ov_date.strftime('%B %d, %Y'),
                    'fertile_start': fert_start.strftime('%Y-%m-%d'),
                    'fertile_end': fert_end.strftime('%Y-%m-%d'),
                    'fertile_start_display': fert_start.strftime('%B %d, %Y'),
                    'fertile_end_display': fert_end.strftime('%B %d, %Y')
                })
            
            # Calculate days until next period
            if next_period_start.date() >= today:
                days_until_period = (next_period_start.date() - today).days
            else:
                days_until_period = 0
            
            # Calculate days until ovulation
            if ovulation_date.date() >= today:
                days_until_ovulation = (ovulation_date.date() - today).days
            else:
                days_until_ovulation = 0
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                cycles=cycles,
                cycle_length=cycle_length,
                period_length=period_length,
                phase_color=phase_color
            )
            
            # Get color info
            color_info = self.get_color_info(phase_color)
            
            result = {
                'success': True,
                'last_period': last_period.strftime('%Y-%m-%d'),
                'last_period_display': last_period.strftime('%B %d, %Y'),
                'cycle_length': cycle_length,
                'period_length': period_length,
                'next_period': {
                    'start': next_period_start.strftime('%Y-%m-%d'),
                    'end': next_period_end.strftime('%Y-%m-%d'),
                    'start_display': next_period_start.strftime('%B %d, %Y'),
                    'end_display': next_period_end.strftime('%B %d, %Y')
                },
                'ovulation_date': ovulation_date.strftime('%Y-%m-%d'),
                'ovulation_date_display': ovulation_date.strftime('%B %d, %Y'),
                'fertile_window': {
                    'start': fertile_start.strftime('%Y-%m-%d'),
                    'end': fertile_end.strftime('%Y-%m-%d'),
                    'start_display': fertile_start.strftime('%B %d, %Y'),
                    'end_display': fertile_end.strftime('%B %d, %Y'),
                    'duration': int(float(N(self.FERTILE_WINDOW_BEFORE + self.FERTILE_WINDOW_AFTER + Float('1', 15), 10)))
                },
                'cycles': cycles,
                'statistics': {
                    'current_cycle_day': current_cycle_day,
                    'days_until_period': days_until_period,
                    'days_until_ovulation': days_until_ovulation,
                    'cycle_progress': round((current_cycle_day / cycle_length) * 100, 1) if current_cycle_day > 0 else 0
                },
                'cycle_phase': cycle_phase,
                'phase_color': phase_color,
                'phase_description': phase_description,
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Period Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_cycle_phase(self, today, last_period, next_period, ovulation_date, fertile_start, fertile_end, period_length):
        """Determine current cycle phase"""
        if today < last_period:
            return 'Unknown', 'gray', 'Please enter a valid last period date.'
        elif today == last_period:
            return 'Menstruation', 'red', 'You are currently in your menstrual phase.'
        elif today <= last_period + timedelta(days=period_length - 1):
            return 'Menstruation', 'red', 'You are currently in your menstrual phase.'
        elif today < fertile_start:
            return 'Follicular Phase', 'blue', 'You are in the follicular phase. Ovulation is approaching.'
        elif today == ovulation_date:
            return 'Ovulation Day', 'pink', 'Today is your predicted ovulation day! This is your most fertile day.'
        elif fertile_start <= today <= fertile_end:
            return 'Fertile Window', 'pink', 'You are in your fertile window. This is the best time for conception.'
        elif today < next_period:
            return 'Luteal Phase', 'purple', 'You are in the luteal phase. Your next period is approaching.'
        else:
            return 'Next Cycle', 'gray', 'Your next cycle should begin soon.'
    
    def get_color_info(self, category_color):
        """Get color information for the category"""
        color_map = {
            'red': {
                'hex': '#ef4444',
                'rgb': 'rgb(239, 68, 68)',
                'tailwind_classes': 'bg-red-100 text-red-800 border-red-300'
            },
            'blue': {
                'hex': '#3b82f6',
                'rgb': 'rgb(59, 130, 246)',
                'tailwind_classes': 'bg-blue-100 text-blue-800 border-blue-300'
            },
            'pink': {
                'hex': '#ec4899',
                'rgb': 'rgb(236, 72, 153)',
                'tailwind_classes': 'bg-pink-100 text-pink-800 border-pink-300'
            },
            'purple': {
                'hex': '#a855f7',
                'rgb': 'rgb(168, 85, 247)',
                'tailwind_classes': 'bg-purple-100 text-purple-800 border-purple-300'
            },
            'gray': {
                'hex': '#6b7280',
                'rgb': 'rgb(107, 114, 128)',
                'tailwind_classes': 'bg-gray-100 text-gray-800 border-gray-300'
            }
        }
        return color_map.get(category_color, color_map['pink'])
    
    def prepare_chart_data(self, cycles, cycle_length, period_length, phase_color):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(phase_color)
        
        # Cycle Timeline Chart
        cycle_labels = [f"Cycle {c['cycle_number']}" for c in cycles]
        cycle_data = []
        cycle_colors = []
        
        for cycle in cycles:
            # Calculate days in each phase
            period_days = period_length
            follicular_days = cycle_length - period_length - 14 - 5  # Approximate
            fertile_days = 7  # 5 before + 1 ovulation + 1 after
            luteal_days = 14
            
            cycle_data.append({
                'period': period_days,
                'follicular': follicular_days,
                'fertile': fertile_days,
                'luteal': luteal_days
            })
        
        # Phase Distribution Chart
        phase_distribution_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Menstruation', 'Follicular', 'Fertile', 'Luteal'],
                'datasets': [{
                    'data': [
                        period_length,
                        max(1, cycle_length - period_length - 14 - 6),
                        7,
                        14
                    ],
                    'backgroundColor': ['#ef4444', '#3b82f6', '#ec4899', '#a855f7'],
                    'borderWidth': 2,
                    'borderColor': '#ffffff'
                }]
            },
            'center_text': {
                'value': cycle_length,
                'label': 'Days',
                'color': color_info['hex']
            }
        }
        
        # Cycle Calendar Chart
        cycle_calendar_data = []
        for cycle in cycles:
            cycle_calendar_data.append({
                'cycle': f"Cycle {cycle['cycle_number']}",
                'period_start': cycle['period_start'],
                'ovulation': cycle['ovulation_date'],
                'fertile_start': cycle['fertile_start'],
                'fertile_end': cycle['fertile_end']
            })
        
        cycle_calendar_chart = {
            'type': 'bar',
            'data': {
                'labels': [f"Cycle {c['cycle_number']}" for c in cycles],
                'datasets': [
                    {
                        'label': 'Period Days',
                        'data': [period_length] * len(cycles),
                        'backgroundColor': '#ef4444',
                        'borderColor': '#dc2626',
                        'borderWidth': 2
                    },
                    {
                        'label': 'Fertile Window',
                        'data': [7] * len(cycles),
                        'backgroundColor': '#ec4899',
                        'borderColor': '#db2777',
                        'borderWidth': 2
                    }
                ]
            }
        }
        
        # Cycle Progress Chart
        cycle_progress_chart = {
            'type': 'line',
            'data': {
                'labels': [f"Cycle {c['cycle_number']}" for c in cycles],
                'datasets': [{
                    'label': 'Cycle Length',
                    'data': [cycle_length] * len(cycles),
                    'borderColor': color_info['hex'],
                    'backgroundColor': color_info['hex'] + '20',
                    'borderWidth': 3,
                    'fill': True,
                    'tension': 0.4,
                    'pointRadius': 5,
                    'pointHoverRadius': 7
                }]
            }
        }
        
        return {
            'phase_distribution_chart': phase_distribution_chart,
            'cycle_calendar_chart': cycle_calendar_chart,
            'cycle_progress_chart': cycle_progress_chart
        }
