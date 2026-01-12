from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StairCalculator(View):
    """
    Professional Stair Calculator with Comprehensive Features
    
    This calculator provides stair calculations with:
    - Calculate number of steps/risers
    - Calculate riser height and tread depth
    - Calculate total rise and run
    - Calculate stair angle
    - Calculate stringer length
    - Building code compliance checks
    
    Features:
    - Supports multiple calculation modes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/stair_calculator.html'
    
    # Length conversion factors (to inches)
    LENGTH_CONVERSIONS = {
        'inches': 1.0,
        'feet': 12.0,  # 1 ft = 12 in
        'meters': 39.3701,  # 1 m = 39.3701 in
        'centimeters': 0.393701,  # 1 cm = 0.393701 in
    }
    
    # Building code standards (in inches)
    MIN_RISER_HEIGHT = 4.0  # Minimum riser height
    MAX_RISER_HEIGHT = 7.75  # Maximum riser height
    MIN_TREAD_DEPTH = 10.0  # Minimum tread depth
    MAX_TREAD_DEPTH = 14.0  # Maximum tread depth
    IDEAL_RISER_TREAD_SUM = 24.5  # 2R + T should be around 24-25 inches
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'inches': 'in',
            'feet': 'ft',
            'meters': 'm',
            'centimeters': 'cm',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Stair Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'design')
            
            if calc_type == 'design':
                return self._calculate_design(data)
            elif calc_type == 'riser_tread':
                return self._calculate_riser_tread(data)
            elif calc_type == 'stringer':
                return self._calculate_stringer(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation type.')
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid JSON data.')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_design(self, data):
        """Calculate stair design from total rise"""
        try:
            if 'total_rise' not in data or data.get('total_rise') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Total rise is required.')
                }, status=400)
            
            try:
                total_rise = float(data.get('total_rise', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            length_unit = data.get('length_unit', 'inches')
            preferred_riser = float(data.get('preferred_riser', 7.0))  # Preferred riser height
            
            # Validate
            if total_rise <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Total rise must be greater than zero.')
                }, status=400)
            
            # Convert to inches
            total_rise_in = float(total_rise * self.LENGTH_CONVERSIONS[length_unit])
            
            # Calculate number of risers
            num_risers = int(np.ceil(np.divide(total_rise_in, preferred_riser)))
            
            # Calculate actual riser height
            riser_height = float(np.divide(total_rise_in, num_risers))
            
            # Calculate tread depth using ideal formula: 2R + T = 24.5
            tread_depth = float(self.IDEAL_RISER_TREAD_SUM - 2 * riser_height)
            
            # Ensure tread depth is within code limits
            if tread_depth < self.MIN_TREAD_DEPTH:
                tread_depth = self.MIN_TREAD_DEPTH
            elif tread_depth > self.MAX_TREAD_DEPTH:
                tread_depth = self.MAX_TREAD_DEPTH
            
            # Calculate total run
            total_run = float(np.multiply(tread_depth, num_risers - 1))  # n-1 treads for n risers
            
            # Calculate stringer length (hypotenuse)
            stringer_length = float(np.sqrt(np.add(np.multiply(total_rise_in, total_rise_in), np.multiply(total_run, total_run))))
            
            # Calculate angle
            angle_rad = float(np.arctan(np.divide(total_rise_in, total_run)))
            angle_deg = float(np.multiply(angle_rad, 180.0 / np.pi))
            
            # Check code compliance
            compliance = self._check_compliance(riser_height, tread_depth)
            
            steps = self._prepare_design_steps(total_rise, length_unit, total_rise_in, preferred_riser, num_risers, riser_height, tread_depth, total_run, stringer_length, angle_deg, compliance)
            chart_data = self._prepare_design_chart_data(riser_height, tread_depth, num_risers, angle_deg)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'design',
                'total_rise': total_rise,
                'length_unit': length_unit,
                'num_risers': num_risers,
                'riser_height': round(riser_height, 3),
                'tread_depth': round(tread_depth, 3),
                'total_run': round(total_run, 3),
                'stringer_length': round(stringer_length, 3),
                'angle': round(angle_deg, 2),
                'compliance': compliance,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating stair design: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_riser_tread(self, data):
        """Calculate from riser and tread dimensions"""
        try:
            if 'riser_height' not in data or data.get('riser_height') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Riser height is required.')
                }, status=400)
            
            if 'tread_depth' not in data or data.get('tread_depth') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Tread depth is required.')
                }, status=400)
            
            if 'num_steps' not in data or data.get('num_steps') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Number of steps is required.')
                }, status=400)
            
            try:
                riser_height = float(data.get('riser_height', 0))
                tread_depth = float(data.get('tread_depth', 0))
                num_steps = int(data.get('num_steps', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            length_unit = data.get('length_unit', 'inches')
            
            # Validate
            if riser_height <= 0 or tread_depth <= 0 or num_steps <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('All values must be greater than zero.')
                }, status=400)
            
            # Convert to inches
            riser_height_in = float(riser_height * self.LENGTH_CONVERSIONS[length_unit])
            tread_depth_in = float(tread_depth * self.LENGTH_CONVERSIONS[length_unit])
            
            # Calculate total rise
            total_rise = float(np.multiply(riser_height_in, num_steps))
            
            # Calculate total run
            total_run = float(np.multiply(tread_depth_in, num_steps - 1))
            
            # Calculate stringer length
            stringer_length = float(np.sqrt(np.add(np.multiply(total_rise, total_rise), np.multiply(total_run, total_run))))
            
            # Calculate angle
            angle_rad = float(np.arctan(np.divide(total_rise, total_run)))
            angle_deg = float(np.multiply(angle_rad, 180.0 / np.pi))
            
            # Check compliance
            compliance = self._check_compliance(riser_height_in, tread_depth_in)
            
            steps = self._prepare_riser_tread_steps(riser_height, tread_depth, num_steps, length_unit, riser_height_in, tread_depth_in, total_rise, total_run, stringer_length, angle_deg, compliance)
            chart_data = self._prepare_design_chart_data(riser_height_in, tread_depth_in, num_steps, angle_deg)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'riser_tread',
                'riser_height': riser_height,
                'tread_depth': tread_depth,
                'num_steps': num_steps,
                'length_unit': length_unit,
                'total_rise': round(total_rise, 3),
                'total_run': round(total_run, 3),
                'stringer_length': round(stringer_length, 3),
                'angle': round(angle_deg, 2),
                'compliance': compliance,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating riser/tread: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_stringer(self, data):
        """Calculate stringer length from rise and run"""
        try:
            if 'total_rise' not in data or data.get('total_rise') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Total rise is required.')
                }, status=400)
            
            if 'total_run' not in data or data.get('total_run') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Total run is required.')
                }, status=400)
            
            try:
                total_rise = float(data.get('total_rise', 0))
                total_run = float(data.get('total_run', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            length_unit = data.get('length_unit', 'inches')
            
            # Validate
            if total_rise <= 0 or total_run <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Total rise and run must be greater than zero.')
                }, status=400)
            
            # Convert to inches
            total_rise_in = float(total_rise * self.LENGTH_CONVERSIONS[length_unit])
            total_run_in = float(total_run * self.LENGTH_CONVERSIONS[length_unit])
            
            # Calculate stringer length (hypotenuse)
            stringer_length = float(np.sqrt(np.add(np.multiply(total_rise_in, total_rise_in), np.multiply(total_run_in, total_run_in))))
            
            # Calculate angle
            angle_rad = float(np.arctan(np.divide(total_rise_in, total_run_in)))
            angle_deg = float(np.multiply(angle_rad, 180.0 / np.pi))
            
            steps = self._prepare_stringer_steps(total_rise, total_run, length_unit, total_rise_in, total_run_in, stringer_length, angle_deg)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'stringer',
                'total_rise': total_rise,
                'total_run': total_run,
                'length_unit': length_unit,
                'stringer_length': round(stringer_length, 3),
                'angle': round(angle_deg, 2),
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating stringer: {error}').format(error=str(e))
            }, status=500)
    
    def _check_compliance(self, riser_height, tread_depth):
        """Check building code compliance"""
        compliance = {
            'riser_ok': self.MIN_RISER_HEIGHT <= riser_height <= self.MAX_RISER_HEIGHT,
            'tread_ok': self.MIN_TREAD_DEPTH <= tread_depth <= self.MAX_TREAD_DEPTH,
            'formula_ok': False,
            'overall': False,
        }
        
        # Check 2R + T formula (should be 24-25 inches)
        riser_tread_sum = 2 * riser_height + tread_depth
        compliance['formula_ok'] = 24.0 <= riser_tread_sum <= 25.0
        compliance['riser_tread_sum'] = round(riser_tread_sum, 2)
        
        compliance['overall'] = compliance['riser_ok'] and compliance['tread_ok'] and compliance['formula_ok']
        
        return compliance
    
    # Step-by-step solution preparation methods
    def _prepare_design_steps(self, total_rise, length_unit, total_rise_in, preferred_riser, num_risers, riser_height, tread_depth, total_run, stringer_length, angle_deg, compliance):
        """Prepare step-by-step solution for design calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Total Rise: {rise} {unit}').format(rise=total_rise, unit=self._format_unit(length_unit)))
        steps.append(_('Preferred Riser Height: {riser} in').format(riser=preferred_riser))
        steps.append('')
        steps.append(_('Step 2: Convert to inches'))
        steps.append(_('Total Rise: {rise} in').format(rise=total_rise_in))
        steps.append('')
        steps.append(_('Step 3: Calculate number of risers'))
        steps.append(_('Number of Risers = Total Rise / Preferred Riser'))
        steps.append(_('Number of Risers = {rise} / {pref} = {num} risers').format(rise=total_rise_in, pref=preferred_riser, num=num_risers))
        steps.append('')
        steps.append(_('Step 4: Calculate actual riser height'))
        steps.append(_('Riser Height = Total Rise / Number of Risers'))
        steps.append(_('Riser Height = {rise} / {num} = {riser} in').format(rise=total_rise_in, num=num_risers, riser=round(riser_height, 3)))
        steps.append('')
        steps.append(_('Step 5: Calculate tread depth'))
        steps.append(_('Using formula: 2R + T = 24.5'))
        steps.append(_('Tread Depth = 24.5 - 2 × Riser Height'))
        steps.append(_('Tread Depth = 24.5 - 2 × {riser} = {tread} in').format(riser=round(riser_height, 3), tread=round(tread_depth, 3)))
        steps.append('')
        steps.append(_('Step 6: Calculate total run'))
        steps.append(_('Total Run = Tread Depth × (Number of Risers - 1)'))
        steps.append(_('Total Run = {tread} × ({num} - 1) = {run} in').format(tread=round(tread_depth, 3), num=num_risers, run=round(total_run, 3)))
        steps.append('')
        steps.append(_('Step 7: Calculate stringer length'))
        steps.append(_('Stringer Length = √(Total Rise² + Total Run²)'))
        steps.append(_('Stringer Length = √({rise}² + {run}²) = {stringer} in').format(rise=total_rise_in, run=round(total_run, 3), stringer=round(stringer_length, 3)))
        steps.append('')
        steps.append(_('Step 8: Calculate angle'))
        steps.append(_('Angle = arctan(Total Rise / Total Run)'))
        steps.append(_('Angle = arctan({rise} / {run}) = {angle}°').format(rise=total_rise_in, run=round(total_run, 3), angle=round(angle_deg, 2)))
        steps.append('')
        steps.append(_('Step 9: Check building code compliance'))
        steps.append(_('Riser Height: {riser} in ({status})').format(riser=round(riser_height, 3), status=_('OK') if compliance['riser_ok'] else _('Not OK')))
        steps.append(_('Tread Depth: {tread} in ({status})').format(tread=round(tread_depth, 3), status=_('OK') if compliance['tread_ok'] else _('Not OK')))
        steps.append(_('2R + T = {sum} ({status})').format(sum=compliance['riser_tread_sum'], status=_('OK') if compliance['formula_ok'] else _('Not OK')))
        return steps
    
    def _prepare_riser_tread_steps(self, riser_height, tread_depth, num_steps, length_unit, riser_height_in, tread_depth_in, total_rise, total_run, stringer_length, angle_deg, compliance):
        """Prepare step-by-step solution for riser/tread calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Riser Height: {riser} {unit}').format(riser=riser_height, unit=self._format_unit(length_unit)))
        steps.append(_('Tread Depth: {tread} {unit}').format(tread=tread_depth, unit=self._format_unit(length_unit)))
        steps.append(_('Number of Steps: {num}').format(num=num_steps))
        steps.append('')
        steps.append(_('Step 2: Convert to inches'))
        steps.append(_('Riser Height: {riser} in').format(riser=riser_height_in))
        steps.append(_('Tread Depth: {tread} in').format(tread=tread_depth_in))
        steps.append('')
        steps.append(_('Step 3: Calculate total rise'))
        steps.append(_('Total Rise = Riser Height × Number of Steps'))
        steps.append(_('Total Rise = {riser} × {num} = {rise} in').format(riser=riser_height_in, num=num_steps, rise=round(total_rise, 3)))
        steps.append('')
        steps.append(_('Step 4: Calculate total run'))
        steps.append(_('Total Run = Tread Depth × (Number of Steps - 1)'))
        steps.append(_('Total Run = {tread} × ({num} - 1) = {run} in').format(tread=tread_depth_in, num=num_steps, run=round(total_run, 3)))
        steps.append('')
        steps.append(_('Step 5: Calculate stringer length'))
        steps.append(_('Stringer Length = √(Total Rise² + Total Run²)'))
        steps.append(_('Stringer Length = √({rise}² + {run}²) = {stringer} in').format(rise=round(total_rise, 3), run=round(total_run, 3), stringer=round(stringer_length, 3)))
        steps.append('')
        steps.append(_('Step 6: Calculate angle'))
        steps.append(_('Angle = arctan(Total Rise / Total Run)'))
        steps.append(_('Angle = arctan({rise} / {run}) = {angle}°').format(rise=round(total_rise, 3), run=round(total_run, 3), angle=round(angle_deg, 2)))
        steps.append('')
        steps.append(_('Step 7: Check building code compliance'))
        steps.append(_('Riser Height: {riser} in ({status})').format(riser=round(riser_height_in, 3), status=_('OK') if compliance['riser_ok'] else _('Not OK')))
        steps.append(_('Tread Depth: {tread} in ({status})').format(tread=round(tread_depth_in, 3), status=_('OK') if compliance['tread_ok'] else _('Not OK')))
        steps.append(_('2R + T = {sum} ({status})').format(sum=compliance['riser_tread_sum'], status=_('OK') if compliance['formula_ok'] else _('Not OK')))
        return steps
    
    def _prepare_stringer_steps(self, total_rise, total_run, length_unit, total_rise_in, total_run_in, stringer_length, angle_deg):
        """Prepare step-by-step solution for stringer calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Total Rise: {rise} {unit}').format(rise=total_rise, unit=self._format_unit(length_unit)))
        steps.append(_('Total Run: {run} {unit}').format(run=total_run, unit=self._format_unit(length_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to inches'))
        steps.append(_('Total Rise: {rise} in').format(rise=total_rise_in))
        steps.append(_('Total Run: {run} in').format(run=total_run_in))
        steps.append('')
        steps.append(_('Step 3: Calculate stringer length'))
        steps.append(_('Stringer Length = √(Total Rise² + Total Run²)'))
        steps.append(_('Stringer Length = √({rise}² + {run}²)').format(rise=total_rise_in, run=total_run_in))
        steps.append(_('Stringer Length = {stringer} in').format(stringer=round(stringer_length, 3)))
        steps.append('')
        steps.append(_('Step 4: Calculate angle'))
        steps.append(_('Angle = arctan(Total Rise / Total Run)'))
        steps.append(_('Angle = arctan({rise} / {run}) = {angle}°').format(rise=total_rise_in, run=total_run_in, angle=round(angle_deg, 2)))
        return steps
    
    # Chart data preparation methods
    def _prepare_design_chart_data(self, riser_height, tread_depth, num_steps, angle_deg):
        """Prepare chart data for stair visualization"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Riser Height'), _('Tread Depth'), _('Angle')],
                    'datasets': [{
                        'label': _('Stair Dimensions'),
                        'data': [riser_height, tread_depth, angle_deg],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(234, 179, 8, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#eab308'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Stair Dimensions')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value')
                            }
                        }
                    }
                }
            }
            return {'stair_chart': chart_config}
        except Exception as e:
            return None
