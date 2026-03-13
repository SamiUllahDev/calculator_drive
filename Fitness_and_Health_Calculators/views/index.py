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
            {'name': _('BMI Calculator'), 'url': 'bmi-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate your Body Mass Index and health category'), },
            {'name': _('Anorexic BMI Calculator'), 'url': 'anorexic-bmi-calculator', 'category': _('BMI & Body Composition'), 'description': _('Specialized BMI calculator for eating disorder assessment'), },
            {'name': _('Body Fat Calculator'), 'url': 'body-fat-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate body fat percentage using various methods'), },
            {'name': _('Army Body Fat Calculator'), 'url': 'army-body-fat-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate body fat using Army measurement standards'), },
            {'name': _('Body Surface Area Calculator'), 'url': 'body-surface-area-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate body surface area for medical purposes'), },
            {'name': _('Body Type Calculator'), 'url': 'body-type-calculator', 'category': _('BMI & Body Composition'), 'description': _('Determine your body type (ectomorph, mesomorph, endomorph)'), },
            {'name': _('Lean Body Mass Calculator'), 'url': 'lean-body-mass-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate lean body mass and muscle percentage'), },
            {'name': _('Healthy Weight Calculator'), 'url': 'healthy-weight-calculator', 'category': _('BMI & Body Composition'), 'description': _('Find your healthy weight range'), },
            {'name': _('Ideal Weight Calculator'), 'url': 'ideal-weight-calculator', 'category': _('BMI & Body Composition'), 'description': _('Calculate ideal weight based on height'), },
            {'name': _('Overweight Calculator'), 'url': 'overweight-calculator', 'category': _('BMI & Body Composition'), 'description': _('Determine if you are overweight and by how much'), },
            
            # Metabolism & Calories
            {'name': _('BMR Calculator'), 'url': 'bmr-calculator', 'category': _('Metabolism & Calories'), 'description': _('Calculate your Basal Metabolic Rate'), },
            {'name': _('TDEE Calculator'), 'url': 'tdee-calculator', 'category': _('Metabolism & Calories'), 'description': _('Calculate Total Daily Energy Expenditure'), },
            {'name': _('Calorie Calculator'), 'url': 'calorie-calculator', 'category': _('Metabolism & Calories'), 'description': _('Calculate daily calorie needs for your goals'), },
            {'name': _('Calories Burned Calculator'), 'url': 'calories-burned-calculator', 'category': _('Metabolism & Calories'), 'description': _('Calculate calories burned during exercise'), },
            {'name': _('Macro Calculator'), 'url': 'macro-calculator', 'category': _('Metabolism & Calories'), 'description': _('Calculate macronutrient distribution'), },
            
            # Nutrition & Diet
            {'name': _('Carbohydrate Calculator'), 'url': 'carbohydrate-calculator', 'category': _('Nutrition & Diet'), 'description': _('Calculate daily carbohydrate intake'), },
            {'name': _('Fat Intake Calculator'), 'url': 'fat-intake-calculator', 'category': _('Nutrition & Diet'), 'description': _('Calculate recommended fat intake'), },
            {'name': _('Protein Calculator'), 'url': 'protein-calculator', 'category': _('Nutrition & Diet'), 'description': _('Calculate protein needs based on weight and goals'), },
            {'name': _('Weight Watcher Points Calculator'), 'url': 'weight-watcher-points-calculator', 'category': _('Nutrition & Diet'), 'description': _('Calculate Weight Watchers points for foods'), },
            {'name': _('Chipotle Nutrition Calculator'), 'url': 'chipotle-nutrition-calculator', 'category': _('Nutrition & Diet'), 'description': _('Build a Chipotle meal and see full nutrition breakdown'), },
            {'name': _('Starbucks Calorie Calculator'), 'url': 'starbucks-calorie-calculator', 'category': _('Nutrition & Diet'), 'description': _('Customize your Starbucks order and see calories, sugar, and caffeine'), },
            
            # Fitness & Exercise
            {'name': _('Target Heart Rate Calculator'), 'url': 'target-heart-rate-calculator', 'category': _('Fitness & Exercise'), 'description': _('Calculate your target heart rate zones'), },
            {'name': _('One Rep Max Calculator'), 'url': 'one-rep-max-calculator', 'category': _('Fitness & Exercise'), 'description': _('Estimate your one rep max for weight training'), },
            {'name': _('Pace Calculator'), 'url': 'pace-calculator', 'category': _('Fitness & Exercise'), 'description': _('Calculate running or cycling pace'), },
            
            # Pregnancy & Conception
            {'name': _('Due Date Calculator'), 'url': 'due-date-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Calculate estimated due date during pregnancy'), },
            {'name': _('Ovulation Calculator'), 'url': 'ovulation-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Calculate ovulation dates for fertility planning'), },
            {'name': _('Conception Calculator'), 'url': 'conception-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Calculate conception date from due date'), },
            {'name': _('Pregnancy Calculator'), 'url': 'pregnancy-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Track pregnancy week and due date'), },
            {'name': _('Pregnancy Conception Calculator'), 'url': 'pregnancy-conception-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Calculate pregnancy timeline from conception'), },
            {'name': _('Pregnancy Weight Gain Calculator'), 'url': 'pregnancy-weight-gain-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Track healthy pregnancy weight gain'), },
            {'name': _('Period Calculator'), 'url': 'period-calculator', 'category': _('Pregnancy & Conception'), 'description': _('Predict next period and cycle dates'), },
            
            # Health & Medical
            {'name': _('BAC Calculator'), 'url': 'bac-calculator', 'category': _('Health & Medical'), 'description': _('Calculate blood alcohol content level'), },
            {'name': _('GFR Calculator'), 'url': 'gfr-calculator', 'category': _('Health & Medical'), 'description': _('Calculate glomerular filtration rate for kidney function'), },
        ]
        
        context['calculators'] = calculators
        context['total_calculators'] = len(calculators)
        
        # Get unique categories
        categories_set = set(calc['category'] for calc in calculators)
        context['categories'] = sorted(list(categories_set))
        
        return context
