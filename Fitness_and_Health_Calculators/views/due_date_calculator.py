from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
from datetime import datetime, timedelta


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DueDateCalculator(View):
    """
    Class-based view for Due Date Calculator
    Calculates due date based on last menstrual period or conception date.
    Enhanced with chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/due_date_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Due Date Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            calc_type = data.get('calc_type', 'from_lmp')
            
            if calc_type == 'from_lmp':
                lmp_str = data.get('lmp')
                cycle_length = int(data.get('cycle_length', 28))
                
                if cycle_length < 21 or cycle_length > 35:
                    return JsonResponse({'success': False, 'error': 'Cycle length must be between 21 and 35 days.'}, status=400)
                
                try:
                    lmp = datetime.strptime(lmp_str, '%Y-%m-%d')
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
                
                # Naegele's rule: Add 1 year, subtract 3 months, add 7 days
                # Simplified: Add 280 days (40 weeks)
                due_date = lmp + timedelta(days=280)
                
                # Conception date is typically 14 days after LMP (or cycle_length - 14)
                conception_date = lmp + timedelta(days=cycle_length - 14)
                
            elif calc_type == 'from_conception':
                conception_str = data.get('conception_date')
                
                try:
                    conception_date = datetime.strptime(conception_str, '%Y-%m-%d')
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
                
                # Due date is 266 days from conception
                due_date = conception_date + timedelta(days=266)
                lmp = conception_date - timedelta(days=14)
            
            # Calculate current status
            today = datetime.now()
            days_passed = (today - lmp).days if today > lmp else 0
            weeks_pregnant = days_passed // 7
            days_remaining = (due_date - today).days if due_date > today else 0
            weeks_remaining = days_remaining // 7
            
            # Trimester
            if weeks_pregnant < 13:
                trimester = 1
                trimester_name = 'First'
                trimester_color = 'blue'
            elif weeks_pregnant < 27:
                trimester = 2
                trimester_name = 'Second'
                trimester_color = 'green'
            else:
                trimester = 3
                trimester_name = 'Third'
                trimester_color = 'orange'
            
            # Calculate pregnancy progress percentage
            total_days = 280  # 40 weeks
            progress_percentage = min((days_passed / total_days) * 100, 100) if days_passed > 0 else 0
            
            # Milestones
            milestones = {
                'first_trimester_end': lmp + timedelta(days=91),  # 13 weeks
                'second_trimester_end': lmp + timedelta(days=189),  # 27 weeks
                'viability_week': lmp + timedelta(days=168),  # 24 weeks
                'full_term': lmp + timedelta(days=259),  # 37 weeks
                'conception_window_start': conception_date - timedelta(days=5),
                'conception_window_end': conception_date + timedelta(days=1)
            }
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                weeks_pregnant=weeks_pregnant,
                days_pregnant=days_passed,
                progress_percentage=progress_percentage,
                trimester=trimester,
                trimester_color=trimester_color,
                lmp=lmp,
                conception_date=conception_date,
                due_date=due_date,
                days_remaining=days_remaining
            )
            
            # Get color info
            color_info = self.get_color_info(trimester_color)
            
            result = {
                'success': True,
                'calc_type': calc_type,
                'lmp': lmp.strftime('%Y-%m-%d'),
                'conception_date': conception_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'weeks_pregnant': weeks_pregnant,
                'days_pregnant': days_passed,
                'days_remaining': days_remaining,
                'weeks_remaining': weeks_remaining,
                'trimester': trimester,
                'trimester_name': trimester_name,
                'trimester_color': trimester_color,
                'progress_percentage': round(progress_percentage, 1),
                'milestones': {k: v.strftime('%Y-%m-%d') for k, v in milestones.items()},
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Due Date Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_color_info(self, trimester_color):
        """Get color information for the trimester"""
        color_map = {
            'blue': {
                'hex': '#3b82f6',
                'rgb': 'rgb(59, 130, 246)',
                'tailwind_classes': 'bg-blue-100 text-blue-800 border-blue-300'
            },
            'green': {
                'hex': '#10b981',
                'rgb': 'rgb(16, 185, 129)',
                'tailwind_classes': 'bg-green-100 text-green-800 border-green-300'
            },
            'orange': {
                'hex': '#f97316',
                'rgb': 'rgb(249, 115, 22)',
                'tailwind_classes': 'bg-orange-100 text-orange-800 border-orange-300'
            }
        }
        return color_map.get(trimester_color, color_map['blue'])
    
    def prepare_chart_data(self, weeks_pregnant, days_pregnant, progress_percentage, trimester, trimester_color, lmp, conception_date, due_date, days_remaining):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(trimester_color)
        
        # Pregnancy Progress Chart
        progress_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Completed', 'Remaining'],
                'datasets': [{
                    'data': [round(progress_percentage, 1), round(100 - progress_percentage, 1)],
                    'backgroundColor': [color_info['hex'], '#e5e7eb'],
                    'borderColor': [color_info['hex'], '#d1d5db'],
                    'borderWidth': 2
                }]
            }
        }
        
        # Trimester Distribution Chart
        trimester_data = [0, 0, 0]
        trimester_colors = ['#e5e7eb', '#e5e7eb', '#e5e7eb']
        
        if trimester == 1:
            trimester_data = [100, 0, 0]
            trimester_colors = ['#3b82f6', '#e5e7eb', '#e5e7eb']
        elif trimester == 2:
            trimester_data = [0, 100, 0]
            trimester_colors = ['#e5e7eb', '#10b981', '#e5e7eb']
        else:
            trimester_data = [0, 0, 100]
            trimester_colors = ['#e5e7eb', '#e5e7eb', '#f97316']
        
        trimester_chart = {
            'type': 'bar',
            'data': {
                'labels': ['First Trimester', 'Second Trimester', 'Third Trimester'],
                'datasets': [{
                    'label': 'Current Trimester',
                    'data': trimester_data,
                    'backgroundColor': trimester_colors,
                    'borderColor': ['#2563eb', '#059669', '#ea580c'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Timeline Chart (weeks progression)
        weeks_labels = []
        weeks_data = []
        weeks_colors = []
        
        for week in range(0, 41, 5):  # Every 5 weeks
            weeks_labels.append(f'Week {week}')
            if week <= weeks_pregnant:
                weeks_data.append(100)
                weeks_colors.append(color_info['hex'])
            else:
                weeks_data.append(0)
                weeks_colors.append('#e5e7eb')
        
        timeline_chart = {
            'type': 'bar',
            'data': {
                'labels': weeks_labels,
                'datasets': [{
                    'label': 'Progress',
                    'data': weeks_data,
                    'backgroundColor': weeks_colors,
                    'borderColor': color_info['hex'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Countdown Chart (days remaining)
        countdown_data = []
        countdown_labels = []
        
        if days_remaining > 0:
            weeks_remaining = days_remaining // 7
            days_in_week = days_remaining % 7
            
            countdown_labels = ['Weeks Remaining', 'Days Remaining']
            countdown_data = [weeks_remaining, days_in_week]
        else:
            countdown_labels = ['Overdue', 'Days Overdue']
            countdown_data = [0, abs(days_remaining)]
        
        countdown_chart = {
            'type': 'bar',
            'data': {
                'labels': countdown_labels,
                'datasets': [{
                    'label': 'Time',
                    'data': countdown_data,
                    'backgroundColor': [color_info['hex'], '#8b5cf6'],
                    'borderColor': [color_info['hex'], '#7c3aed'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'progress_chart': progress_chart,
            'trimester_chart': trimester_chart,
            'timeline_chart': timeline_chart,
            'countdown_chart': countdown_chart
        }
