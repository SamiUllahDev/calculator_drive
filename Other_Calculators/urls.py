from django.urls import path
from .views.index import OtherIndexView
from .views.age_calculator import AgeCalculator
from .views.date_calculator import DateCalculator
from .views.time_calculator import TimeCalculator
from .views.hours_calculator import HoursCalculator
from .views.gpa_calculator import GpaCalculator
from .views.grade_calculator import GradeCalculator
from .views.height_calculator import HeightCalculator
from .views.concrete_calculator import ConcreteCalculator
from .views.ip_subnet_calculator import IpSubnetCalculator
from .views.bra_size_calculator import BraSizeCalculator
from .views.password_generator import PasswordGenerator
from .views.dice_roller import DiceRoller
from .views.conversion_calculator import ConversionCalculator
from .views.fuel_cost_calculator import FuelCostCalculator
from .views.voltage_drop_calculator import VoltageDropCalculator
from .views.btu_calculator import BtuCalculator
from .views.square_footage_calculator import SquareFootageCalculator
from .views.time_card_calculator import TimeCardCalculator
from .views.time_zone_calculator import TimeZoneCalculator
from .views.love_calculator import LoveCalculator
from .views.gdp_calculator import GdpCalculator
from .views.gas_mileage_calculator import GasMileageCalculator
from .views.horsepower_calculator import HorsepowerCalculator
from .views.engine_horsepower_calculator import EngineHorsepowerCalculator
from .views.stair_calculator import StairCalculator
from .views.resistor_calculator import ResistorCalculator
from .views.ohms_law_calculator import OhmsLawCalculator
from .views.electricity_calculator import ElectricityCalculator
from .views.shoe_size_conversion import ShoeSizeConversion
from .views.tip_calculator import TipCalculator
from .views.mileage_calculator import MileageCalculator
from .views.density_calculator import DensityCalculator
from .views.mass_calculator import MassCalculator
from .views.weight_calculator import WeightCalculator
from .views.speed_calculator import SpeedCalculator
from .views.molarity_calculator import MolarityCalculator
from .views.molecular_weight_calculator import MolecularWeightCalculator
from .views.roman_numeral_converter import RomanNumeralConverter
from .views.golf_handicap_calculator import GolfHandicapCalculator
from .views.sleep_calculator import SleepCalculator
from .views.tire_size_calculator import TireSizeCalculator
from .views.roofing_calculator import RoofingCalculator
from .views.tile_calculator import TileCalculator
from .views.mulch_calculator import MulchCalculator
from .views.gravel_calculator import GravelCalculator
from .views.wind_chill_calculator import WindChillCalculator
from .views.heat_index_calculator import HeatIndexCalculator
from .views.dew_point_calculator import DewPointCalculator
from .views.bandwidth_calculator import BandwidthCalculator
from .views.time_duration_calculator import TimeDurationCalculator
from .views.day_counter import DayCounter
from .views.day_of_the_week_calculator import DayOfTheWeekCalculator
from .views.day_of_week_calculator import DayOfWeekCalculator
from .views.snow_day_calculator import SnowDayCalculator
from .views.female_delusion_calculator import FemaleDelusionCalculator
from .views.schedule_one_calculator import ScheduleOneCalculator
from .views.gag_calculator import GagCalculator
from .views.silca_tire_pressure_calculator import SilcaTirePressureCalculator
from .views.circle_skirt_calculator import CircleSkirtCalculator

