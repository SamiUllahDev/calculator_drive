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
class ShoeSizeConversion(View):
    """
    Professional Shoe Size Conversion Calculator
    
    This calculator provides shoe size conversions with:
    - Convert between US, UK, EU, CM, and other size systems
    - Support for men's and women's sizes
    - Accurate conversion formulas
    - Step-by-step conversion process
    
    Features:
    - Supports multiple size systems
    - Handles gender-specific conversions
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/shoe_size_conversion.html'
    
    # Size ranges for validation (US sizes)
    MEN_US_RANGE = (4, 16)
    WOMEN_US_RANGE = (4, 14)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Shoe Size Conversion'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for conversions"""
        try:
            data = json.loads(request.body)
            
            if 'from_size' not in data or data.get('from_size') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Size is required.')
                }, status=400)
            
            if 'from_system' not in data:
                return JsonResponse({
                    'success': False,
                    'error': _('Source size system is required.')
                }, status=400)
            
            if 'to_system' not in data:
                return JsonResponse({
                    'success': False,
                    'error': _('Target size system is required.')
                }, status=400)
            
            try:
                from_size = float(data.get('from_size', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a valid number.')
                }, status=400)
            
            from_system = data.get('from_system', 'us')
            to_system = data.get('to_system', 'uk')
            gender = data.get('gender', 'men')  # 'men' or 'women'
            
            # Validate size range
            if not self._is_valid_size(from_size, from_system, gender):
                return JsonResponse({
                    'success': False,
                    'error': _('Size is out of valid range for the selected system and gender.')
                }, status=400)
            
            # Convert to CM first (common intermediate)
            cm_size = self._to_cm(from_size, from_system, gender)
            
            if cm_size is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion. Please check your input.')
                }, status=400)
            
            # Convert from CM to target system
            to_size = self._from_cm(cm_size, to_system, gender)
            
            if to_size is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion. Please check your input.')
                }, status=400)
            
            # Round appropriately
            if to_system in ['us', 'uk']:
                to_size = round(to_size * 2) / 2  # Round to nearest 0.5
            elif to_system == 'eu':
                to_size = round(to_size)
            elif to_system == 'cm':
                to_size = round(to_size, 1)
            else:
                to_size = round(to_size, 1)
            
            steps = self._prepare_conversion_steps(from_size, from_system, cm_size, to_size, to_system, gender)
            
            chart_data = self._prepare_chart_data(from_size, from_system, to_size, to_system, gender)
            
            return JsonResponse({
                'success': True,
                'from_size': from_size,
                'from_system': from_system,
                'to_size': to_size,
                'to_system': to_system,
                'gender': gender,
                'cm_size': round(cm_size, 1),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
                
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
    
    def _to_cm(self, size, system, gender):
        """Convert size to centimeters"""
        try:
            if system == 'cm':
                return float(size)
            
            elif system == 'us':
                if gender == 'men':
                    # US Men's to CM: CM = (US + 22) * 0.847
                    return float((size + 22) * 0.847)
                else:  # women
                    # US Women's to CM: CM = (US + 20.5) * 0.847
                    return float((size + 20.5) * 0.847)
            
            elif system == 'uk':
                if gender == 'men':
                    # UK Men's to CM: CM = (UK + 23) * 0.847
                    return float((size + 23) * 0.847)
                else:  # women
                    # UK Women's to CM: CM = (UK + 21.5) * 0.847
                    return float((size + 21.5) * 0.847)
            
            elif system == 'eu':
                if gender == 'men':
                    # EU Men's to CM: CM = (EU - 2) / 1.5 * 2.54
                    return float((size - 2) / 1.5 * 2.54)
                else:  # women
                    # EU Women's to CM: CM = (EU - 2) / 1.5 * 2.54
                    return float((size - 2) / 1.5 * 2.54)
            
            elif system == 'jp':
                # Japanese sizes are already in CM
                return float(size)
            
            return None
        except Exception:
            return None
    
    def _from_cm(self, cm_size, system, gender):
        """Convert from centimeters to target system"""
        try:
            if system == 'cm':
                return float(cm_size)
            
            elif system == 'us':
                if gender == 'men':
                    # CM to US Men's: US = (CM / 0.847) - 22
                    return float((cm_size / 0.847) - 22)
                else:  # women
                    # CM to US Women's: US = (CM / 0.847) - 20.5
                    return float((cm_size / 0.847) - 20.5)
            
            elif system == 'uk':
                if gender == 'men':
                    # CM to UK Men's: UK = (CM / 0.847) - 23
                    return float((cm_size / 0.847) - 23)
                else:  # women
                    # CM to UK Women's: UK = (CM / 0.847) - 21.5
                    return float((cm_size / 0.847) - 21.5)
            
            elif system == 'eu':
                if gender == 'men':
                    # CM to EU Men's: EU = (CM / 2.54) * 1.5 + 2
                    return float((cm_size / 2.54) * 1.5 + 2)
                else:  # women
                    # CM to EU Women's: EU = (CM / 2.54) * 1.5 + 2
                    return float((cm_size / 2.54) * 1.5 + 2)
            
            elif system == 'jp':
                # Japanese sizes are in CM
                return float(cm_size)
            
            return None
        except Exception:
            return None
    
    def _is_valid_size(self, size, system, gender):
        """Validate if size is within valid range"""
        try:
            if system == 'cm':
                # CM range: approximately 20-35 cm
                return 20 <= size <= 35
            
            elif system == 'us':
                if gender == 'men':
                    return self.MEN_US_RANGE[0] <= size <= self.MEN_US_RANGE[1]
                else:
                    return self.WOMEN_US_RANGE[0] <= size <= self.WOMEN_US_RANGE[1]
            
            elif system == 'uk':
                # UK is typically 1 size smaller than US
                if gender == 'men':
                    return (self.MEN_US_RANGE[0] - 1) <= size <= (self.MEN_US_RANGE[1] - 1)
                else:
                    return (self.WOMEN_US_RANGE[0] - 1) <= size <= (self.WOMEN_US_RANGE[1] - 1)
            
            elif system == 'eu':
                # EU range: approximately 35-50
                return 35 <= size <= 50
            
            elif system == 'jp':
                # Japanese range: approximately 20-35 cm
                return 20 <= size <= 35
            
            return True  # Default to valid if system not recognized
        except Exception:
            return False
    
    def _prepare_conversion_steps(self, from_size, from_system, cm_size, to_size, to_system, gender):
        """Prepare step-by-step conversion explanation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Size: {size} ({system})').format(size=from_size, system=self._get_system_name(from_system)))
        steps.append(_('Gender: {gender}').format(gender=gender.title()))
        steps.append('')
        steps.append(_('Step 2: Convert to centimeters (common intermediate unit)'))
        
        if from_system == 'us':
            if gender == 'men':
                steps.append(_('CM = (US + 22) × 0.847'))
                steps.append(_('CM = ({size} + 22) × 0.847').format(size=from_size))
            else:
                steps.append(_('CM = (US + 20.5) × 0.847'))
                steps.append(_('CM = ({size} + 20.5) × 0.847').format(size=from_size))
        elif from_system == 'uk':
            if gender == 'men':
                steps.append(_('CM = (UK + 23) × 0.847'))
                steps.append(_('CM = ({size} + 23) × 0.847').format(size=from_size))
            else:
                steps.append(_('CM = (UK + 21.5) × 0.847'))
                steps.append(_('CM = ({size} + 21.5) × 0.847').format(size=from_size))
        elif from_system == 'eu':
            steps.append(_('CM = (EU - 2) / 1.5 × 2.54'))
            steps.append(_('CM = ({size} - 2) / 1.5 × 2.54').format(size=from_size))
        elif from_system == 'cm':
            steps.append(_('CM = {size} (already in centimeters)').format(size=from_size))
        elif from_system == 'jp':
            steps.append(_('CM = {size} (Japanese sizes are in centimeters)').format(size=from_size))
        
        steps.append(_('CM = {cm} cm').format(cm=round(cm_size, 1)))
        steps.append('')
        
        if to_system != 'cm':
            steps.append(_('Step 3: Convert from centimeters to target system'))
            
            if to_system == 'us':
                if gender == 'men':
                    steps.append(_('US = (CM / 0.847) - 22'))
                    steps.append(_('US = ({cm} / 0.847) - 22').format(cm=round(cm_size, 1)))
                else:
                    steps.append(_('US = (CM / 0.847) - 20.5'))
                    steps.append(_('US = ({cm} / 0.847) - 20.5').format(cm=round(cm_size, 1)))
            elif to_system == 'uk':
                if gender == 'men':
                    steps.append(_('UK = (CM / 0.847) - 23'))
                    steps.append(_('UK = ({cm} / 0.847) - 23').format(cm=round(cm_size, 1)))
                else:
                    steps.append(_('UK = (CM / 0.847) - 21.5'))
                    steps.append(_('UK = ({cm} / 0.847) - 21.5').format(cm=round(cm_size, 1)))
            elif to_system == 'eu':
                steps.append(_('EU = (CM / 2.54) × 1.5 + 2'))
                steps.append(_('EU = ({cm} / 2.54) × 1.5 + 2').format(cm=round(cm_size, 1)))
            elif to_system == 'jp':
                steps.append(_('JP = {cm} (Japanese sizes are in centimeters)').format(cm=round(cm_size, 1)))
            
            steps.append(_('Result = {size} ({system})').format(size=to_size, system=self._get_system_name(to_system)))
        else:
            steps.append(_('Step 3: Result'))
            steps.append(_('Size = {size} cm').format(size=to_size))
        
        return steps
    
    def _get_system_name(self, system):
        """Get display name for size system"""
        names = {
            'us': 'US',
            'uk': 'UK',
            'eu': 'EU',
            'cm': 'CM',
            'jp': 'JP',
        }
        return names.get(system, system.upper())
    
    def _prepare_chart_data(self, from_size, from_system, to_size, to_system, gender):
        """Prepare chart data for visualization"""
        try:
            # Create comparison chart showing all size systems
            all_systems = ['us', 'uk', 'eu', 'cm', 'jp']
            sizes = []
            labels = []
            
            # Calculate sizes for all systems
            cm_size = self._to_cm(from_size, from_system, gender)
            
            for system in all_systems:
                size = self._from_cm(cm_size, system, gender)
                if system in ['us', 'uk']:
                    size = round(size * 2) / 2
                elif system == 'eu':
                    size = round(size)
                elif system == 'cm':
                    size = round(size, 1)
                else:
                    size = round(size, 1)
                
                sizes.append(size)
                labels.append(self._get_system_name(system))
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': _('Shoe Size'),
                        'data': sizes,
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)' if system == from_system or system == to_system
                            else 'rgba(156, 163, 175, 0.6)'
                            for system in all_systems
                        ],
                        'borderColor': [
                            '#3b82f6' if system == from_system or system == to_system
                            else '#9ca3af'
                            for system in all_systems
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
                            'text': _('Shoe Size Conversion ({gender})').format(gender=gender.title())
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': False,
                            'title': {
                                'display': True,
                                'text': _('Size')
                            }
                        }
                    }
                }
            }
            return {'conversion_chart': chart_config}
        except Exception as e:
            return None
