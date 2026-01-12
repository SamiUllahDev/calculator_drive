from django.urls import path
from .views.index import HealthIndexView
from .views.bmi_calculator import BmiCalculator
from .views.calorie_calculator import CalorieCalculator
from .views.body_fat_calculator import BodyFatCalculator
from .views.bmr_calculator import BmrCalculator
from .views.macro_calculator import MacroCalculator
from .views.ideal_weight_calculator import IdealWeightCalculator
from .views.pregnancy_calculator import PregnancyCalculator
from .views.pregnancy_weight_gain_calculator import PregnancyWeightGainCalculator
from .views.pregnancy_conception_calculator import PregnancyConceptionCalculator
from .views.due_date_calculator import DueDateCalculator
from .views.pace_calculator import PaceCalculator
from .views.army_body_fat_calculator import ArmyBodyFatCalculator
from .views.carbohydrate_calculator import CarbohydrateCalculator
from .views.lean_body_mass_calculator import LeanBodyMassCalculator
from .views.healthy_weight_calculator import HealthyWeightCalculator
from .views.calories_burned_calculator import CaloriesBurnedCalculator
from .views.one_rep_max_calculator import OneRepMaxCalculator
from .views.target_heart_rate_calculator import TargetHeartRateCalculator
from .views.protein_calculator import ProteinCalculator
from .views.fat_intake_calculator import FatIntakeCalculator
from .views.tdee_calculator import TdeeCalculator
from .views.ovulation_calculator import OvulationCalculator
from .views.conception_calculator import ConceptionCalculator
from .views.period_calculator import PeriodCalculator
from .views.gfr_calculator import GfrCalculator
from .views.body_type_calculator import BodyTypeCalculator
from .views.body_surface_area_calculator import BodySurfaceAreaCalculator
from .views.bac_calculator import BacCalculator
from .views.anorexic_bmi_calculator import AnorexicBmiCalculator
from .views.weight_watcher_points_calculator import WeightWatcherPointsCalculator
from .views.overweight_calculator import OverweightCalculator

urlpatterns = [
    path('', HealthIndexView.as_view(), name='index'),
    path('bmi-calculator/', BmiCalculator.as_view(), name='bmi_calculator'),
    path('calorie-calculator/', CalorieCalculator.as_view(), name='calorie_calculator'),
    path('body-fat-calculator/', BodyFatCalculator.as_view(), name='body_fat_calculator'),
    path('bmr-calculator/', BmrCalculator.as_view(), name='bmr_calculator'),
    path('macro-calculator/', MacroCalculator.as_view(), name='macro_calculator'),
    path('ideal-weight-calculator/', IdealWeightCalculator.as_view(), name='ideal_weight_calculator'),
    path('pregnancy-calculator/', PregnancyCalculator.as_view(), name='pregnancy_calculator'),
    path('pregnancy-weight-gain-calculator/', PregnancyWeightGainCalculator.as_view(), name='pregnancy_weight_gain_calculator'),
    path('pregnancy-conception-calculator/', PregnancyConceptionCalculator.as_view(), name='pregnancy_conception_calculator'),
    path('due-date-calculator/', DueDateCalculator.as_view(), name='due_date_calculator'),
    path('pace-calculator/', PaceCalculator.as_view(), name='pace_calculator'),
    path('army-body-fat-calculator/', ArmyBodyFatCalculator.as_view(), name='army_body_fat_calculator'),
    path('carbohydrate-calculator/', CarbohydrateCalculator.as_view(), name='carbohydrate_calculator'),
    path('lean-body-mass-calculator/', LeanBodyMassCalculator.as_view(), name='lean_body_mass_calculator'),
    path('healthy-weight-calculator/', HealthyWeightCalculator.as_view(), name='healthy_weight_calculator'),
    path('calories-burned-calculator/', CaloriesBurnedCalculator.as_view(), name='calories_burned_calculator'),
    path('one-rep-max-calculator/', OneRepMaxCalculator.as_view(), name='one_rep_max_calculator'),
    path('target-heart-rate-calculator/', TargetHeartRateCalculator.as_view(), name='target_heart_rate_calculator'),
    path('protein-calculator/', ProteinCalculator.as_view(), name='protein_calculator'),
    path('fat-intake-calculator/', FatIntakeCalculator.as_view(), name='fat_intake_calculator'),
    path('tdee-calculator/', TdeeCalculator.as_view(), name='tdee_calculator'),
    path('ovulation-calculator/', OvulationCalculator.as_view(), name='ovulation_calculator'),
    path('conception-calculator/', ConceptionCalculator.as_view(), name='conception_calculator'),
    path('period-calculator/', PeriodCalculator.as_view(), name='period_calculator'),
    path('gfr-calculator/', GfrCalculator.as_view(), name='gfr_calculator'),
    path('body-type-calculator/', BodyTypeCalculator.as_view(), name='body_type_calculator'),
    path('body-surface-area-calculator/', BodySurfaceAreaCalculator.as_view(), name='body_surface_area_calculator'),
    path('bac-calculator/', BacCalculator.as_view(), name='bac_calculator'),
    path('anorexic-bmi-calculator/', AnorexicBmiCalculator.as_view(), name='anorexic_bmi_calculator'),
    path('weight-watcher-points-calculator/', WeightWatcherPointsCalculator.as_view(), name='weight_watcher_points_calculator'),
    path('overweight-calculator/', OverweightCalculator.as_view(), name='overweight_calculator'),
]

app_name = 'fitness_and_health_calculators'