urlpatterns = [
    path('', OtherIndexView.as_view(), name='index'),
    path('age-calculator/', AgeCalculator.as_view(), name='age_calculator'),
    path('date-calculator/', DateCalculator.as_view(), name='date_calculator'),
    path('time-calculator/', TimeCalculator.as_view(), name='time_calculator'),
    path('hours-calculator/', HoursCalculator.as_view(), name='hours_calculator'),
    path('gpa-calculator/', GpaCalculator.as_view(), name='gpa_calculator'),
    path('grade-calculator/', GradeCalculator.as_view(), name='grade_calculator'),
    path('height-calculator/', HeightCalculator.as_view(), name='height_calculator'),
    path('concrete-calculator/', ConcreteCalculator.as_view(), name='concrete_calculator'),
    path('ip-subnet-calculator/', IpSubnetCalculator.as_view(), name='ip_subnet_calculator'),
    path('bra-size-calculator/', BraSizeCalculator.as_view(), name='bra_size_calculator'),
    path('password-generator/', PasswordGenerator.as_view(), name='password_generator'),
    path('dice-roller/', DiceRoller.as_view(), name='dice_roller'),
    path('conversion-calculator/', ConversionCalculator.as_view(), name='conversion_calculator'),
    path('fuel-cost-calculator/', FuelCostCalculator.as_view(), name='fuel_cost_calculator'),
    path('voltage-drop-calculator/', VoltageDropCalculator.as_view(), name='voltage_drop_calculator'),
    path('btu-calculator/', BtuCalculator.as_view(), name='btu_calculator'),
    path('square-footage-calculator/', SquareFootageCalculator.as_view(), name='square_footage_calculator'),
    path('time-card-calculator/', TimeCardCalculator.as_view(), name='time_card_calculator'),
    path('time-zone-calculator/', TimeZoneCalculator.as_view(), name='time_zone_calculator'),
    path('love-calculator/', LoveCalculator.as_view(), name='love_calculator'),
    path('gdp-calculator/', GdpCalculator.as_view(), name='gdp_calculator'),
    path('gas-mileage-calculator/', GasMileageCalculator.as_view(), name='gas_mileage_calculator'),
    path('horsepower-calculator/', HorsepowerCalculator.as_view(), name='horsepower_calculator'),
    path('engine-horsepower-calculator/', EngineHorsepowerCalculator.as_view(), name='engine_horsepower_calculator'),
    path('stair-calculator/', StairCalculator.as_view(), name='stair_calculator'),
    path('resistor-calculator/', ResistorCalculator.as_view(), name='resistor_calculator'),
    path('ohms-law-calculator/', OhmsLawCalculator.as_view(), name='ohms_law_calculator'),
    path('electricity-calculator/', ElectricityCalculator.as_view(), name='electricity_calculator'),
    path('shoe-size-conversion/', ShoeSizeConversion.as_view(), name='shoe_size_conversion'),
    path('tip-calculator/', TipCalculator.as_view(), name='tip_calculator'),
    path('mileage-calculator/', MileageCalculator.as_view(), name='mileage_calculator'),
    path('density-calculator/', DensityCalculator.as_view(), name='density_calculator'),
    path('mass-calculator/', MassCalculator.as_view(), name='mass_calculator'),
    path('weight-calculator/', WeightCalculator.as_view(), name='weight_calculator'),
    path('speed-calculator/', SpeedCalculator.as_view(), name='speed_calculator'),
    path('molarity-calculator/', MolarityCalculator.as_view(), name='molarity_calculator'),
    path('molecular-weight-calculator/', MolecularWeightCalculator.as_view(), name='molecular_weight_calculator'),
    path('roman-numeral-converter/', RomanNumeralConverter.as_view(), name='roman_numeral_converter'),
    path('golf-handicap-calculator/', GolfHandicapCalculator.as_view(), name='golf_handicap_calculator'),
    path('sleep-calculator/', SleepCalculator.as_view(), name='sleep_calculator'),
    path('tire-size-calculator/', TireSizeCalculator.as_view(), name='tire_size_calculator'),
    path('roofing-calculator/', RoofingCalculator.as_view(), name='roofing_calculator'),
    path('tile-calculator/', TileCalculator.as_view(), name='tile_calculator'),
    path('mulch-calculator/', MulchCalculator.as_view(), name='mulch_calculator'),
    path('gravel-calculator/', GravelCalculator.as_view(), name='gravel_calculator'),
    path('wind-chill-calculator/', WindChillCalculator.as_view(), name='wind_chill_calculator'),
    path('heat-index-calculator/', HeatIndexCalculator.as_view(), name='heat_index_calculator'),
    path('dew-point-calculator/', DewPointCalculator.as_view(), name='dew_point_calculator'),
    path('bandwidth-calculator/', BandwidthCalculator.as_view(), name='bandwidth_calculator'),
    path('time-duration-calculator/', TimeDurationCalculator.as_view(), name='time_duration_calculator'),
    path('day-counter/', DayCounter.as_view(), name='day_counter'),
    path('day-of-the-week-calculator/', DayOfTheWeekCalculator.as_view(), name='day_of_the_week_calculator'),
    path('day-of-week-calculator/', DayOfWeekCalculator.as_view(), name='day_of_week_calculator'),
    path('snow-day-calculator/', SnowDayCalculator.as_view(), name='snow_day_calculator'),
    path('female-delusion-calculator/', FemaleDelusionCalculator.as_view(), name='female_delusion_calculator'),
    path('schedule-1-calculator/', ScheduleOneCalculator.as_view(), name='schedule_one_calculator'),
    path('gag-calculator/', GagCalculator.as_view(), name='gag_calculator'),
    path('silca-tire-pressure-calculator/', SilcaTirePressureCalculator.as_view(), name='silca_tire_pressure_calculator'),
    path('circle-skirt-calculator/', CircleSkirtCalculator.as_view(), name='circle_skirt_calculator'),
]

app_name = 'other_calculators'
