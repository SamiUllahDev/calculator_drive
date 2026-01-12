from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BraSizeCalculator(View):
    """
    Professional Bra Size Calculator with Comprehensive Features
    
    This calculator provides bra size calculations with:
    - Multiple sizing systems (US, UK, EU, FR, AU)
    - Band size calculations
    - Cup size determinations
    - Sister size suggestions
    - Size conversion between systems
    - Visual size charts
    
    Features:
    - Supports multiple measurement units (inches, cm)
    - Handles different sizing standards
    - Provides sister sizes
    - Calculates proper fit recommendations
    - Interactive visualizations
    """
    template_name = 'other_calculators/bra_size_calculator.html'
    
    # Cup size mappings for different systems
    CUP_SIZES = {
        'US': ['AA', 'A', 'B', 'C', 'D', 'DD', 'DDD', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'UK': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ'],
        'EU': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'FR': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'AU': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ'],
        'PK': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ'],  # Pakistan (uses UK sizing)
        'CA': ['AA', 'A', 'B', 'C', 'D', 'DD', 'DDD', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],  # Canada (uses US sizing)
        'IN': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ'],  # India (uses UK sizing)
        'NZ': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ'],  # New Zealand (uses UK sizing)
        'IT': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],  # Italy (uses EU sizing)
        'ES': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],  # Spain (uses EU sizing)
        'DE': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],  # Germany (uses EU sizing)
        'JP': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],  # Japan (uses similar to EU)
        'CN': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],  # China (uses similar to EU)
        'BR': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],  # Brazil (uses EU sizing)
        'MX': ['AA', 'A', 'B', 'C', 'D', 'DD', 'DDD', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],  # Mexico (uses US sizing)
        'ZA': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ']  # South Africa (uses UK sizing)
    }
    
    # Country to sizing system mapping
    COUNTRY_TO_SYSTEM = {
        'US': 'US', 'United States': 'US', 'USA': 'US',
        'UK': 'UK', 'United Kingdom': 'UK', 'Britain': 'UK',
        'EU': 'EU', 'Europe': 'EU',
        'FR': 'FR', 'France': 'FR',
        'AU': 'AU', 'Australia': 'AU',
        'PK': 'PK', 'Pakistan': 'PK',
        'CA': 'CA', 'Canada': 'CA',
        'IN': 'IN', 'India': 'IN',
        'NZ': 'NZ', 'New Zealand': 'NZ',
        'IT': 'IT', 'Italy': 'IT',
        'ES': 'ES', 'Spain': 'ES',
        'DE': 'DE', 'Germany': 'DE',
        'JP': 'JP', 'Japan': 'JP',
        'CN': 'CN', 'China': 'CN',
        'BR': 'BR', 'Brazil': 'BR',
        'MX': 'MX', 'Mexico': 'MX',
        'ZA': 'ZA', 'South Africa': 'ZA'
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Bra Size Calculator'),
            'features': [
                _('Multiple sizing systems (US, UK, EU, FR, AU, PK, CA, IN, NZ, IT, ES, DE, JP, CN, BR, MX, ZA)'),
                _('Band and cup size calculations'),
                _('Sister size suggestions'),
                _('Size conversion between systems'),
                _('Proper fit recommendations'),
                _('Visual size charts')
            ]
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'bra_size')
            
            if calc_type == 'bra_size':
                return self._calculate_bra_size(data)
            elif calc_type == 'size_conversion':
                return self._convert_size(data)
            elif calc_type == 'sister_sizes':
                return self._get_sister_sizes(data)
            else:
                return JsonResponse({'success': False, 'error': _('Invalid calculation type.')}, status=400)
                
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: {error}').format(error=str(e))}, status=400)
        except Exception as e:
            import traceback
            print(f"Bra Size Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
    
    def _calculate_bra_size(self, data):
        """Calculate bra size from measurements"""
        underbust = float(data.get('underbust', 0))
        bust = float(data.get('bust', 0))
        unit = data.get('unit', 'inches')
        sizing_system = data.get('sizing_system', 'US')
        
        if underbust <= 0 or bust <= 0:
            return JsonResponse({'success': False, 'error': _('Measurements must be greater than zero.')}, status=400)
        
        if bust <= underbust:
            return JsonResponse({'success': False, 'error': _('Bust measurement must be greater than underbust measurement.')}, status=400)
        
        # Convert to inches if needed
        if unit == 'cm':
            underbust_inches = underbust / 2.54
            bust_inches = bust / 2.54
        else:
            underbust_inches = underbust
            bust_inches = bust
        
        # Validate measurements are in reasonable range
        if underbust_inches < 20 or underbust_inches > 60:
            return JsonResponse({'success': False, 'error': _('Underbust measurement must be between 20 and 60 inches (51-152 cm).')}, status=400)
        
        if bust_inches < 25 or bust_inches > 70:
            return JsonResponse({'success': False, 'error': _('Bust measurement must be between 25 and 70 inches (64-178 cm).')}, status=400)
        
        # Calculate band size (round to nearest even number)
        band_size = self._calculate_band_size(underbust_inches)
        
        # Validate band size is in valid range
        if band_size < 28 or band_size > 50:
            return JsonResponse({'success': False, 'error': _('Calculated band size ({band}) is outside valid range (28-50). Please check your measurements.').format(band=int(band_size))}, status=400)
        
        # Calculate cup size
        cup_difference = bust_inches - band_size
        cup_size_index = self._get_cup_index(cup_difference)
        
        # Get cup letter for the sizing system
        cup_letter = self.CUP_SIZES.get(sizing_system, self.CUP_SIZES['US'])[cup_size_index] if cup_size_index < len(self.CUP_SIZES.get(sizing_system, self.CUP_SIZES['US'])) else 'N'
        
        # Calculate sizes in all systems
        all_sizes = self._get_all_system_sizes(band_size, cup_size_index)
        
        # Get sister sizes
        sister_sizes = self._calculate_sister_sizes(band_size, cup_size_index, sizing_system)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_bra_size_steps(
            underbust, bust, unit, underbust_inches, bust_inches,
            band_size, cup_difference, cup_size_index, cup_letter, sizing_system
        )
        
        # Prepare chart data
        chart_data = self._prepare_chart_data(all_sizes, sizing_system)
        
        result = {
            'success': True,
            'calc_type': 'bra_size',
            'measurements': {
                'underbust': underbust,
                'bust': bust,
                'unit': unit,
                'underbust_inches': round(underbust_inches, 2),
                'bust_inches': round(bust_inches, 2)
            },
            'bra_size': {
                'band': int(band_size),
                'cup': cup_letter,
                'full_size': f"{int(band_size)}{cup_letter}",
                'sizing_system': sizing_system
            },
            'all_sizes': all_sizes,
            'sister_sizes': sister_sizes,
            'cup_difference': round(cup_difference, 2),
            'step_by_step': step_by_step,
            'chart_data': chart_data
        }
        
        return JsonResponse(result)
    
    def _convert_size(self, data):
        """Convert bra size between different systems"""
        size = data.get('size', '')
        from_system = data.get('from_system', 'US')
        to_system = data.get('to_system', 'UK')
        
        if not size:
            return JsonResponse({'success': False, 'error': _('Please enter a bra size.')}, status=400)
        
        # Parse size (e.g., "34C" or "34 C")
        import re
        match = re.match(r'(\d+)\s*([A-Z]+)', size.upper())
        if not match:
            return JsonResponse({'success': False, 'error': _('Invalid size format. Please use format like "34C" or "34 C".')}, status=400)
        
        band = int(match.group(1))
        cup_letter = match.group(2)
        
        # Validate band size
        if from_system == 'FR':
            if band < 75 or band > 115:
                return JsonResponse({'success': False, 'error': _('FR band size must be between 75 and 115.')}, status=400)
        else:
            if band < 28 or band > 50:
                return JsonResponse({'success': False, 'error': _('Band size must be between 28 and 50.')}, status=400)
        
        # Get cup index in source system
        source_cups = self.CUP_SIZES.get(from_system, self.CUP_SIZES['US'])
        try:
            cup_index = source_cups.index(cup_letter)
        except ValueError:
            return JsonResponse({'success': False, 'error': _('Invalid cup size for the selected system.')}, status=400)
        
        # Convert to target system
        target_cups = self.CUP_SIZES.get(to_system, self.CUP_SIZES['US'])
        if cup_index >= len(target_cups):
            return JsonResponse({'success': False, 'error': _('Cup size not available in target system.')}, status=400)
        
        target_cup = target_cups[cup_index]
        
        # Band size conversion
        # FR uses cm-based band (add 15 to convert from inches)
        # All other systems use the same band size (inches-based)
        if from_system == 'FR' and to_system != 'FR':
            # Convert from FR to others (FR uses cm, subtract 15)
            converted_band = band - 15
            if converted_band < 28 or converted_band > 50:
                return JsonResponse({'success': False, 'error': _('Converted band size is outside valid range.')}, status=400)
        elif to_system == 'FR' and from_system != 'FR':
            # Convert to FR (add 15)
            converted_band = band + 15
            if converted_band < 75 or converted_band > 115:
                return JsonResponse({'success': False, 'error': _('Converted band size is outside valid FR range.')}, status=400)
        else:
            # Same band size for all other systems (US, UK, EU, PK, CA, IN, NZ, IT, ES, DE, JP, CN, BR, MX, ZA, AU)
            converted_band = band
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_conversion_steps(band, cup_letter, from_system, int(converted_band), target_cup, to_system)
        
        result = {
            'success': True,
            'calc_type': 'size_conversion',
            'original_size': f"{band}{cup_letter}",
            'from_system': from_system,
            'converted_size': f"{int(converted_band)}{target_cup}",
            'to_system': to_system,
            'step_by_step': step_by_step
        }
        
        return JsonResponse(result)
    
    def _get_sister_sizes(self, data):
        """Get sister sizes for a given bra size"""
        size = data.get('size', '')
        system = data.get('sizing_system', 'US')
        
        if not size:
            return JsonResponse({'success': False, 'error': _('Please enter a bra size.')}, status=400)
        
        import re
        match = re.match(r'(\d+)\s*([A-Z]+)', size.upper())
        if not match:
            return JsonResponse({'success': False, 'error': _('Invalid size format.')}, status=400)
        
        band = int(match.group(1))
        cup_letter = match.group(2)
        
        cups = self.CUP_SIZES.get(system, self.CUP_SIZES['US'])
        try:
            cup_index = cups.index(cup_letter)
        except ValueError:
            return JsonResponse({'success': False, 'error': _('Invalid cup size.')}, status=400)
        
        # Validate band size
        if system == 'FR':
            if band < 75 or band > 115:
                return JsonResponse({'success': False, 'error': _('FR band size must be between 75 and 115.')}, status=400)
        else:
            if band < 28 or band > 50:
                return JsonResponse({'success': False, 'error': _('Band size must be between 28 and 50.')}, status=400)
        
        sister_sizes = self._calculate_sister_sizes(band, cup_index, system)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_sister_sizes_steps(band, cup_letter, system, sister_sizes)
        
        result = {
            'success': True,
            'calc_type': 'sister_sizes',
            'original_size': f"{band}{cup_letter}",
            'sizing_system': system,
            'sister_sizes': sister_sizes,
            'step_by_step': step_by_step
        }
        
        return JsonResponse(result)
    
    def _calculate_band_size(self, underbust_inches):
        """Calculate band size from underbust measurement"""
        # Round to nearest even number
        rounded = round(underbust_inches)
        if rounded % 2 == 0:
            return rounded
        else:
            return rounded + 1
    
    def _get_cup_index(self, cup_difference):
        """Get cup size index based on difference"""
        # Cup sizes: AA=0, A=1, B=2, C=3, D=4, DD=5, etc.
        if cup_difference < 0.5:
            return 0  # AA
        elif cup_difference < 1.5:
            return 1  # A
        elif cup_difference < 2.5:
            return 2  # B
        elif cup_difference < 3.5:
            return 3  # C
        elif cup_difference < 4.5:
            return 4  # D
        elif cup_difference < 5.5:
            return 5  # DD/E
        elif cup_difference < 6.5:
            return 6  # DDD/F
        elif cup_difference < 7.5:
            return 7  # G
        elif cup_difference < 8.5:
            return 8  # H
        elif cup_difference < 9.5:
            return 9  # I
        elif cup_difference < 10.5:
            return 10  # J
        elif cup_difference < 11.5:
            return 11  # K
        elif cup_difference < 12.5:
            return 12  # L
        elif cup_difference < 13.5:
            return 13  # M
        else:
            return 14  # N
    
    def _get_all_system_sizes(self, band_size, cup_index):
        """Get bra size in all sizing systems"""
        all_sizes = {}
        for system, cups in self.CUP_SIZES.items():
            if cup_index < len(cups):
                if system == 'FR':
                    # FR uses cm-based band (add 15)
                    all_sizes[system] = f"{int(band_size + 15)}{cups[cup_index]}"
                else:
                    all_sizes[system] = f"{int(band_size)}{cups[cup_index]}"
        return all_sizes
    
    def _calculate_sister_sizes(self, band_size, cup_index, system):
        """Calculate sister sizes (same cup volume, different band/cup combination)"""
        sister_sizes = []
        cups = self.CUP_SIZES.get(system, self.CUP_SIZES['US'])
        
        # Sister sizes: go up/down in band, opposite in cup
        for offset in [-2, -1, 1, 2]:
            new_band = band_size + offset
            new_cup_index = cup_index - offset
            
            if new_band >= 28 and new_band <= 50 and new_cup_index >= 0 and new_cup_index < len(cups):
                sister_sizes.append({
                    'band': int(new_band),
                    'cup': cups[new_cup_index],
                    'size': f"{int(new_band)}{cups[new_cup_index]}"
                })
        
        return sister_sizes
    
    def _prepare_bra_size_steps(self, underbust, bust, unit, underbust_inches, bust_inches,
                               band_size, cup_difference, cup_index, cup_letter, system):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(_("Step 1: Take Measurements"))
        steps.append(_("  Underbust: {measurement} {unit}").format(measurement=underbust, unit=unit))
        steps.append(_("  Bust (at fullest point): {measurement} {unit}").format(measurement=bust, unit=unit))
        steps.append("")
        
        if unit == 'cm':
            steps.append(_("Step 2: Convert to Inches (if needed)"))
            steps.append(_("  Underbust in inches = {cm} cm ÷ 2.54 = {inches:.2f} inches").format(
                cm=underbust, inches=underbust_inches
            ))
            steps.append(_("  Bust in inches = {cm} cm ÷ 2.54 = {inches:.2f} inches").format(
                cm=bust, inches=bust_inches
            ))
            steps.append("")
        
        steps.append(_("Step 3: Calculate Band Size"))
        steps.append(_("  Band Size = Round underbust ({inches:.2f} inches) to nearest even number").format(inches=underbust_inches))
        steps.append(_("  Band Size = {band}").format(band=int(band_size)))
        steps.append("")
        
        steps.append(_("Step 4: Calculate Cup Size"))
        steps.append(_("  Cup Difference = Bust - Band Size"))
        steps.append(_("  Cup Difference = {bust:.2f} - {band} = {diff:.2f} inches").format(
            bust=bust_inches, band=int(band_size), diff=cup_difference
        ))
        steps.append(_("  Cup Size = {cup} (based on {diff:.2f} inch difference)").format(
            cup=cup_letter, diff=cup_difference
        ))
        steps.append("")
        
        steps.append(_("Step 5: Final Result"))
        steps.append(_("  Bra Size ({system}): {band}{cup}").format(
            system=system, band=int(band_size), cup=cup_letter
        ))
        
        return [str(step) for step in steps]
    
    def _prepare_chart_data(self, all_sizes, current_system):
        """Prepare chart data for size visualization"""
        chart_data = {}
        
        try:
            systems = list(all_sizes.keys())
            # Extract band sizes for visualization (numeric data)
            band_sizes = []
            cup_indices = []
            
            for sys in systems:
                size_str = all_sizes[sys]
                import re
                match = re.match(r'(\d+)([A-Z]+)', size_str)
                if match:
                    band_sizes.append(int(match.group(1)))
                    cup_letter = match.group(2)
                    cups = self.CUP_SIZES.get(sys, self.CUP_SIZES['US'])
                    try:
                        cup_indices.append(cups.index(cup_letter))
                    except ValueError:
                        cup_indices.append(0)
            
            # Generate colors for all systems
            pink_colors = [
                'rgba(236, 72, 153, 0.6)', 'rgba(244, 63, 94, 0.6)', 'rgba(251, 113, 133, 0.6)',
                'rgba(252, 165, 165, 0.6)', 'rgba(253, 164, 175, 0.6)', 'rgba(254, 205, 211, 0.6)',
                'rgba(255, 228, 230, 0.6)', 'rgba(255, 192, 203, 0.6)', 'rgba(255, 182, 193, 0.6)',
                'rgba(255, 160, 122, 0.6)', 'rgba(255, 105, 180, 0.6)', 'rgba(255, 20, 147, 0.6)',
                'rgba(219, 112, 147, 0.6)', 'rgba(199, 21, 133, 0.6)', 'rgba(255, 192, 203, 0.6)',
                'rgba(255, 160, 122, 0.6)', 'rgba(255, 105, 180, 0.6)'
            ]
            pink_borders = [
                '#ec4899', '#f43f5e', '#fb7185', '#fca5a5', '#fda4af', '#fecdd3',
                '#ffe4e6', '#ffc0cb', '#ffb6c1', '#ffa07a', '#ff69b4', '#ff1493',
                '#db7093', '#c71585', '#ffc0cb', '#ffa07a', '#ff69b4'
            ]
            
            # Band size comparison chart
            chart_data['band_size_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': systems,
                    'datasets': [{
                        'label': str(_('Band Size')),
                        'data': band_sizes,
                        'backgroundColor': pink_colors[:len(systems)],
                        'borderColor': pink_borders[:len(systems)],
                        'borderWidth': 2,
                        'borderRadius': 4
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {
                            'display': True
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': False,
                            'min': min(band_sizes) - 2 if band_sizes else 0,
                            'max': max(band_sizes) + 2 if band_sizes else 50
                        }
                    }
                }
            }
            
            # Generate purple colors for cup chart
            purple_colors = [
                'rgba(139, 92, 246, 0.6)', 'rgba(168, 85, 247, 0.6)', 'rgba(192, 132, 252, 0.6)',
                'rgba(221, 214, 254, 0.6)', 'rgba(233, 213, 255, 0.6)', 'rgba(196, 181, 253, 0.6)',
                'rgba(167, 139, 250, 0.6)', 'rgba(147, 51, 234, 0.6)', 'rgba(126, 34, 206, 0.6)',
                'rgba(109, 40, 217, 0.6)', 'rgba(91, 33, 182, 0.6)', 'rgba(76, 29, 149, 0.6)',
                'rgba(124, 58, 237, 0.6)', 'rgba(139, 92, 246, 0.6)', 'rgba(168, 85, 247, 0.6)',
                'rgba(192, 132, 252, 0.6)', 'rgba(221, 214, 254, 0.6)'
            ]
            purple_borders = [
                '#8b5cf6', '#a855f7', '#c084fc', '#ddd6fe', '#e9d5ff', '#c4b5fd',
                '#a78bfa', '#9333ea', '#7e22ce', '#6d28d9', '#5b21b6', '#4c1d95',
                '#7c3aed', '#8b5cf6', '#a855f7', '#c084fc', '#ddd6fe'
            ]
            
            # Cup size comparison chart
            chart_data['cup_size_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': systems,
                    'datasets': [{
                        'label': str(_('Cup Index')),
                        'data': cup_indices,
                        'backgroundColor': purple_colors[:len(systems)],
                        'borderColor': purple_borders[:len(systems)],
                        'borderWidth': 2,
                        'borderRadius': 4
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {
                            'display': True
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True
                        }
                    }
                }
            }
        except Exception as e:
            import traceback
            print(f"Chart data preparation error: {traceback.format_exc()}")
            chart_data = {}
        
        return chart_data
    
    def _prepare_conversion_steps(self, band, cup_letter, from_system, converted_band, target_cup, to_system):
        """Prepare step-by-step solution for size conversion"""
        steps = []
        
        steps.append(_("Step 1: Parse Original Size"))
        steps.append(_("  Original Size: {band}{cup} ({system})").format(band=band, cup=cup_letter, system=from_system))
        steps.append(_("  Band: {band}").format(band=band))
        steps.append(_("  Cup: {cup}").format(cup=cup_letter))
        steps.append("")
        
        steps.append(_("Step 2: Find Cup Index"))
        source_cups = self.CUP_SIZES.get(from_system, self.CUP_SIZES['US'])
        cup_index = source_cups.index(cup_letter)
        steps.append(_("  Cup '{cup}' is at index {index} in {system} system").format(cup=cup_letter, index=cup_index, system=from_system))
        steps.append("")
        
        steps.append(_("Step 3: Convert Band Size"))
        if from_system == 'FR' and to_system != 'FR':
            steps.append(_("  Converting from FR (cm-based) to {system}").format(system=to_system))
            steps.append(_("  Converted Band = {band} - 15 = {converted}").format(band=band, converted=converted_band))
        elif to_system == 'FR' and from_system != 'FR':
            steps.append(_("  Converting to FR (cm-based) from {system}").format(system=from_system))
            steps.append(_("  Converted Band = {band} + 15 = {converted}").format(band=band, converted=converted_band))
        else:
            steps.append(_("  Band size remains the same: {band}").format(band=band))
        steps.append("")
        
        steps.append(_("Step 4: Convert Cup Size"))
        target_cups = self.CUP_SIZES.get(to_system, self.CUP_SIZES['US'])
        steps.append(_("  Using cup index {index} in {system} system").format(index=cup_index, system=to_system))
        steps.append(_("  Converted Cup = {cup}").format(cup=target_cup))
        steps.append("")
        
        steps.append(_("Step 5: Final Result"))
        steps.append(_("  Converted Size ({system}): {band}{cup}").format(system=to_system, band=converted_band, cup=target_cup))
        
        return [str(step) for step in steps]
    
    def _prepare_sister_sizes_steps(self, band, cup_letter, system, sister_sizes):
        """Prepare step-by-step solution for sister sizes"""
        steps = []
        
        steps.append(_("Step 1: Original Size"))
        steps.append(_("  Original Size: {band}{cup} ({system})").format(band=band, cup=cup_letter, system=system))
        steps.append("")
        
        steps.append(_("Step 2: Understanding Sister Sizes"))
        steps.append(_("  Sister sizes have the same cup volume but different band and cup combinations"))
        steps.append(_("  When band size increases, cup size decreases (and vice versa)"))
        steps.append("")
        
        steps.append(_("Step 3: Calculate Sister Sizes"))
        cups = self.CUP_SIZES.get(system, self.CUP_SIZES['US'])
        cup_index = cups.index(cup_letter)
        
        for offset in [-2, -1, 1, 2]:
            new_band = band + offset
            new_cup_index = cup_index - offset
            if new_band >= 28 and new_band <= 50 and new_cup_index >= 0 and new_cup_index < len(cups):
                steps.append(_("  {band}{cup}: Band {original} {direction} {offset} = {new_band}, Cup {original_cup} {cup_direction} {offset} = {new_cup}").format(
                    band=new_band, cup=cups[new_cup_index],
                    original=band, direction="+" if offset > 0 else "-", offset=abs(offset), new_band=new_band,
                    original_cup=cup_letter, cup_direction="-" if offset > 0 else "+", new_cup=cups[new_cup_index]
                ))
        steps.append("")
        
        steps.append(_("Step 4: Sister Sizes Found"))
        if sister_sizes:
            steps.append(_("  Found {count} sister sizes:").format(count=len(sister_sizes)))
            for sister in sister_sizes:
                steps.append(_("    {size}").format(size=sister['size']))
        else:
            steps.append(_("  No valid sister sizes found within the valid range"))
        
        return [str(step) for step in steps]
