from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.translation import gettext as _


class HealthIndexView(TemplateView):
    template_name = 'fitness_and_health_calculators/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Comprehensive health and fitness calculators list organized by categories
        calculators = [
            # BMI & Body Composition
            {'name': _('BMI Calculator'), 'url': 'bmi-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate your Body Mass Index and health category'), 'icon': 'fas fa-weight-scale'},
            {'name': _('Anorexic BMI Calculator'), 'url': 'anorexic-bmi-calculator', 'category': _('BMI & Body Composition'), 'description': _('Specialized BMI calculator for eating disorder assessment'), 'icon': 'fas fa-triangle-exclamation'},
            {'name': _('Body Fat Calculator'), 'url': 'body-fat-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate body fat percentage using various methods'), 'icon': 'fas fa-percent'},
            {'name': _('Army Body Fat Calculator'), 'url': 'army-body-fat-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate body fat using Army measurement standards'), 'icon': 'fas fa-shield-halved'},
            {'name': _('Body Surface Area Calculator'), 'url': 'body-surface-area-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate body surface area for medical purposes'), 'icon': 'fas fa-ruler-combined'},
            {'name': _('Body Type Calculator'), 'url': 'body-type-calculator', 'category': _('BMI & Body Composition'), 'description': _('Determine your body type (ectomorph, mesomorph, endomorph)'), 'icon': 'fas fa-person'},
            {'name': _('Lean Body Mass Calculator'), 'url': 'lean-body-mass-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate lean body mass and muscle percentage'), 'icon': 'fas fa-dumbbell'},
            {'name': _('Healthy Weight Calculator'), 'url': 'healthy-weight-calculator', 'category': _('BMI & Body Composition'), 'description': _('Find your healthy weight range'), 'icon': 'fas fa-heart-pulse'},
            {'name': _('Ideal Weight Calculator'), 'url': 'ideal-weight-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate ideal weight based on height'), 'icon': 'fas fa-bullseye'},
            {'name': _('Overweight Calculator'), 'url': 'overweight-calculator', 'category': _('BMI & Body Composition'), 'description': _('Determine if you are overweight and by how much'), 'icon': 'fas fa-scale-balanced'},
            
            # Metabolism & Calories
            {'name': _('BMR Calculator'), 'url': 'bmr-calculator', 'category': _('Metabolism & Calories'), 'description': _('Calculate your Basal Metabolic Rate'), 'icon': 'fas fa-fire'},
            {'name': _('TDEE Calculator'), 'url': 'tdee-calculator', 'category': _('Metabolism & Calories'), 'description': _('Calculate Total Daily Energy Expenditure'), 'icon': 'fas fa-bolt'},
            {'name': _('Calorie Calculator'), 'url': 'calorie-calculator', 'category': _('Metabolism & Calories'), 'description': _('Calculate daily calorie needs for your goals'), 'icon': 'fas fa-chart-pie'},
            {'name': _('Calories Burned Calculator'), 'url': 'calories-burned-calculator', 'category': _('Metabolism & Calories'), 'description': _('Calculate calories burned during exercise'), 'icon': 'fas fa-fire-flame-curved'},
            {'name': _('Macro Calculator'), 'url': 'macro-calculator', 'category': _('Metabolism & Calories'), 'description': _('Calculate macronutrient distribution'), 'icon': 'fas fa-chart-simple'},
            
            # Nutrition & Diet
            {'name': _('Carbohydrate Calculator'), 'url': 'carbohydrate-calculator', 'category': _('Nutrition & Diet'), 'description': _('Calculate daily carbohydrate intake'), 'icon': 'fas fa-bread-slice'},
            {'name': _('Fat Intake Calculator'), 'url': 'fat-intake-calculator', 'category': _('Nutrition & Diet'), 'description': _('Calculate recommended fat intake'), 'icon': 'fas fa-droplet'},
            {'name': _('Protein Calculator'), 'url': 'protein-calculator', 'category': _('Nutrition & Diet'), 'description': _('Calculate protein needs based on weight and goals'), 'icon': 'fas fa-drumstick-bite'},
            {'name': _('Weight Watcher Points Calculator'), 'url': 'weight-watcher-points-calculator', 'category': _('Nutrition & Diet'), 'description': _('Calculate Weight Watchers points for foods'), 'icon': 'fas fa-star'},
            {'name': _('Chipotle Nutrition Calculator'), 'url': 'chipotle-nutrition-calculator', 'category': _('Nutrition & Diet'), 'description': _('Build a Chipotle meal and see full nutrition breakdown'), 'icon': 'fas fa-pepper-hot'},
            {'name': _('Starbucks Calorie Calculator'), 'url': 'starbucks-calorie-calculator', 'category': _('Nutrition & Diet'), 'description': _('Customize your Starbucks order and see calories, sugar, and caffeine'), 'icon': 'fas fa-mug-hot'},
            
            # Fitness & Exercise
            {'name': _('Target Heart Rate Calculator'), 'url': 'target-heart-rate-calculator', 'category': _('Fitness & Exercise'), 'description': _('Calculate your target heart rate zones'), 'icon': 'fas fa-heart'},
            {'name': _('One Rep Max Calculator'), 'url': 'one-rep-max-calculator', 'category': _('Fitness & Exercise'), 'description': _('Estimate your one rep max for weight training'), 'icon': 'fas fa-dumbbell'},
            {'name': _('Pace Calculator'), 'url': 'pace-calculator', 'category': _('Fitness & Exercise'), 'description': _('Calculate running or cycling pace'), 'icon': 'fas fa-person-running'},
            
            # Pregnancy & Conception
            {'name': _('Due Date Calculator'), 'url': 'due-date-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Calculate estimated due date during pregnancy'), 'icon': 'fas fa-calendar-days'},
            {'name': _('Ovulation Calculator'), 'url': 'ovulation-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Calculate ovulation dates for fertility planning'), 'icon': 'fas fa-calendar-check'},
            {'name': _('Conception Calculator'), 'url': 'conception-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Calculate conception date from due date'), 'icon': 'fas fa-baby'},
            {'name': _('Pregnancy Calculator'), 'url': 'pregnancy-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Track pregnancy week and due date'), 'icon': 'fas fa-person-pregnant'},
            {'name': _('Pregnancy Conception Calculator'), 'url': 'pregnancy-conception-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Calculate pregnancy timeline from conception'), 'icon': 'fas fa-clock'},
            {'name': _('Pregnancy Weight Gain Calculator'), 'url': 'pregnancy-weight-gain-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Track healthy pregnancy weight gain'), 'icon': 'fas fa-weight-hanging'},
            {'name': _('Period Calculator'), 'url': 'period-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Predict next period and cycle dates'), 'icon': 'fas fa-calendar-week'},
            
            # Health & Medical
            {'name': _('BAC Calculator'), 'url': 'bac-calculator', 'category': _('Health & Medical'), 'description': _('Calculate blood alcohol content level'), 'icon': 'fas fa-wine-glass'},
            {'name': _('GFR Calculator'), 'url': 'gfr-calculator', 'category': _('Health & Medical'), 'description': _('Calculate glomerular filtration rate for kidney function'), 'icon': 'fas fa-stethoscope'},
        ]
        
        context['calculators'] = calculators
        context['total_calculators'] = len(calculators)
        
        # Get unique categories
        categories_set = set(calc['category'] for calc in calculators)
        context['categories'] = sorted(list(categories_set))
        
        return context
