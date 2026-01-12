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
class PregnancyCalculator(View):
    """
    Class-based view for Pregnancy Calculator
    Comprehensive pregnancy tracking and calculations.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/pregnancy_calculator.html'
    
    # Constants using SymPy Float for precision
    STANDARD_PREGNANCY_DAYS = Float('280', 15)  # Days from LMP to due date
    CONCEPTION_TO_DUE_DAYS = Float('266', 15)  # Days from conception to due date
    LMP_TO_CONCEPTION_DAYS = Float('14', 15)  # Days from LMP to conception (approximate)
    DAYS_PER_WEEK = Float('7', 15)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Pregnancy Calculator',
            'page_title': 'Pregnancy Calculator - Comprehensive Pregnancy Tracker',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            calc_type = data.get('calc_type', 'from_lmp')
            
            if calc_type == 'from_lmp':
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
                
                # Calculate conception date using SymPy
                cycle_length_sympy = Float(cycle_length, 15)
                conception_date = lmp + timedelta(days=int(float(N(cycle_length_sympy - self.LMP_TO_CONCEPTION_DAYS, 10))))
                
                # Calculate due date using SymPy
                due_date = lmp + timedelta(days=int(float(N(self.STANDARD_PREGNANCY_DAYS, 10))))
                
            elif calc_type == 'from_conception':
                conception_str = data.get('conception_date')
                
                try:
                    conception_date = datetime.strptime(conception_str, '%Y-%m-%d')
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
                
                # Calculate due date using SymPy
                due_date = conception_date + timedelta(days=int(float(N(self.CONCEPTION_TO_DUE_DAYS, 10))))
                
                # Calculate LMP using SymPy
                lmp = conception_date - timedelta(days=int(float(N(self.LMP_TO_CONCEPTION_DAYS, 10))))
            
            elif calc_type == 'from_due_date':
                due_date_str = data.get('due_date')
                
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
                
                # Calculate conception date using SymPy
                conception_date = due_date - timedelta(days=int(float(N(self.CONCEPTION_TO_DUE_DAYS, 10))))
                
                # Calculate LMP using SymPy
                lmp = conception_date - timedelta(days=int(float(N(self.LMP_TO_CONCEPTION_DAYS, 10))))
            
            # Calculate current status using SymPy
            today = datetime.now()
            lmp_date_only = lmp.date()
            today_date_only = today.date()
            
            days_passed = (today_date_only - lmp_date_only).days if today_date_only > lmp_date_only else 0
            
            # Calculate weeks and days using SymPy
            days_passed_sympy = Float(days_passed, 15)
            weeks_pregnant = int(float(N(days_passed_sympy / self.DAYS_PER_WEEK, 10)))
            days_pregnant = int(float(N(days_passed_sympy % self.DAYS_PER_WEEK, 10)))
            
            # Calculate days remaining using SymPy
            due_date_only = due_date.date()
            if due_date_only >= today_date_only:
                days_remaining = (due_date_only - today_date_only).days
            else:
                days_remaining = 0
            
            # Trimester calculation
            trimester, trimester_name, trimester_color, trimester_description = self.get_trimester(weeks_pregnant)
            
            # Fetal development milestones
            milestones = self.get_milestones(weeks_pregnant, lmp)
            
            # Next appointments (typical schedule)
            appointments = self.get_appointments(weeks_pregnant, lmp)
            
            # Calculate pregnancy progress percentage
            total_pregnancy_days = int(float(N(self.STANDARD_PREGNANCY_DAYS, 10)))
            progress_percentage = min(100, round((days_passed / total_pregnancy_days) * 100, 1)) if days_passed > 0 else 0
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                weeks_pregnant=weeks_pregnant,
                days_passed=days_passed,
                days_remaining=days_remaining,
                progress_percentage=progress_percentage,
                trimester=trimester,
                trimester_color=trimester_color,
                milestones=milestones
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
                'due_date': due_date.strftime('%Y-%m-%d'),
                'due_date_display': due_date.strftime('%B %d, %Y'),
                'weeks_pregnant': weeks_pregnant,
                'days_pregnant': days_pregnant,
                'total_days_pregnant': days_passed,
                'days_remaining': days_remaining,
                'trimester': trimester,
                'trimester_name': trimester_name,
                'trimester_color': trimester_color,
                'trimester_description': trimester_description,
                'progress_percentage': progress_percentage,
                'milestones': milestones,
                'appointments': appointments,
                'statistics': {
                    'weeks_completed': weeks_pregnant,
                    'weeks_remaining': int(float(N(Float(days_remaining, 15) / self.DAYS_PER_WEEK, 10))),
                    'total_weeks': 40,
                    'progress_percentage': progress_percentage
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
            print(f"Pregnancy Calculator Error: {error_details}")
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
    
    def get_milestones(self, weeks_pregnant, lmp):
        """Get fetal development milestones"""
        milestone_data = [
            {'week': 4, 'description': 'Neural tube forms, heart begins to beat', 'color': 'blue'},
            {'week': 8, 'description': 'All major organs forming, fingers and toes visible', 'color': 'green'},
            {'week': 12, 'description': 'Sex organs developing, baby can make fists', 'color': 'yellow'},
            {'week': 16, 'description': 'Baby can hear, skeleton hardening', 'color': 'orange'},
            {'week': 20, 'description': 'Baby can swallow, hair begins to grow', 'color': 'pink'},
            {'week': 24, 'description': 'Viable outside womb, fingerprints forming', 'color': 'purple'},
            {'week': 28, 'description': 'Eyes can open, baby responds to sound', 'color': 'indigo'},
            {'week': 32, 'description': 'Baby gaining weight rapidly, lungs developing', 'color': 'red'},
            {'week': 36, 'description': 'Baby preparing for birth, head down position', 'color': 'teal'},
            {'week': 40, 'description': 'Full term, ready for birth', 'color': 'green'}
        ]
        
        milestones = []
        for milestone in milestone_data:
            milestone_date = lmp + timedelta(days=milestone['week'] * 7)
            passed = weeks_pregnant >= milestone['week']
            milestones.append({
                'week': milestone['week'],
                'date': milestone_date.strftime('%Y-%m-%d'),
                'date_display': milestone_date.strftime('%B %d, %Y'),
                'description': milestone['description'],
                'passed': passed,
                'color': milestone['color']
            })
        
        return milestones
    
    def get_appointments(self, weeks_pregnant, lmp):
        """Get upcoming prenatal appointments"""
        appointment_weeks = [8, 12, 16, 20, 24, 28, 32, 36, 38, 40]
        appointments = []
        
        for week in appointment_weeks:
            if week >= weeks_pregnant:
                appt_date = lmp + timedelta(days=week * 7)
                if week < 28:
                    appt_type = 'Prenatal Checkup'
                elif week < 36:
                    appt_type = 'Prenatal Checkup (Bi-weekly)'
                else:
                    appt_type = 'Final Checkup (Weekly)'
                
                appointments.append({
                    'week': week,
                    'date': appt_date.strftime('%Y-%m-%d'),
                    'date_display': appt_date.strftime('%B %d, %Y'),
                    'type': appt_type
                })
                if len(appointments) >= 3:  # Show next 3
                    break
        
        return appointments
    
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
    
    def prepare_chart_data(self, weeks_pregnant, days_passed, days_remaining, progress_percentage, trimester, trimester_color, milestones):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(trimester_color)
        
        # Pregnancy Progress Gauge Chart
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
        
        # Milestones Timeline Chart
        milestones_passed = sum(1 for m in milestones if m['passed'])
        milestones_total = len(milestones)
        
        milestones_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Milestones Reached', 'Remaining'],
                'datasets': [{
                    'data': [milestones_passed, milestones_total - milestones_passed],
                    'backgroundColor': ['#10b981', '#e5e7eb'],
                    'borderWidth': 2,
                    'borderColor': '#ffffff'
                }]
            },
            'center_text': {
                'value': milestones_passed,
                'label': f'of {milestones_total}',
                'color': '#10b981'
            }
        }
        
        # Weeks Progress Chart
        weeks_chart = {
            'type': 'line',
            'data': {
                'labels': ['Week 0', 'Week 10', 'Week 20', 'Week 30', 'Week 40'],
                'datasets': [{
                    'label': 'Pregnancy Progress',
                    'data': [0, 25, 50, 75, 100],
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
            'progress_gauge_chart': progress_gauge_chart,
            'trimester_chart': trimester_chart,
            'milestones_chart': milestones_chart,
            'weeks_chart': weeks_chart
        }
