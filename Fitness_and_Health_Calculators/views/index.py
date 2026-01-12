from django.shortcuts import render
from django.views.generic import TemplateView


class HealthIndexView(TemplateView):
    template_name = 'fitness_and_health_calculators/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Comprehensive health and fitness calculators list organized by categories
        calculators = [
            # BMI & Body Composition
            {'name': 'BMI Calculator', 'url': 'bmi-calculator', 'category': 'BMI & Body Composition', 'description': 'Calculate your Body Mass Index and health category'},
            {'name': 'Anorexic BMI Calculator', 'url': 'anorexic-bmi-calculator', 'category': 'BMI & Body Composition', 'description': 'Specialized BMI calculator for eating disorder assessment'},
            {'name': 'Body Fat Calculator', 'url': 'body-fat-calculator', 'category': 'BMI & Body Composition', 'description': 'Calculate body fat percentage using various methods'},
            {'name': 'Army Body Fat Calculator', 'url': 'army-body-fat-calculator', 'category': 'BMI & Body Composition', 'description': 'Calculate body fat using Army measurement standards'},
            {'name': 'Body Surface Area Calculator', 'url': 'body-surface-area-calculator', 'category': 'BMI & Body Composition', 'description': 'Calculate body surface area for medical purposes'},
            {'name': 'Body Type Calculator', 'url': 'body-type-calculator', 'category': 'BMI & Body Composition', 'description': 'Determine your body type (ectomorph, mesomorph, endomorph)'},
            {'name': 'Lean Body Mass Calculator', 'url': 'lean-body-mass-calculator', 'category': 'BMI & Body Composition', 'description': 'Calculate lean body mass and muscle percentage'},
            {'name': 'Healthy Weight Calculator', 'url': 'healthy-weight-calculator', 'category': 'BMI & Body Composition', 'description': 'Find your healthy weight range'},
            {'name': 'Ideal Weight Calculator', 'url': 'ideal-weight-calculator', 'category': 'BMI & Body Composition', 'description': 'Calculate ideal weight based on height'},
            {'name': 'Overweight Calculator', 'url': 'overweight-calculator', 'category': 'BMI & Body Composition', 'description': 'Determine if you are overweight and by how much'},
            
            # Metabolism & Calories
            {'name': 'BMR Calculator', 'url': 'bmr-calculator', 'category': 'Metabolism & Calories', 'description': 'Calculate your Basal Metabolic Rate'},
            {'name': 'TDEE Calculator', 'url': 'tdee-calculator', 'category': 'Metabolism & Calories', 'description': 'Calculate Total Daily Energy Expenditure'},
            {'name': 'Calorie Calculator', 'url': 'calorie-calculator', 'category': 'Metabolism & Calories', 'description': 'Calculate daily calorie needs for your goals'},
            {'name': 'Calories Burned Calculator', 'url': 'calories-burned-calculator', 'category': 'Metabolism & Calories', 'description': 'Calculate calories burned during exercise'},
            {'name': 'Macro Calculator', 'url': 'macro-calculator', 'category': 'Metabolism & Calories', 'description': 'Calculate macronutrient distribution'},
            
            # Nutrition & Diet
            {'name': 'Carbohydrate Calculator', 'url': 'carbohydrate-calculator', 'category': 'Nutrition & Diet', 'description': 'Calculate daily carbohydrate intake'},
            {'name': 'Fat Intake Calculator', 'url': 'fat-intake-calculator', 'category': 'Nutrition & Diet', 'description': 'Calculate recommended fat intake'},
            {'name': 'Protein Calculator', 'url': 'protein-calculator', 'category': 'Nutrition & Diet', 'description': 'Calculate protein needs based on weight and goals'},
            {'name': 'Weight Watcher Points Calculator', 'url': 'weight-watcher-points-calculator', 'category': 'Nutrition & Diet', 'description': 'Calculate Weight Watchers points for foods'},
            
            # Fitness & Exercise
            {'name': 'Target Heart Rate Calculator', 'url': 'target-heart-rate-calculator', 'category': 'Fitness & Exercise', 'description': 'Calculate your target heart rate zones'},
            {'name': 'One Rep Max Calculator', 'url': 'one-rep-max-calculator', 'category': 'Fitness & Exercise', 'description': 'Estimate your one rep max for weight training'},
            {'name': 'Pace Calculator', 'url': 'pace-calculator', 'category': 'Fitness & Exercise', 'description': 'Calculate running or cycling pace'},
            
            # Pregnancy & Conception
            {'name': 'Due Date Calculator', 'url': 'due-date-calculator', 'category': 'Pregnancy & Conception', 'description': 'Calculate estimated due date during pregnancy'},
            {'name': 'Ovulation Calculator', 'url': 'ovulation-calculator', 'category': 'Pregnancy & Conception', 'description': 'Calculate ovulation dates for fertility planning'},
            {'name': 'Conception Calculator', 'url': 'conception-calculator', 'category': 'Pregnancy & Conception', 'description': 'Calculate conception date from due date'},
            {'name': 'Pregnancy Calculator', 'url': 'pregnancy-calculator', 'category': 'Pregnancy & Conception', 'description': 'Track pregnancy week and due date'},
            {'name': 'Pregnancy Conception Calculator', 'url': 'pregnancy-conception-calculator', 'category': 'Pregnancy & Conception', 'description': 'Calculate pregnancy timeline from conception'},
            {'name': 'Pregnancy Weight Gain Calculator', 'url': 'pregnancy-weight-gain-calculator', 'category': 'Pregnancy & Conception', 'description': 'Track healthy pregnancy weight gain'},
            {'name': 'Period Calculator', 'url': 'period-calculator', 'category': 'Pregnancy & Conception', 'description': 'Predict next period and cycle dates'},
            
            # Health & Medical
            {'name': 'BAC Calculator', 'url': 'bac-calculator', 'category': 'Health & Medical', 'description': 'Calculate blood alcohol content level'},
            {'name': 'GFR Calculator', 'url': 'gfr-calculator', 'category': 'Health & Medical', 'description': 'Calculate glomerular filtration rate for kidney function'},
        ]
        
        context['calculators'] = calculators
        context['total_calculators'] = len(calculators)
        
        # Get unique categories
        categories_set = set(calc['category'] for calc in calculators)
        context['categories'] = sorted(list(categories_set))
        
        return context
