from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class DepreciationCalculator(View):
    """
    Class-based view for Depreciation Calculator
    Calculates asset depreciation using various methods.
    """
    template_name = 'financial_calculators/depreciation_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Depreciation Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for depreciation calculations"""
        try:
            data = json.loads(request.body)

            # Asset details
            asset_cost = float(str(data.get('asset_cost', 0)).replace(',', ''))
            salvage_value = float(str(data.get('salvage_value', 0)).replace(',', ''))
            useful_life = int(data.get('useful_life', 5))  # years
            depreciation_method = data.get('method', 'straight_line')
            
            # For declining balance
            db_rate = float(str(data.get('db_rate', 200)).replace(',', ''))  # 200% for double declining
            
            # For units of production
            total_units = int(data.get('total_units', 0))
            units_per_year = data.get('units_per_year', [])  # list of units produced each year

            if asset_cost <= 0:
                return JsonResponse({'success': False, 'error': 'Asset cost must be greater than zero.'}, status=400)
            if useful_life <= 0:
                return JsonResponse({'success': False, 'error': 'Useful life must be greater than zero.'}, status=400)
            if salvage_value < 0:
                return JsonResponse({'success': False, 'error': 'Salvage value cannot be negative.'}, status=400)
            if salvage_value >= asset_cost:
                return JsonResponse({'success': False, 'error': 'Salvage value must be less than asset cost.'}, status=400)

            depreciable_amount = asset_cost - salvage_value
            schedule = []

            if depreciation_method == 'straight_line':
                # Straight-Line Depreciation
                annual_depreciation = depreciable_amount / useful_life
                
                book_value = asset_cost
                accumulated = 0
                
                for year in range(1, useful_life + 1):
                    depreciation = annual_depreciation
                    accumulated += depreciation
                    book_value -= depreciation
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(book_value, 2)
                    })

                result = {
                    'success': True,
                    'method': 'Straight-Line',
                    'formula': 'Depreciation = (Cost - Salvage) / Useful Life',
                    'annual_depreciation': round(annual_depreciation, 2),
                    'monthly_depreciation': round(annual_depreciation / 12, 2)
                }

            elif depreciation_method == 'declining_balance':
                # Declining Balance Depreciation
                rate = db_rate / 100 / useful_life  # e.g., 200% / 5 years = 40%
                
                book_value = asset_cost
                accumulated = 0
                
                for year in range(1, useful_life + 1):
                    # Cannot depreciate below salvage value
                    depreciation = book_value * rate
                    
                    if book_value - depreciation < salvage_value:
                        depreciation = book_value - salvage_value
                    
                    accumulated += depreciation
                    book_value -= depreciation
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'depreciation_rate': round(rate * 100, 2),
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(book_value, 2)
                    })
                    
                    if book_value <= salvage_value:
                        break

                result = {
                    'success': True,
                    'method': f'{int(db_rate)}% Declining Balance',
                    'formula': 'Depreciation = Book Value × Rate',
                    'depreciation_rate': round(rate * 100, 2),
                    'first_year_depreciation': round(schedule[0]['depreciation'], 2) if schedule else 0
                }

            elif depreciation_method == 'double_declining':
                # Double Declining Balance (DDB)
                rate = 2 / useful_life
                
                book_value = asset_cost
                accumulated = 0
                
                for year in range(1, useful_life + 1):
                    depreciation = book_value * rate
                    
                    # Cannot depreciate below salvage value
                    if book_value - depreciation < salvage_value:
                        depreciation = book_value - salvage_value
                    
                    accumulated += depreciation
                    book_value -= depreciation
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'depreciation_rate': round(rate * 100, 2),
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(book_value, 2)
                    })
                    
                    if book_value <= salvage_value:
                        break

                result = {
                    'success': True,
                    'method': 'Double Declining Balance (DDB)',
                    'formula': 'Depreciation = Book Value × (2 / Useful Life)',
                    'depreciation_rate': round(rate * 100, 2),
                    'first_year_depreciation': round(schedule[0]['depreciation'], 2) if schedule else 0
                }

            elif depreciation_method == 'sum_of_years':
                # Sum of Years' Digits (SYD)
                sum_of_years = sum(range(1, useful_life + 1))
                
                book_value = asset_cost
                accumulated = 0
                
                for year in range(1, useful_life + 1):
                    remaining_life = useful_life - year + 1
                    fraction = remaining_life / sum_of_years
                    depreciation = depreciable_amount * fraction
                    
                    accumulated += depreciation
                    book_value -= depreciation
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'remaining_life': remaining_life,
                        'fraction': f'{remaining_life}/{sum_of_years}',
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(book_value, 2)
                    })

                result = {
                    'success': True,
                    'method': "Sum of Years' Digits (SYD)",
                    'formula': 'Depreciation = (Remaining Life / Sum of Years) × Depreciable Amount',
                    'sum_of_years': sum_of_years,
                    'first_year_depreciation': round(schedule[0]['depreciation'], 2) if schedule else 0
                }

            elif depreciation_method == 'units_of_production':
                # Units of Production
                if total_units <= 0:
                    return JsonResponse({'success': False, 'error': 'Total units must be greater than zero for this method.'}, status=400)
                
                depreciation_per_unit = depreciable_amount / total_units
                
                book_value = asset_cost
                accumulated = 0
                total_units_produced = 0
                
                # If units_per_year not provided, assume equal distribution
                if not units_per_year:
                    units_per_year = [total_units / useful_life] * useful_life
                
                try:
                    units_list = [float(str(u).replace(',', '')) for u in units_per_year]
                except:
                    units_list = [total_units / useful_life] * useful_life
                
                for year, units in enumerate(units_list, 1):
                    depreciation = units * depreciation_per_unit
                    
                    # Cannot depreciate below salvage value
                    if book_value - depreciation < salvage_value:
                        depreciation = book_value - salvage_value
                    
                    accumulated += depreciation
                    book_value -= depreciation
                    total_units_produced += units
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'units_produced': int(units),
                        'depreciation_per_unit': round(depreciation_per_unit, 4),
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(book_value, 2),
                        'total_units_to_date': int(total_units_produced)
                    })
                    
                    if book_value <= salvage_value:
                        break

                result = {
                    'success': True,
                    'method': 'Units of Production',
                    'formula': 'Depreciation = Units Produced × Depreciation per Unit',
                    'total_units': total_units,
                    'depreciation_per_unit': round(depreciation_per_unit, 4)
                }

            elif depreciation_method == 'macrs':
                # MACRS (Modified Accelerated Cost Recovery System)
                # Common MACRS rates for different property classes
                macrs_rates = {
                    3: [33.33, 44.45, 14.81, 7.41],
                    5: [20.00, 32.00, 19.20, 11.52, 11.52, 5.76],
                    7: [14.29, 24.49, 17.49, 12.49, 8.93, 8.92, 8.93, 4.46],
                    10: [10.00, 18.00, 14.40, 11.52, 9.22, 7.37, 6.55, 6.55, 6.56, 6.55, 3.28],
                    15: [5.00, 9.50, 8.55, 7.70, 6.93, 6.23, 5.90, 5.90, 5.91, 5.90, 5.91, 5.90, 5.91, 5.90, 5.91, 2.95],
                }
                
                if useful_life not in macrs_rates:
                    return JsonResponse({'success': False, 'error': 'MACRS requires property class of 3, 5, 7, 10, or 15 years.'}, status=400)
                
                rates = macrs_rates[useful_life]
                book_value = asset_cost
                accumulated = 0
                
                # MACRS doesn't use salvage value
                for year, rate in enumerate(rates, 1):
                    depreciation = asset_cost * (rate / 100)
                    accumulated += depreciation
                    book_value -= depreciation
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'macrs_rate': rate,
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(max(0, book_value), 2)
                    })

                result = {
                    'success': True,
                    'method': f'MACRS ({useful_life}-Year Property)',
                    'formula': 'Depreciation = Cost × MACRS Rate',
                    'property_class': f'{useful_life}-Year',
                    'note': 'MACRS does not consider salvage value'
                }

            else:
                return JsonResponse({'success': False, 'error': 'Invalid depreciation method.'}, status=400)

            # Add common fields to result
            result.update({
                'asset_cost': round(asset_cost, 2),
                'salvage_value': round(salvage_value, 2),
                'depreciable_amount': round(depreciable_amount, 2),
                'useful_life': useful_life,
                'total_depreciation': round(sum([s['depreciation'] for s in schedule]), 2),
                'schedule': schedule
            })

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
