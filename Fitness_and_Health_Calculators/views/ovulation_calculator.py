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
class OvulationCalculator(View):
    """
    Class-based view for Ovulation Calculator
    Calculates ovulation date and fertile window based on menstrual cycle.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/ovulation_calculator.html'
    
    # Constants using SymPy Float for precision
    STANDARD_LUTEAL_PHASE = Float('14', 15)  # Days
    FERTILE_WINDOW_BEFORE = Float('5', 15)  # Days before ovulation
    FERTILE_WINDOW_AFTER = Float('1', 15)  # Days after ovulation
    MENSTRUATION_DAYS = Float('5', 15)  # Typical menstruation duration
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Ovulation Calculator',
            'page_title': 'Ovulation Calculator - Calculate Fertile Window',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            last_period = data.get('last_period')
            cycle_length = int(data.get('cycle_length', 28))
            
            # Parse date
            try:
                last_period_date = datetime.strptime(last_period, '%Y-%m-%d')
            except:
                return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
            
            # Validation using NumPy
            cycle_length_array = np.array([cycle_length])
            if np.any(cycle_length_array < 21) or np.any(cycle_length_array > 35):
                return JsonResponse({'success': False, 'error': 'Cycle length should be between 21 and 35 days.'}, status=400)
            
            # Check if date is not in the future
            if last_period_date > datetime.now():
                return JsonResponse({'success': False, 'error': 'Last period date cannot be in the future.'}, status=400)
            
            # Calculate ovulation day using SymPy for precision
            cycle_length_sympy = Float(cycle_length, 15)
            ovulation_day = float(N(cycle_length_sympy - self.STANDARD_LUTEAL_PHASE, 10))
            
            # Calculate dates
            ovulation_date = last_period_date + timedelta(days=int(ovulation_day))
            next_period_date = last_period_date + timedelta(days=cycle_length)
            
            # Fertile window calculation using SymPy
            fertile_start = ovulation_date - timedelta(days=int(float(N(self.FERTILE_WINDOW_BEFORE, 10))))
            fertile_end = ovulation_date + timedelta(days=int(float(N(self.FERTILE_WINDOW_AFTER, 10))))
            
            # Calculate cycle phases with enhanced detection
            cycle_calendar = []
            phase_counts = {
                'menstruation': 0,
                'follicular': 0,
                'fertile': 0,
                'ovulation': 0,
                'luteal': 0
            }
            
            for i in range(cycle_length):
                day_date = last_period_date + timedelta(days=i)
                day_num = i + 1
                
                # Determine phase with enhanced logic
                if day_num <= int(float(N(self.MENSTRUATION_DAYS, 10))):
                    phase = 'menstruation'
                elif day_date < fertile_start:
                    phase = 'follicular'
                elif day_date == ovulation_date:
                    phase = 'ovulation'
                elif fertile_start <= day_date <= fertile_end:
                    phase = 'fertile'
                else:
                    phase = 'luteal'
                
                phase_counts[phase] += 1
                
                cycle_calendar.append({
                    'day': day_num,
                    'date': day_date.strftime('%Y-%m-%d'),
                    'date_display': day_date.strftime('%B %d, %Y'),
                    'day_name': day_date.strftime('%A'),
                    'phase': phase,
                    'is_ovulation': day_date == ovulation_date,
                    'is_fertile': fertile_start <= day_date <= fertile_end,
                    'is_menstruation': day_num <= int(float(N(self.MENSTRUATION_DAYS, 10)))
                })
            
            # Calculate days until ovulation
            today = datetime.now().date()
            last_period_date_only = last_period_date.date()
            ovulation_date_only = ovulation_date.date()
            
            if ovulation_date_only >= today:
                days_until_ovulation = (ovulation_date_only - today).days
                ovulation_status = 'upcoming' if days_until_ovulation > 0 else 'today'
            else:
                days_until_ovulation = (today - ovulation_date_only).days
                ovulation_status = 'past'
            
            # Calculate days until next period
            next_period_date_only = next_period_date.date()
            if next_period_date_only >= today:
                days_until_period = (next_period_date_only - today).days
            else:
                days_until_period = 0
            
            # Determine cycle phase category
            cycle_phase_category, cycle_phase_color, cycle_phase_description = self.get_cycle_phase_category(
                today, last_period_date_only, ovulation_date_only, next_period_date_only, fertile_start.date(), fertile_end.date()
            )
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                cycle_calendar=cycle_calendar,
                cycle_length=cycle_length,
                phase_counts=phase_counts,
                ovulation_date=ovulation_date,
                fertile_start=fertile_start,
                fertile_end=fertile_end,
                cycle_phase_color=cycle_phase_color
            )
            
            # Get color info
            color_info = self.get_color_info(cycle_phase_color)
            
            result = {
                'success': True,
                'last_period': last_period_date.strftime('%Y-%m-%d'),
                'last_period_display': last_period_date.strftime('%B %d, %Y'),
                'cycle_length': cycle_length,
                'ovulation_date': ovulation_date.strftime('%Y-%m-%d'),
                'ovulation_date_display': ovulation_date.strftime('%B %d, %Y'),
                'fertile_window': {
                    'start': fertile_start.strftime('%Y-%m-%d'),
                    'end': fertile_end.strftime('%Y-%m-%d'),
                    'start_display': fertile_start.strftime('%B %d, %Y'),
                    'end_display': fertile_end.strftime('%B %d, %Y'),
                    'duration': int(float(N(self.FERTILE_WINDOW_BEFORE + self.FERTILE_WINDOW_AFTER + Float('1', 15), 10)))
                },
                'next_period': next_period_date.strftime('%Y-%m-%d'),
                'next_period_display': next_period_date.strftime('%B %d, %Y'),
                'cycle_calendar': cycle_calendar,
                'phase_counts': phase_counts,
                'statistics': {
                    'days_until_ovulation': days_until_ovulation,
                    'days_until_period': days_until_period,
                    'ovulation_status': ovulation_status,
                    'cycle_day': (today - last_period_date_only).days + 1 if today >= last_period_date_only else 0,
                    'fertile_window_duration': int(float(N(self.FERTILE_WINDOW_BEFORE + self.FERTILE_WINDOW_AFTER + Float('1', 15), 10)))
                },
                'cycle_phase_category': cycle_phase_category,
                'cycle_phase_color': cycle_phase_color,
                'cycle_phase_description': cycle_phase_description,
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Ovulation Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_cycle_phase_category(self, today, last_period, ovulation_date, next_period, fertile_start, fertile_end):
        """Determine current cycle phase category"""
        if today < last_period:
            return 'Unknown', 'gray', 'Please enter a valid last period date.'
        elif today == last_period:
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
    
    def prepare_chart_data(self, cycle_calendar, cycle_length, phase_counts, ovulation_date, fertile_start, fertile_end, cycle_phase_color):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(cycle_phase_color)
        
        # Phase Distribution Chart
        phase_colors = {
            'menstruation': '#ef4444',
            'follicular': '#3b82f6',
            'fertile': '#ec4899',
            'ovulation': '#f472b6',
            'luteal': '#a855f7'
        }
        
        phase_distribution_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Menstruation', 'Follicular', 'Fertile', 'Ovulation', 'Luteal'],
                'datasets': [{
                    'data': [
                        phase_counts['menstruation'],
                        phase_counts['follicular'],
                        phase_counts['fertile'],
                        phase_counts['ovulation'],
                        phase_counts['luteal']
                    ],
                    'backgroundColor': [
                        phase_colors['menstruation'],
                        phase_colors['follicular'],
                        phase_colors['fertile'],
                        phase_colors['ovulation'],
                        phase_colors['luteal']
                    ],
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
        
        # Cycle Timeline Chart
        timeline_data = []
        timeline_colors = []
        timeline_labels = []
        
        for day_info in cycle_calendar:
            phase = day_info['phase']
            timeline_data.append(1)  # Each day gets equal space
            timeline_colors.append(phase_colors.get(phase, '#e5e7eb'))
            # Only label key days
            if day_info['is_ovulation']:
                timeline_labels.append('Ov')
            elif day_info['day'] == 1:
                timeline_labels.append('1')
            elif day_info['day'] == cycle_length:
                timeline_labels.append(str(cycle_length))
            else:
                timeline_labels.append('')
        
        cycle_timeline_chart = {
            'type': 'bar',
            'data': {
                'labels': [str(d['day']) for d in cycle_calendar],
                'datasets': [{
                    'label': 'Cycle Days',
                    'data': timeline_data,
                    'backgroundColor': timeline_colors,
                    'borderColor': timeline_colors,
                    'borderWidth': 1,
                    'barThickness': 'flex',
                    'maxBarThickness': 20
                }]
            }
        }
        
        # Fertility Probability Chart (estimated)
        fertility_probability = []
        for day_info in cycle_calendar:
            if day_info['is_ovulation']:
                fertility_probability.append(100)  # Peak fertility
            elif day_info['is_fertile']:
                # Decreasing probability as we move away from ovulation
                days_from_ovulation = abs(day_info['day'] - (cycle_length - 14))
                if days_from_ovulation == 0:
                    fertility_probability.append(100)
                elif days_from_ovulation == 1:
                    fertility_probability.append(80)
                elif days_from_ovulation == 2:
                    fertility_probability.append(60)
                elif days_from_ovulation == 3:
                    fertility_probability.append(40)
                elif days_from_ovulation == 4:
                    fertility_probability.append(20)
                elif days_from_ovulation == 5:
                    fertility_probability.append(10)
                else:
                    fertility_probability.append(5)
            else:
                fertility_probability.append(0)
        
        fertility_chart = {
            'type': 'line',
            'data': {
                'labels': [str(d['day']) for d in cycle_calendar],
                'datasets': [{
                    'label': 'Fertility Probability (%)',
                    'data': fertility_probability,
                    'borderColor': '#ec4899',
                    'backgroundColor': '#ec489920',
                    'borderWidth': 3,
                    'fill': True,
                    'tension': 0.4,
                    'pointRadius': 3,
                    'pointHoverRadius': 5
                }]
            }
        }
        
        return {
            'phase_distribution_chart': phase_distribution_chart,
            'cycle_timeline_chart': cycle_timeline_chart,
            'fertility_chart': fertility_chart
        }
