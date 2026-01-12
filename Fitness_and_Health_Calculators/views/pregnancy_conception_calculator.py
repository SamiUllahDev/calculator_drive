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
class PregnancyConceptionCalculator(View):
    """
    Class-based view for Pregnancy Conception Calculator
    Calculates conception date and pregnancy timeline.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/pregnancy_conception_calculator.html'
    
    # Constants using SymPy Float for precision
    STANDARD_PREGNANCY_DAYS = Float('280', 15)  # Days from LMP to due date
    CONCEPTION_TO_DUE_DAYS = Float('266', 15)  # Days from conception to due date
    LMP_TO_CONCEPTION_DAYS = Float('14', 15)  # Days from LMP to conception (approximate)
    DAYS_PER_WEEK = Float('7', 15)
    FERTILE_WINDOW_BEFORE = Float('5', 15)  # Days before ovulation
    FERTILE_WINDOW_AFTER = Float('1', 15)  # Days after ovulation
    IMPLANTATION_START_DAYS = Float('6', 15)  # Days after conception
    IMPLANTATION_END_DAYS = Float('12', 15)  # Days after conception
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Pregnancy Conception Calculator',
            'page_title': 'Pregnancy Conception Calculator - Calculate Conception Date',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            calc_type = data.get('calc_type', 'from_due_date')
            
            if calc_type == 'from_due_date':
                due_date_str = data.get('due_date')
                
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
                
                # Conception typically occurs 266 days before due date using SymPy
                conception_date = due_date - timedelta(days=int(float(N(self.CONCEPTION_TO_DUE_DAYS, 10))))
                lmp = conception_date - timedelta(days=int(float(N(self.LMP_TO_CONCEPTION_DAYS, 10))))
                
            elif calc_type == 'from_lmp':
                lmp_str = data.get('lmp')
                cycle_length = int(data.get('cycle_length', 28))
                
                try:
                    lmp = datetime.strptime(lmp_str, '%Y-%m-%d')
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
                
                # Validation using NumPy
                cycle_length_array = np.array([cycle_length])
                if np.any(cycle_length_array < 21) or np.any(cycle_length_array > 35):
                    return JsonResponse({'success': False, 'error': 'Cycle length should be between 21 and 35 days.'}, status=400)
                
                # Ovulation (conception window) is typically 14 days before next period using SymPy
                cycle_length_sympy = Float(cycle_length, 15)
                ovulation_day = int(float(N(cycle_length_sympy - self.LMP_TO_CONCEPTION_DAYS, 10)))
                conception_date = lmp + timedelta(days=ovulation_day)
                due_date = lmp + timedelta(days=int(float(N(self.STANDARD_PREGNANCY_DAYS, 10))))
                
            elif calc_type == 'from_conception':
                conception_str = data.get('conception_date')
                
                try:
                    conception_date = datetime.strptime(conception_str, '%Y-%m-%d')
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
                
                lmp = conception_date - timedelta(days=int(float(N(self.LMP_TO_CONCEPTION_DAYS, 10))))
                due_date = conception_date + timedelta(days=int(float(N(self.CONCEPTION_TO_DUE_DAYS, 10))))
            
            # Calculate current status using SymPy
            today = datetime.now()
            conception_date_only = conception_date.date()
            today_date_only = today.date()
            lmp_date_only = lmp.date()
            
            days_since_conception = (today_date_only - conception_date_only).days if today_date_only > conception_date_only else 0
            days_pregnant = (today_date_only - lmp_date_only).days if today_date_only > lmp_date_only else 0
            
            # Calculate weeks using SymPy
            days_since_conception_sympy = Float(days_since_conception, 15)
            days_pregnant_sympy = Float(days_pregnant, 15)
            
            weeks_since_conception = int(float(N(days_since_conception_sympy / self.DAYS_PER_WEEK, 10)))
            weeks_pregnant = int(float(N(days_pregnant_sympy / self.DAYS_PER_WEEK, 10)))
            
            # Fertile window using SymPy
            ovulation_date = conception_date
            fertile_start = ovulation_date - timedelta(days=int(float(N(self.FERTILE_WINDOW_BEFORE, 10))))
            fertile_end = ovulation_date + timedelta(days=int(float(N(self.FERTILE_WINDOW_AFTER, 10))))
            
            # Implantation window using SymPy
            implantation_start = conception_date + timedelta(days=int(float(N(self.IMPLANTATION_START_DAYS, 10))))
            implantation_end = conception_date + timedelta(days=int(float(N(self.IMPLANTATION_END_DAYS, 10))))
            
            # Trimester calculation
            trimester, trimester_name, trimester_color, trimester_description = self.get_trimester(weeks_pregnant)
            
            # Calculate days until due date
            due_date_only = due_date.date()
            if due_date_only >= today_date_only:
                days_until_due = (due_date_only - today_date_only).days
            else:
                days_until_due = 0
            
            # Calculate pregnancy progress
            total_pregnancy_days = int(float(N(self.STANDARD_PREGNANCY_DAYS, 10)))
            progress_percentage = min(100, round((days_pregnant / total_pregnancy_days) * 100, 1)) if days_pregnant > 0 else 0
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                weeks_pregnant=weeks_pregnant,
                weeks_since_conception=weeks_since_conception,
                days_pregnant=days_pregnant,
                days_since_conception=days_since_conception,
                progress_percentage=progress_percentage,
                trimester=trimester,
                trimester_color=trimester_color,
                fertile_start=fertile_start,
                fertile_end=fertile_end,
                implantation_start=implantation_start,
                implantation_end=implantation_end
            )
            
            # Get color info
            color_info = self.get_color_info(trimester_color)
            
            result = {
                'success': True,
                'calc_type': calc_type,
                'lmp': lmp.strftime('%Y-%m-%d'),
                'lmp_display': lmp.strftime('%B %d, %Y'),
                'conception_date': conception_date.strftime('%Y-%m-%d'),
                'conception_date_display': conception_date.strftime('%B %d, %Y'),
                'ovulation_date': ovulation_date.strftime('%Y-%m-%d'),
                'ovulation_date_display': ovulation_date.strftime('%B %d, %Y'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'due_date_display': due_date.strftime('%B %d, %Y'),
                'fertile_window': {
                    'start': fertile_start.strftime('%Y-%m-%d'),
                    'end': fertile_end.strftime('%Y-%m-%d'),
                    'start_display': fertile_start.strftime('%B %d, %Y'),
                    'end_display': fertile_end.strftime('%B %d, %Y'),
                    'duration': int(float(N(self.FERTILE_WINDOW_BEFORE + self.FERTILE_WINDOW_AFTER + Float('1', 15), 10)))
                },
                'implantation_window': {
                    'start': implantation_start.strftime('%Y-%m-%d'),
                    'end': implantation_end.strftime('%Y-%m-%d'),
                    'start_display': implantation_start.strftime('%B %d, %Y'),
                    'end_display': implantation_end.strftime('%B %d, %Y'),
                    'duration': int(float(N(self.IMPLANTATION_END_DAYS - self.IMPLANTATION_START_DAYS + Float('1', 15), 10)))
                },
                'weeks_pregnant': weeks_pregnant,
                'days_pregnant': days_pregnant,
                'weeks_since_conception': weeks_since_conception,
                'days_since_conception': days_since_conception,
                'trimester': trimester,
                'trimester_name': trimester_name,
                'trimester_color': trimester_color,
                'trimester_description': trimester_description,
                'days_until_due': days_until_due,
                'progress_percentage': progress_percentage,
                'statistics': {
                    'weeks_pregnant': weeks_pregnant,
                    'weeks_since_conception': weeks_since_conception,
                    'days_pregnant': days_pregnant,
                    'days_since_conception': days_since_conception,
                    'progress_percentage': progress_percentage,
                    'days_until_due': days_until_due
                },
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Pregnancy Conception Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_trimester(self, weeks_pregnant):
        """Determine trimester with detailed information"""
        if weeks_pregnant < 13:
            return 1, 'First Trimester', 'pink', 'Early development phase. Baby\'s major organs and body systems are forming. Important time for prenatal care and folic acid.'
        elif weeks_pregnant < 27:
            return 2, 'Second Trimester', 'purple', 'Often called the "golden period." Baby is growing rapidly, and you may start feeling movement. Energy levels typically improve.'
        elif weeks_pregnant < 40:
            return 3, 'Third Trimester', 'blue', 'Final preparation phase. Baby is gaining weight and preparing for birth. Regular checkups become more frequent.'
        else:
            return 3, 'Full Term', 'green', 'Baby is full term and ready for birth. Any time now!'
    
    def get_color_info(self, category_color):
        """Get color information for the category"""
        color_map = {
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
            'blue': {
                'hex': '#3b82f6',
                'rgb': 'rgb(59, 130, 246)',
                'tailwind_classes': 'bg-blue-100 text-blue-800 border-blue-300'
            },
            'green': {
                'hex': '#10b981',
                'rgb': 'rgb(16, 185, 129)',
                'tailwind_classes': 'bg-green-100 text-green-800 border-green-300'
            }
        }
        return color_map.get(category_color, color_map['pink'])
    
    def prepare_chart_data(self, weeks_pregnant, weeks_since_conception, days_pregnant, days_since_conception, progress_percentage, trimester, trimester_color, fertile_start, fertile_end, implantation_start, implantation_end):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(trimester_color)
        
        # Conception Timeline Chart
        timeline_data = []
        timeline_labels = []
        timeline_colors = []
        
        # Add key dates to timeline
        dates = [
            {'label': 'LMP', 'date': fertile_start - timedelta(days=14), 'color': '#ef4444'},
            {'label': 'Fertile Start', 'date': fertile_start, 'color': '#10b981'},
            {'label': 'Ovulation', 'date': fertile_start + timedelta(days=5), 'color': '#3b82f6'},
            {'label': 'Conception', 'date': fertile_start + timedelta(days=5), 'color': '#ec4899'},
            {'label': 'Implant Start', 'date': implantation_start, 'color': '#a855f7'},
            {'label': 'Implant End', 'date': implantation_end, 'color': '#a855f7'}
        ]
        
        for item in dates:
            timeline_labels.append(item['label'])
            timeline_data.append(1)  # Equal spacing
            timeline_colors.append(item['color'])
        
        timeline_chart = {
            'type': 'bar',
            'data': {
                'labels': timeline_labels,
                'datasets': [{
                    'label': 'Timeline',
                    'data': timeline_data,
                    'backgroundColor': timeline_colors,
                    'borderColor': timeline_colors,
                    'borderWidth': 2,
                    'barThickness': 'flex',
                    'maxBarThickness': 30
                }]
            }
        }
        
        # Progress Gauge Chart
        progress_gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Progress', 'Remaining'],
                'datasets': [{
                    'data': [round(progress_percentage, 2), round(100 - progress_percentage, 2)],
                    'backgroundColor': [color_info['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': round(progress_percentage, 1),
                'label': '% Complete',
                'color': color_info['hex']
            }
        }
        
        # Weeks Comparison Chart
        weeks_comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Weeks Pregnant', 'Weeks Since Conception'],
                'datasets': [{
                    'label': 'Weeks',
                    'data': [weeks_pregnant, weeks_since_conception],
                    'backgroundColor': [color_info['hex'], '#10b981'],
                    'borderColor': [color_info['hex'], '#059669'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Trimester Progress Chart
        trimester_data = [0, 0, 0]
        if trimester == 1:
            trimester_data[0] = min(100, (weeks_pregnant / 13) * 100)
        elif trimester == 2:
            trimester_data[0] = 100
            trimester_data[1] = min(100, ((weeks_pregnant - 13) / 14) * 100)
        else:
            trimester_data[0] = 100
            trimester_data[1] = 100
            trimester_data[2] = min(100, ((weeks_pregnant - 27) / 13) * 100)
        
        trimester_chart = {
            'type': 'bar',
            'data': {
                'labels': ['1st Trimester', '2nd Trimester', '3rd Trimester'],
                'datasets': [{
                    'label': 'Progress (%)',
                    'data': [round(trimester_data[0], 1), round(trimester_data[1], 1), round(trimester_data[2], 1)],
                    'backgroundColor': ['#ec4899', '#a855f7', '#3b82f6'],
                    'borderColor': ['#db2777', '#9333ea', '#2563eb'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'timeline_chart': timeline_chart,
            'progress_gauge_chart': progress_gauge_chart,
            'weeks_comparison_chart': weeks_comparison_chart,
            'trimester_chart': trimester_chart
        }
