from django.shortcuts import render
from django.views.generic import TemplateView


class OtherIndexView(TemplateView):
    template_name = 'other_calculators/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Comprehensive other calculators list organized by categories
        calculators = [
            # Time & Date
            {'name': 'Time Calculator', 'url': 'time-calculator', 'category': 'Time & Date', 'description': 'Calculate time differences and durations'},
            {'name': 'Date Calculator', 'url': 'date-calculator', 'category': 'Time & Date', 'description': 'Calculate dates and days between dates'},
            {'name': 'Day Counter', 'url': 'day-counter', 'category': 'Time & Date', 'description': 'Count days between two dates'},
            {'name': 'Day of the Week Calculator', 'url': 'day-of-the-week-calculator', 'category': 'Time & Date', 'description': 'Find day of the week for any date'},
            {'name': 'Day of Week Calculator', 'url': 'day-of-week-calculator', 'category': 'Time & Date', 'description': 'Determine day of week for dates'},
            {'name': 'Time Duration Calculator', 'url': 'time-duration-calculator', 'category': 'Time & Date', 'description': 'Calculate time duration between events'},
            {'name': 'Time Card Calculator', 'url': 'time-card-calculator', 'category': 'Time & Date', 'description': 'Calculate work hours and time card totals'},
            {'name': 'Time Zone Calculator', 'url': 'time-zone-calculator', 'category': 'Time & Date', 'description': 'Convert times between time zones'},
            {'name': 'Hours Calculator', 'url': 'hours-calculator', 'category': 'Time & Date', 'description': 'Calculate total hours and minutes'},
            {'name': 'Sleep Calculator', 'url': 'sleep-calculator', 'category': 'Time & Date', 'description': 'Calculate optimal sleep schedules'},
            
            # Personal Information
            {'name': 'Age Calculator', 'url': 'age-calculator', 'category': 'Personal Information', 'description': 'Calculate age from birth date'},
            {'name': 'Height Calculator', 'url': 'height-calculator', 'category': 'Personal Information', 'description': 'Convert and calculate height measurements'},
            {'name': 'Weight Calculator', 'url': 'weight-calculator', 'category': 'Personal Information', 'description': 'Convert weight units and measurements'},
            {'name': 'GPA Calculator', 'url': 'gpa-calculator', 'category': 'Personal Information', 'description': 'Calculate grade point average'},
            {'name': 'Grade Calculator', 'url': 'grade-calculator', 'category': 'Personal Information', 'description': 'Calculate final grades and percentages'},
            {'name': 'Bra Size Calculator', 'url': 'bra-size-calculator', 'category': 'Personal Information', 'description': 'Find your bra size with proper measurements'},
            {'name': 'Shoe Size Conversion', 'url': 'shoe-size-conversion', 'category': 'Personal Information', 'description': 'Convert shoe sizes between different countries'},
            
            # Conversions
            {'name': 'Conversion Calculator', 'url': 'conversion-calculator', 'category': 'Conversions', 'description': 'Convert between various units of measurement'},
            {'name': 'Roman Numeral Converter', 'url': 'roman-numeral-converter', 'category': 'Conversions', 'description': 'Convert numbers to and from Roman numerals'},
            
            # Energy & Physics
            {'name': 'Electricity Calculator', 'url': 'electricity-calculator', 'category': 'Energy & Physics', 'description': 'Calculate electrical power and consumption'},
            {'name': 'Voltage Drop Calculator', 'url': 'voltage-drop-calculator', 'category': 'Energy & Physics', 'description': 'Calculate voltage drop in electrical circuits'},
            {'name': 'Ohms Law Calculator', 'url': 'ohms-law-calculator', 'category': 'Energy & Physics', 'description': 'Calculate voltage, current, resistance using Ohms Law'},
            {'name': 'Resistor Calculator', 'url': 'resistor-calculator', 'category': 'Energy & Physics', 'description': 'Calculate resistor values and color codes'},
            {'name': 'BTU Calculator', 'url': 'btu-calculator', 'category': 'Energy & Physics', 'description': 'Calculate BTU for heating and cooling'},
            {'name': 'Horsepower Calculator', 'url': 'horsepower-calculator', 'category': 'Energy & Physics', 'description': 'Calculate horsepower from torque and RPM'},
            {'name': 'Engine Horsepower Calculator', 'url': 'engine-horsepower-calculator', 'category': 'Energy & Physics', 'description': 'Estimate engine horsepower'},
            
            # Chemistry
            {'name': 'Molarity Calculator', 'url': 'molarity-calculator', 'category': 'Chemistry', 'description': 'Calculate molarity of solutions'},
            {'name': 'Molecular Weight Calculator', 'url': 'molecular-weight-calculator', 'category': 'Chemistry', 'description': 'Calculate molecular weights of compounds'},
            {'name': 'Density Calculator', 'url': 'density-calculator', 'category': 'Chemistry', 'description': 'Calculate density from mass and volume'},
            {'name': 'Mass Calculator', 'url': 'mass-calculator', 'category': 'Chemistry', 'description': 'Calculate mass from density and volume'},
            
            # Weather
            {'name': 'Heat Index Calculator', 'url': 'heat-index-calculator', 'category': 'Weather', 'description': 'Calculate heat index from temperature and humidity'},
            {'name': 'Dew Point Calculator', 'url': 'dew-point-calculator', 'category': 'Weather', 'description': 'Calculate dew point temperature'},
            {'name': 'Wind Chill Calculator', 'url': 'wind-chill-calculator', 'category': 'Weather', 'description': 'Calculate wind chill from temperature and wind speed'},
            
            # Automotive
            {'name': 'Fuel Cost Calculator', 'url': 'fuel-cost-calculator', 'category': 'Automotive', 'description': 'Calculate fuel costs for trips'},
            {'name': 'Gas Mileage Calculator', 'url': 'gas-mileage-calculator', 'category': 'Automotive', 'description': 'Calculate gas mileage and fuel efficiency'},
            {'name': 'Mileage Calculator', 'url': 'mileage-calculator', 'category': 'Automotive', 'description': 'Calculate distance traveled and mileage'},
            {'name': 'Tire Size Conversion', 'url': 'tire-size-calculator', 'category': 'Automotive', 'description': 'Convert tire sizes between formats'},
            {'name': 'Speed Calculator', 'url': 'speed-calculator', 'category': 'Automotive', 'description': 'Calculate speed, distance, and time'},
            
            # Construction & Materials
            {'name': 'Concrete Calculator', 'url': 'concrete-calculator', 'category': 'Construction & Materials', 'description': 'Calculate concrete needed for projects'},
            {'name': 'Gravel Calculator', 'url': 'gravel-calculator', 'category': 'Construction & Materials', 'description': 'Calculate gravel and stone material amounts'},
            {'name': 'Mulch Calculator', 'url': 'mulch-calculator', 'category': 'Construction & Materials', 'description': 'Calculate mulch needed for landscaping'},
            {'name': 'Tile Calculator', 'url': 'tile-calculator', 'category': 'Construction & Materials', 'description': 'Calculate tiles needed for projects'},
            {'name': 'Roofing Calculator', 'url': 'roofing-calculator', 'category': 'Construction & Materials', 'description': 'Calculate roofing materials needed'},
            {'name': 'Stair Calculator', 'url': 'stair-calculator', 'category': 'Construction & Materials', 'description': 'Calculate stair dimensions and rise/run'},
            {'name': 'Square Footage Calculator', 'url': 'square-footage-calculator', 'category': 'Construction & Materials', 'description': 'Calculate square footage of areas'},
            
            # Fun & Utilities
            {'name': 'Tip Calculator', 'url': 'tip-calculator', 'category': 'Fun & Utilities', 'description': 'Calculate tips and splits for meals'},
            {'name': 'Love Calculator', 'url': 'love-calculator', 'category': 'Fun & Utilities', 'description': 'Fun compatibility calculator'},
            {'name': 'Golf Handicap Calculator', 'url': 'golf-handicap-calculator', 'category': 'Fun & Utilities', 'description': 'Calculate golf handicap'},
            {'name': 'Dice Roller', 'url': 'dice-roller', 'category': 'Fun & Utilities', 'description': 'Roll virtual dice'},
            {'name': 'Password Generator', 'url': 'password-generator', 'category': 'Fun & Utilities', 'description': 'Generate secure passwords'},
            
            # Economics & Network
            {'name': 'GDP Calculator', 'url': 'gdp-calculator', 'category': 'Economics & Network', 'description': 'Calculate GDP and economic indicators'},
            {'name': 'IP Subnet Calculator', 'url': 'ip-subnet-calculator', 'category': 'Economics & Network', 'description': 'Calculate IP subnet masks and ranges'},
            {'name': 'Bandwidth Calculator', 'url': 'bandwidth-calculator', 'category': 'Economics & Network', 'description': 'Calculate bandwidth and data transfer'},
        ]
        
        context['calculators'] = calculators
        context['total_calculators'] = len(calculators)
        
        # Get unique categories
        categories_set = set(calc['category'] for calc in calculators)
        context['categories'] = sorted(list(categories_set))
        
        return context
