from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
import re
from collections import defaultdict


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MolecularWeightCalculator(View):
    """
    Professional Molecular Weight Calculator with Comprehensive Features
    
    This calculator provides molecular weight calculations with:
    - Calculate molecular weight from chemical formula
    - Parse complex formulas with parentheses and subscripts
    - Display element breakdown
    - Calculate mass percentage of elements
    - Handle hydrates and complex compounds
    
    Features:
    - Supports complex chemical formulas
    - Handles parentheses, subscripts, and multipliers
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/molecular_weight_calculator.html'
    
    # Atomic weights (in g/mol) - most common elements
    ATOMIC_WEIGHTS = {
        'H': 1.008, 'He': 4.003, 'Li': 6.941, 'Be': 9.012, 'B': 10.81,
        'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998, 'Ne': 20.180,
        'Na': 22.990, 'Mg': 24.305, 'Al': 26.982, 'Si': 28.086, 'P': 30.974,
        'S': 32.066, 'Cl': 35.453, 'Ar': 39.948, 'K': 39.098, 'Ca': 40.078,
        'Sc': 44.956, 'Ti': 47.867, 'V': 50.942, 'Cr': 52.000, 'Mn': 54.938,
        'Fe': 55.845, 'Co': 58.933, 'Ni': 58.693, 'Cu': 63.546, 'Zn': 65.380,
        'Ga': 69.723, 'Ge': 72.631, 'As': 74.922, 'Se': 78.971, 'Br': 79.904,
        'Kr': 83.798, 'Rb': 85.468, 'Sr': 87.62, 'Y': 88.906, 'Zr': 91.224,
        'Nb': 92.906, 'Mo': 95.950, 'Tc': 98.000, 'Ru': 101.07, 'Rh': 102.906,
        'Pd': 106.42, 'Ag': 107.868, 'Cd': 112.411, 'In': 114.818, 'Sn': 118.710,
        'Sb': 121.760, 'Te': 127.600, 'I': 126.904, 'Xe': 131.293, 'Cs': 132.905,
        'Ba': 137.327, 'La': 138.905, 'Ce': 140.116, 'Pr': 140.908, 'Nd': 144.242,
        'Pm': 145.000, 'Sm': 150.360, 'Eu': 151.964, 'Gd': 157.250, 'Tb': 158.925,
        'Dy': 162.500, 'Ho': 164.930, 'Er': 167.259, 'Tm': 168.934, 'Yb': 173.045,
        'Lu': 174.967, 'Hf': 178.490, 'Ta': 180.948, 'W': 183.840, 'Re': 186.207,
        'Os': 190.230, 'Ir': 192.217, 'Pt': 195.085, 'Au': 196.967, 'Hg': 200.592,
        'Tl': 204.383, 'Pb': 207.200, 'Bi': 208.980, 'Po': 209.000, 'At': 210.000,
        'Rn': 222.000, 'Fr': 223.000, 'Ra': 226.000, 'Ac': 227.000, 'Th': 232.038,
        'Pa': 231.036, 'U': 238.029, 'Np': 237.000, 'Pu': 244.000,
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Molecular Weight Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'calculate_mw')
            
            if calc_type == 'calculate_mw':
                return self._calculate_molecular_weight(data)
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
    
    def _parse_formula(self, formula):
        """
        Parse a chemical formula and return element counts
        
        Handles:
        - Simple formulas: H2O, CO2
        - Formulas with parentheses: Ca(OH)2, Al2(SO4)3
        - Formulas with dots (hydrates): CuSO4·5H2O
        - Complex formulas: C6H12O6
        """
        formula = formula.strip()
        if not formula:
            return None
        
        # Replace · with * for hydrate notation
        formula = formula.replace('·', '*').replace('•', '*')
        
        # Split by * for hydrates
        parts = formula.split('*')
        
        element_counts = defaultdict(float)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Parse this part
            counts = self._parse_formula_part(part)
            if counts is None:
                return None
            
            # Merge counts
            for element, count in counts.items():
                element_counts[element] += count
        
        return dict(element_counts)
    
    def _parse_formula_part(self, formula):
        """Parse a single formula part (without hydrates)"""
        element_counts = defaultdict(float)
        
        # Pattern to match element symbols (1-2 letters) followed by optional number
        # Also handles parentheses groups
        pattern = r'([A-Z][a-z]?)(\d*)|\(([^)]+)\)(\d*)'
        
        i = 0
        while i < len(formula):
            # Try to match element or group
            match = re.match(r'([A-Z][a-z]?)(\d*)|\(([^)]+)\)(\d*)', formula[i:])
            
            if not match:
                # Invalid character
                return None
            
            if match.group(1):  # Element match
                element = match.group(1)
                count_str = match.group(2)
                count = float(count_str) if count_str else 1.0
                
                if element not in self.ATOMIC_WEIGHTS:
                    return None
                
                element_counts[element] += count
                i += len(match.group(0))
            
            elif match.group(3):  # Parentheses group match
                group_formula = match.group(3)
                count_str = match.group(4)
                multiplier = float(count_str) if count_str else 1.0
                
                # Recursively parse the group
                group_counts = self._parse_formula_part(group_formula)
                if group_counts is None:
                    return None
                
                # Multiply counts by multiplier
                for element, count in group_counts.items():
                    element_counts[element] += count * multiplier
                
                i += len(match.group(0))
            else:
                return None
        
        return dict(element_counts) if element_counts else None
    
    def _calculate_molecular_weight(self, data):
        """Calculate molecular weight from chemical formula"""
        try:
            if 'formula' not in data or not data.get('formula'):
                return JsonResponse({
                    'success': False,
                    'error': _('Chemical formula is required.')
                }, status=400)
            
            formula = data.get('formula', '').strip()
            
            if not formula:
                return JsonResponse({
                    'success': False,
                    'error': _('Chemical formula cannot be empty.')
                }, status=400)
            
            # Parse formula
            element_counts = self._parse_formula(formula)
            
            if element_counts is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid chemical formula. Please check the format.')
                }, status=400)
            
            # Calculate molecular weight
            molecular_weight = 0.0
            element_details = []
            
            for element, count in sorted(element_counts.items()):
                if element not in self.ATOMIC_WEIGHTS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Unknown element: {element}').format(element=element)
                    }, status=400)
                
                atomic_weight = self.ATOMIC_WEIGHTS[element]
                element_mass = atomic_weight * count
                molecular_weight += element_mass
                
                element_details.append({
                    'element': element,
                    'count': count,
                    'atomic_weight': atomic_weight,
                    'mass': element_mass,
                    'percentage': 0.0  # Will calculate after total MW
                })
            
            # Calculate percentages
            if molecular_weight > 0:
                for detail in element_details:
                    detail['percentage'] = (detail['mass'] / molecular_weight) * 100.0
            
            # Validate result
            if math.isinf(molecular_weight) or math.isnan(molecular_weight) or molecular_weight <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_molecular_weight_steps(formula, element_details, molecular_weight)
            
            chart_data = self._prepare_molecular_weight_chart_data(element_details, molecular_weight)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'calculate_mw',
                'formula': formula,
                'molecular_weight': round(molecular_weight, 4),
                'element_details': element_details,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating molecular weight: {error}').format(error=str(e))
            }, status=500)
    
    def _prepare_molecular_weight_steps(self, formula, element_details, molecular_weight):
        """Prepare step-by-step solution for molecular weight calculation"""
        steps = []
        steps.append(_('Step 1: Identify the chemical formula'))
        steps.append(_('Formula: {formula}').format(formula=formula))
        steps.append('')
        steps.append(_('Step 2: Identify all elements and their counts'))
        
        for detail in element_details:
            if detail['count'] == int(detail['count']):
                count_str = str(int(detail['count']))
            else:
                count_str = str(detail['count'])
            steps.append(_('{element}: {count} atom(s)').format(element=detail['element'], count=count_str))
        
        steps.append('')
        steps.append(_('Step 3: Calculate mass contribution of each element'))
        
        for detail in element_details:
            if detail['count'] == int(detail['count']):
                count_str = str(int(detail['count']))
            else:
                count_str = str(detail['count'])
            steps.append(_('{element}: {count} × {aw} g/mol = {mass} g/mol').format(
                element=detail['element'],
                count=count_str,
                aw=detail['atomic_weight'],
                mass=round(detail['mass'], 4)
            ))
        
        steps.append('')
        steps.append(_('Step 4: Sum all mass contributions'))
        mass_sum = ' + '.join([_('{mass}').format(mass=round(detail['mass'], 4)) for detail in element_details])
        steps.append(_('Molecular Weight = {sum}').format(sum=mass_sum))
        steps.append(_('Molecular Weight = {mw} g/mol').format(mw=round(molecular_weight, 4)))
        steps.append('')
        steps.append(_('Step 5: Calculate mass percentage of each element'))
        
        for detail in element_details:
            steps.append(_('{element}: ({mass} / {mw}) × 100% = {pct}%').format(
                element=detail['element'],
                mass=round(detail['mass'], 4),
                mw=round(molecular_weight, 4),
                pct=round(detail['percentage'], 2)
            ))
        
        return steps
    
    def _prepare_molecular_weight_chart_data(self, element_details, molecular_weight):
        """Prepare chart data for molecular weight calculation"""
        try:
            # Pie chart for element mass percentages
            pie_config = {
                'type': 'pie',
                'data': {
                    'labels': [detail['element'] for detail in element_details],
                    'datasets': [{
                        'data': [detail['percentage'] for detail in element_details],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(20, 184, 166, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24',
                            '#ef4444',
                            '#8b5cf6',
                            '#ec4899',
                            '#14b8a6',
                            '#f59e0b',
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': True,
                            'position': 'right'
                        },
                        'title': {
                            'display': True,
                            'text': _('Element Mass Percentage')
                        },
                    }
                }
            }
            
            # Bar chart for element masses
            bar_config = {
                'type': 'bar',
                'data': {
                    'labels': [detail['element'] for detail in element_details],
                    'datasets': [{
                        'label': _('Mass Contribution (g/mol)'),
                        'data': [detail['mass'] for detail in element_details],
                        'backgroundColor': 'rgba(59, 130, 246, 0.8)',
                        'borderColor': '#3b82f6',
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': True
                        },
                        'title': {
                            'display': True,
                            'text': _('Element Mass Contributions')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Mass (g/mol)')
                            }
                        }
                    }
                }
            }
            
            return {
                'element_percentage_chart': pie_config,
                'element_mass_chart': bar_config
            }
        except Exception as e:
            return None
