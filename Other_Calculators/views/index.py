from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.translation import gettext as _


class OtherIndexView(TemplateView):
    template_name = 'other_calculators/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Comprehensive other calculators list organized by categories
        calculators = [
            # Time & Date
            {'name': _('Time Calculator'), 'url': 'time-calculator', 'category': _('Time & Date'), 'description': _('Calculate time differences and durations'), 'icon': 'far fa-clock'},
            {'name': _('Date Calculator'), 'url': 'date-calculator', 'category': _('Time & Date'), 'description': _('Calculate dates and days between dates'), 'icon': 'fas fa-calendar-days'},
            {'name': _('Day Counter'), 'url': 'day-counter', 'category': _('Time & Date'), 'description': _('Count days between two dates'), 'icon': 'fas fa-hashtag'},
            {'name': _('Day of the Week Calculator'), 'url': 'day-of-the-week-calculator', 'category': _('Time & Date'), 'description': _('Find day of the week for any date'), 'icon': 'fas fa-calendar-week'},
            {'name': _('Day of Week Calculator'), 'url': 'day-of-week-calculator', 'category': _('Time & Date'), 'description': _('Determine day of week for dates'), 'icon': 'fas fa-calendar-check'},
            {'name': _('Time Duration Calculator'), 'url': 'time-duration-calculator', 'category': _('Time & Date'), 'description': _('Calculate time duration between events'), 'icon': 'fas fa-hourglass-half'},
            {'name': _('Time Card Calculator'), 'url': 'time-card-calculator', 'category': _('Time & Date'), 'description': _('Calculate work hours and time card totals'), 'icon': 'fas fa-id-card'},
            {'name': _('Time Zone Calculator'), 'url': 'time-zone-calculator', 'category': _('Time & Date'), 'description': _('Convert times between time zones'), 'icon': 'fas fa-globe'},
            {'name': _('Hours Calculator'), 'url': 'hours-calculator', 'category': _('Time & Date'), 'description': _('Calculate total hours and minutes'), 'icon': 'fas fa-stopwatch'},
            {'name': _('Sleep Calculator'), 'url': 'sleep-calculator', 'category': _('Time & Date'), 'description': _('Calculate optimal sleep schedules'), 'icon': 'fas fa-bed'},
            
            # Personal Information
            {'name': _('Age Calculator'), 'url': 'age-calculator', 'category': _('Personal Information'), 'description': _('Calculate age from birth date'), 'icon': 'fas fa-cake-candles'},
            {'name': _('Height Calculator'), 'url': 'height-calculator', 'category': _('Personal Information'), 'description': _('Convert and calculate height measurements'), 'icon': 'fas fa-ruler-vertical'},
            {'name': _('Weight Calculator'), 'url': 'weight-calculator', 'category': _('Personal Information'), 'description': _('Convert weight units and measurements'), 'icon': 'fas fa-weight-scale'},
            {'name': _('GPA Calculator'), 'url': 'gpa-calculator', 'category': _('Personal Information'), 'description': _('Calculate grade point average'), 'icon': 'fas fa-graduation-cap'},
            {'name': _('Grade Calculator'), 'url': 'grade-calculator', 'category': _('Personal Information'), 'description': _('Calculate final grades and percentages'), 'icon': 'fas fa-chart-simple'},
            {'name': _('Bra Size Calculator'), 'url': 'bra-size-calculator', 'category': _('Personal Information'), 'description': _('Find your bra size with proper measurements'), 'icon': 'fas fa-tape'},
            {'name': _('Shoe Size Conversion'), 'url': 'shoe-size-conversion', 'category': _('Personal Information'), 'description': _('Convert shoe sizes between different countries'), 'icon': 'fas fa-shoe-prints'},
            
            # Conversions
            {'name': _('Conversion Calculator'), 'url': 'conversion-calculator', 'category': _('Conversions'), 'description': _('Convert between various units of measurement'), 'icon': 'fas fa-arrows-rotate'},
            {'name': _('Roman Numeral Converter'), 'url': 'roman-numeral-converter', 'category': _('Conversions'), 'description': _('Convert numbers to and from Roman numerals'), 'icon': 'fas fa-landmark'},
            
            # Energy & Physics
            {'name': _('Electricity Calculator'), 'url': 'electricity-calculator', 'category': _('Energy & Physics'), 'description': _('Calculate electrical power and consumption'), 'icon': 'fas fa-plug'},
            {'name': _('Voltage Drop Calculator'), 'url': 'voltage-drop-calculator', 'category': _('Energy & Physics'), 'description': _('Calculate voltage drop in electrical circuits'), 'icon': 'fas fa-bolt'},
            {'name': _('Ohms Law Calculator'), 'url': 'ohms-law-calculator', 'category': _('Energy & Physics'), 'description': _('Calculate voltage, current, resistance using Ohms Law'), 'icon': 'fas fa-circle-nodes'},
            {'name': _('Resistor Calculator'), 'url': 'resistor-calculator', 'category': _('Energy & Physics'), 'description': _('Calculate resistor values and color codes'), 'icon': 'fas fa-microchip'},
            {'name': _('BTU Calculator'), 'url': 'btu-calculator', 'category': _('Energy & Physics'), 'description': _('Calculate BTU for heating and cooling'), 'icon': 'fas fa-temperature-half'},
            {'name': _('Horsepower Calculator'), 'url': 'horsepower-calculator', 'category': _('Energy & Physics'), 'description': _('Calculate horsepower from torque and RPM'), 'icon': 'fas fa-horse'},
            {'name': _('Engine Horsepower Calculator'), 'url': 'engine-horsepower-calculator', 'category': _('Energy & Physics'), 'description': _('Estimate engine horsepower'), 'icon': 'fas fa-gears'},
            
            # Chemistry
            {'name': _('Molarity Calculator'), 'url': 'molarity-calculator', 'category': _('Chemistry'), 'description': _('Calculate molarity of solutions'), 'icon': 'fas fa-flask'},
            {'name': _('Molecular Weight Calculator'), 'url': 'molecular-weight-calculator', 'category': _('Chemistry'), 'description': _('Calculate molecular weights of compounds'), 'icon': 'fas fa-atom'},
            {'name': _('Density Calculator'), 'url': 'density-calculator', 'category': _('Chemistry'), 'description': _('Calculate density from mass and volume'), 'icon': 'fas fa-cubes'},
            {'name': _('Mass Calculator'), 'url': 'mass-calculator', 'category': _('Chemistry'), 'description': _('Calculate mass from density and volume'), 'icon': 'fas fa-weight-hanging'},
            
            # Weather
            {'name': _('Heat Index Calculator'), 'url': 'heat-index-calculator', 'category': _('Weather'), 'description': _('Calculate heat index from temperature and humidity'), 'icon': 'fas fa-temperature-high'},
            {'name': _('Dew Point Calculator'), 'url': 'dew-point-calculator', 'category': _('Weather'), 'description': _('Calculate dew point temperature'), 'icon': 'fas fa-droplet'},
            {'name': _('Wind Chill Calculator'), 'url': 'wind-chill-calculator', 'category': _('Weather'), 'description': _('Calculate wind chill from temperature and wind speed'), 'icon': 'fas fa-wind'},
            {'name': _('Snow Day Calculator'), 'url': 'snow-day-calculator', 'category': _('Weather'), 'description': _('Predict the likelihood of school closures due to snow'), 'icon': 'fas fa-snowflake'},
            
            # Automotive
            {'name': _('Fuel Cost Calculator'), 'url': 'fuel-cost-calculator', 'category': _('Automotive'), 'description': _('Calculate fuel costs for trips'), 'icon': 'fas fa-gas-pump'},
            {'name': _('Gas Mileage Calculator'), 'url': 'gas-mileage-calculator', 'category': _('Automotive'), 'description': _('Calculate gas mileage and fuel efficiency'), 'icon': 'fas fa-gauge-high'},
            {'name': _('Mileage Calculator'), 'url': 'mileage-calculator', 'category': _('Automotive'), 'description': _('Calculate distance traveled and mileage'), 'icon': 'fas fa-road'},
            {'name': _('Tire Size Conversion'), 'url': 'tire-size-calculator', 'category': _('Automotive'), 'description': _('Convert tire sizes between formats'), 'icon': 'fas fa-circle-notch'},
            {'name': _('Speed Calculator'), 'url': 'speed-calculator', 'category': _('Automotive'), 'description': _('Calculate speed, distance, and time'), 'icon': 'fas fa-tachograph-digital'},
            
            # Construction & Materials
            {'name': _('Concrete Calculator'), 'url': 'concrete-calculator', 'category': _('Construction & Materials'), 'description': _('Calculate concrete needed for projects'), 'icon': 'fas fa-truck'},
            {'name': _('Gravel Calculator'), 'url': 'gravel-calculator', 'category': _('Construction & Materials'), 'description': _('Calculate gravel and stone material amounts'), 'icon': 'fas fa-mound'},
            {'name': _('Mulch Calculator'), 'url': 'mulch-calculator', 'category': _('Construction & Materials'), 'description': _('Calculate mulch needed for landscaping'), 'icon': 'fas fa-leaf'},
            {'name': _('Tile Calculator'), 'url': 'tile-calculator', 'category': _('Construction & Materials'), 'description': _('Calculate tiles needed for projects'), 'icon': 'fas fa-border-all'},
            {'name': _('Roofing Calculator'), 'url': 'roofing-calculator', 'category': _('Construction & Materials'), 'description': _('Calculate roofing materials needed'), 'icon': 'fas fa-house-chimney'},
            {'name': _('Stair Calculator'), 'url': 'stair-calculator', 'category': _('Construction & Materials'), 'description': _('Calculate stair dimensions and rise/run'), 'icon': 'fas fa-stairs'},
            {'name': _('Square Footage Calculator'), 'url': 'square-footage-calculator', 'category': _('Construction & Materials'), 'description': _('Calculate square footage of areas'), 'icon': 'fas fa-ruler-combined'},
            
            # Fun & Utilities
            {'name': _('Tip Calculator'), 'url': 'tip-calculator', 'category': _('Fun & Utilities'), 'description': _('Calculate tips and splits for meals'), 'icon': 'fas fa-hand-holding-dollar'},
            {'name': _('Love Calculator'), 'url': 'love-calculator', 'category': _('Fun & Utilities'), 'description': _('Fun compatibility calculator'), 'icon': 'fas fa-heart'},
            {'name': _('Golf Handicap Calculator'), 'url': 'golf-handicap-calculator', 'category': _('Fun & Utilities'), 'description': _('Calculate golf handicap'), 'icon': 'fas fa-golf-ball-tee'},
            {'name': _('Dice Roller'), 'url': 'dice-roller', 'category': _('Fun & Utilities'), 'description': _('Roll virtual dice'), 'icon': 'fas fa-dice'},
            {'name': _('Password Generator'), 'url': 'password-generator', 'category': _('Fun & Utilities'), 'description': _('Generate secure passwords'), 'icon': 'fas fa-key'},
            {'name': _('Female Delusion Calculator'), 'url': 'female-delusion-calculator', 'category': _('Fun & Utilities'), 'description': _('Find the statistical probability of your ideal partner'), 'icon': 'fas fa-venus'},
            {'name': _('Schedule 1 Calculator'), 'url': 'schedule-1-calculator', 'category': _('Fun & Utilities'), 'description': _('Calculate mix profits and effects for the game Schedule I'), 'icon': 'fas fa-gamepad'},
            {'name': _('GAG Calculator'), 'url': 'gag-calculator', 'category': _('Fun & Utilities'), 'description': _('Rate yourself and discover your attractiveness grade'), 'icon': 'fas fa-star'},
            
            # Economics & Network
            {'name': _('GDP Calculator'), 'url': 'gdp-calculator', 'category': _('Economics & Network'), 'description': _('Calculate GDP and economic indicators'), 'icon': 'fas fa-chart-line'},
            {'name': _('IP Subnet Calculator'), 'url': 'ip-subnet-calculator', 'category': _('Economics & Network'), 'description': _('Calculate IP subnet masks and ranges'), 'icon': 'fas fa-network-wired'},
            {'name': _('Bandwidth Calculator'), 'url': 'bandwidth-calculator', 'category': _('Economics & Network'), 'description': _('Calculate bandwidth and data transfer'), 'icon': 'fas fa-wifi'},

            # Sports & Vehicles
            {'name': _('Tire Pressure Calculator'), 'url': 'silca-tire-pressure-calculator', 'category': _('Sports & Vehicles'), 'description': _('Silca-style optimal tire pressure for cycling'), 'icon': 'fas fa-bicycle'},

            # Crafts & Sewing
            {'name': _('Circle Skirt Calculator'), 'url': 'circle-skirt-calculator', 'category': _('Crafts & Sewing'), 'description': _('Calculate fabric and cutting measurements for circle skirts'), 'icon': 'fas fa-scissors'},
        ]
        
        context['calculators'] = calculators
        context['total_calculators'] = len(calculators)
        
        # Get unique categories
        categories_set = set(calc['category'] for calc in calculators)
        context['categories'] = sorted(list(categories_set))
        
        return context
