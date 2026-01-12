from django.urls import path
from .views.index import MathIndexView
from .views.scientific_calculator import ScientificCalculator
from .views.fraction_calculator import FractionCalculator
from .views.percentage_calculator import PercentageCalculator
from .views.triangle_calculator import TriangleCalculator
from .views.volume_calculator import VolumeCalculator
from .views.standard_deviation_calculator import StandardDeviationCalculator
from .views.random_number_generator import RandomNumberGenerator
from .views.number_sequence_calculator import NumberSequenceCalculator
from .views.percent_error_calculator import PercentErrorCalculator
from .views.exponent_calculator import ExponentCalculator
from .views.binary_calculator import BinaryCalculator
from .views.hex_calculator import HexCalculator
from .views.half_life_calculator import HalfLifeCalculator
from .views.quadratic_formula_calculator import QuadraticFormulaCalculator
from .views.slope_calculator import SlopeCalculator
from .views.log_calculator import LogCalculator
from .views.area_calculator import AreaCalculator
from .views.sample_size_calculator import SampleSizeCalculator
from .views.probability_calculator import ProbabilityCalculator
from .views.statistics_calculator import StatisticsCalculator
from .views.mean_median_mode_range_calculator import MeanMedianModeRangeCalculator
from .views.permutation_and_combination_calculator import PermutationAndCombinationCalculator
from .views.z_score_calculator import ZScoreCalculator
from .views.confidence_interval_calculator import ConfidenceIntervalCalculator
from .views.ratio_calculator import RatioCalculator
from .views.distance_calculator import DistanceCalculator
from .views.circle_calculator import CircleCalculator
from .views.surface_area_calculator import SurfaceAreaCalculator
from .views.pythagorean_theorem_calculator import PythagoreanTheoremCalculator
from .views.right_triangle_calculator import RightTriangleCalculator
from .views.root_calculator import RootCalculator
from .views.least_common_multiple_calculator import LeastCommonMultipleCalculator
from .views.greatest_common_factor_calculator import GreatestCommonFactorCalculator
from .views.factor_calculator import FactorCalculator
from .views.rounding_calculator import RoundingCalculator
from .views.matrix_calculator import MatrixCalculator
from .views.scientific_notation_calculator import ScientificNotationCalculator
from .views.big_number_calculator import BigNumberCalculator
from .views.prime_factorization_calculator import PrimeFactorizationCalculator
from .views.common_factor_calculator import CommonFactorCalculator
from .views.basic_calculator import BasicCalculator
from .views.long_division_calculator import LongDivisionCalculator
from .views.average_calculator import AverageCalculator
from .views.p_value_calculator import PValueCalculator

urlpatterns = [
    path('', MathIndexView.as_view(), name='index'),
    path('scientific-calculator/', ScientificCalculator.as_view(), name='scientific_calculator'),
    path('fraction-calculator/', FractionCalculator.as_view(), name='fraction_calculator'),
    path('percentage-calculator/', PercentageCalculator.as_view(), name='percentage_calculator'),
    path('triangle-calculator/', TriangleCalculator.as_view(), name='triangle_calculator'),
    path('volume-calculator/', VolumeCalculator.as_view(), name='volume_calculator'),
    path('standard-deviation-calculator/', StandardDeviationCalculator.as_view(), name='standard_deviation_calculator'),
    path('random-number-generator/', RandomNumberGenerator.as_view(), name='random_number_generator'),
    path('number-sequence-calculator/', NumberSequenceCalculator.as_view(), name='number_sequence_calculator'),
    path('percent-error-calculator/', PercentErrorCalculator.as_view(), name='percent_error_calculator'),
    path('exponent-calculator/', ExponentCalculator.as_view(), name='exponent_calculator'),
    path('binary-calculator/', BinaryCalculator.as_view(), name='binary_calculator'),
    path('hex-calculator/', HexCalculator.as_view(), name='hex_calculator'),
    path('half-life-calculator/', HalfLifeCalculator.as_view(), name='half_life_calculator'),
    path('quadratic-formula-calculator/', QuadraticFormulaCalculator.as_view(), name='quadratic_formula_calculator'),
    path('slope-calculator/', SlopeCalculator.as_view(), name='slope_calculator'),
    path('log-calculator/', LogCalculator.as_view(), name='log_calculator'),
    path('area-calculator/', AreaCalculator.as_view(), name='area_calculator'),
    path('sample-size-calculator/', SampleSizeCalculator.as_view(), name='sample_size_calculator'),
    path('probability-calculator/', ProbabilityCalculator.as_view(), name='probability_calculator'),
    path('statistics-calculator/', StatisticsCalculator.as_view(), name='statistics_calculator'),
    path('mean-median-mode-range-calculator/', MeanMedianModeRangeCalculator.as_view(), name='mean_median_mode_range_calculator'),
    path('permutation-and-combination-calculator/', PermutationAndCombinationCalculator.as_view(), name='permutation_and_combination_calculator'),
    path('z-score-calculator/', ZScoreCalculator.as_view(), name='z_score_calculator'),
    path('confidence-interval-calculator/', ConfidenceIntervalCalculator.as_view(), name='confidence_interval_calculator'),
    path('ratio-calculator/', RatioCalculator.as_view(), name='ratio_calculator'),
    path('distance-calculator/', DistanceCalculator.as_view(), name='distance_calculator'),
    path('circle-calculator/', CircleCalculator.as_view(), name='circle_calculator'),
    path('surface-area-calculator/', SurfaceAreaCalculator.as_view(), name='surface_area_calculator'),
    path('pythagorean-theorem-calculator/', PythagoreanTheoremCalculator.as_view(), name='pythagorean_theorem_calculator'),
    path('right-triangle-calculator/', RightTriangleCalculator.as_view(), name='right_triangle_calculator'),
    path('root-calculator/', RootCalculator.as_view(), name='root_calculator'),
    path('least-common-multiple-calculator/', LeastCommonMultipleCalculator.as_view(), name='least_common_multiple_calculator'),
    path('greatest-common-factor-calculator/', GreatestCommonFactorCalculator.as_view(), name='greatest_common_factor_calculator'),
    path('factor-calculator/', FactorCalculator.as_view(), name='factor_calculator'),
    path('rounding-calculator/', RoundingCalculator.as_view(), name='rounding_calculator'),
    path('matrix-calculator/', MatrixCalculator.as_view(), name='matrix_calculator'),
    path('scientific-notation-calculator/', ScientificNotationCalculator.as_view(), name='scientific_notation_calculator'),
    path('big-number-calculator/', BigNumberCalculator.as_view(), name='big_number_calculator'),
    path('prime-factorization-calculator/', PrimeFactorizationCalculator.as_view(), name='prime_factorization_calculator'),
    path('common-factor-calculator/', CommonFactorCalculator.as_view(), name='common_factor_calculator'),
    path('basic-calculator/', BasicCalculator.as_view(), name='basic_calculator'),
    path('long-division-calculator/', LongDivisionCalculator.as_view(), name='long_division_calculator'),
    path('average-calculator/', AverageCalculator.as_view(), name='average_calculator'),
    path('p-value-calculator/', PValueCalculator.as_view(), name='p_value_calculator'),
]

app_name = 'math_calculators'
