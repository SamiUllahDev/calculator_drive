#!/usr/bin/env python3
"""
Add Related Health & Fitness Calculators section to all templates.
Inserts a styled grid of related calculator links inside the content area.
"""
import os
import re

TEMPLATE_DIR = '/home/sami/Desktop/calculator_drive/Fitness_and_Health_Calculators/templates/fitness_and_health_calculators'

# Define related calculators for each template
RELATED_MAP = {
    'calorie_calculator': [
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'green'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'yellow'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('fat_intake_calculator', 'Fat Intake Calculator', 'Daily fat intake needs', 'orange'),
        ('carbohydrate_calculator', 'Carb Calculator', 'Daily carbohydrate needs', 'teal'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'emerald'),
    ],
    'bmr_calculator': [
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'blue'),
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'yellow'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'teal'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'emerald'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'green'),
    ],
    'body_fat_calculator': [
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'green'),
        ('body_type_calculator', 'Body Type Calculator', 'Determine your body type', 'purple'),
        ('army_body_fat_calculator', 'Army Body Fat', 'Military body fat standards', 'yellow'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'teal'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'emerald'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'orange'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'rose'),
        ('overweight_calculator', 'Overweight Calculator', 'Assess overweight status', 'indigo'),
    ],
    'macro_calculator': [
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('carbohydrate_calculator', 'Carb Calculator', 'Daily carbohydrate needs', 'teal'),
        ('fat_intake_calculator', 'Fat Intake Calculator', 'Daily fat intake needs', 'yellow'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'green'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'rose'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'emerald'),
    ],
    'tdee_calculator': [
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'green'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'yellow'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'blue'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'teal'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'emerald'),
        ('fat_intake_calculator', 'Fat Intake Calculator', 'Daily fat intake needs', 'purple'),
    ],
    'ideal_weight_calculator': [
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'green'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'purple'),
        ('overweight_calculator', 'Overweight Calculator', 'Assess overweight status', 'yellow'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'emerald'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'teal'),
        ('body_type_calculator', 'Body Type Calculator', 'Determine your body type', 'rose'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'indigo'),
    ],
    'healthy_weight_calculator': [
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'teal'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'purple'),
        ('overweight_calculator', 'Overweight Calculator', 'Assess overweight status', 'yellow'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'green'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'indigo'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'emerald'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
    ],
    'overweight_calculator': [
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'purple'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'green'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'indigo'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'teal'),
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'yellow'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'emerald'),
    ],
    'anorexic_bmi_calculator': [
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'green'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'teal'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'purple'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'emerald'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'yellow'),
    ],
    'army_body_fat_calculator': [
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'blue'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'teal'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'green'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'purple'),
        ('body_type_calculator', 'Body Type Calculator', 'Determine your body type', 'rose'),
        ('one_rep_max_calculator', 'One Rep Max', 'Calculate max lifting weight', 'yellow'),
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'orange'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('target_heart_rate_calculator', 'Target Heart Rate', 'Find your training zones', 'emerald'),
    ],
    'body_surface_area_calculator': [
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'purple'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'green'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'teal'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'emerald'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('body_type_calculator', 'Body Type Calculator', 'Determine your body type', 'rose'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'yellow'),
        ('gfr_calculator', 'GFR Calculator', 'Kidney function assessment', 'indigo'),
    ],
    'body_type_calculator': [
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'purple'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'green'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'teal'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'indigo'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'yellow'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'emerald'),
    ],
    'lean_body_mass_calculator': [
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'blue'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'teal'),
        ('body_type_calculator', 'Body Type Calculator', 'Determine your body type', 'purple'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'green'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'emerald'),
        ('one_rep_max_calculator', 'One Rep Max', 'Calculate max lifting weight', 'yellow'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('army_body_fat_calculator', 'Army Body Fat', 'Military body fat standards', 'orange'),
    ],
    'calories_burned_calculator': [
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'green'),
        ('pace_calculator', 'Pace Calculator', 'Running & walking pace', 'blue'),
        ('target_heart_rate_calculator', 'Target Heart Rate', 'Find your training zones', 'rose'),
        ('one_rep_max_calculator', 'One Rep Max', 'Calculate max lifting weight', 'yellow'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'teal'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'indigo'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'emerald'),
    ],
    'protein_calculator': [
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('carbohydrate_calculator', 'Carb Calculator', 'Daily carbohydrate needs', 'teal'),
        ('fat_intake_calculator', 'Fat Intake Calculator', 'Daily fat intake needs', 'yellow'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'green'),
        ('one_rep_max_calculator', 'One Rep Max', 'Calculate max lifting weight', 'indigo'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'blue'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'emerald'),
    ],
    'carbohydrate_calculator': [
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('fat_intake_calculator', 'Fat Intake Calculator', 'Daily fat intake needs', 'yellow'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'green'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'teal'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'emerald'),
    ],
    'fat_intake_calculator': [
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('carbohydrate_calculator', 'Carb Calculator', 'Daily carbohydrate needs', 'teal'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'green'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'yellow'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'emerald'),
    ],
    'one_rep_max_calculator': [
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'orange'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'green'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('target_heart_rate_calculator', 'Target Heart Rate', 'Find your training zones', 'blue'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'yellow'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'teal'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'emerald'),
    ],
    'target_heart_rate_calculator': [
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'orange'),
        ('pace_calculator', 'Pace Calculator', 'Running & walking pace', 'blue'),
        ('one_rep_max_calculator', 'One Rep Max', 'Calculate max lifting weight', 'yellow'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'green'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'rose'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'teal'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'indigo'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'emerald'),
    ],
    'pace_calculator': [
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'orange'),
        ('target_heart_rate_calculator', 'Target Heart Rate', 'Find your training zones', 'rose'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'yellow'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'green'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('one_rep_max_calculator', 'One Rep Max', 'Calculate max lifting weight', 'teal'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'indigo'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'emerald'),
    ],
    'pregnancy_calculator': [
        ('due_date_calculator', 'Due Date Calculator', 'Calculate your due date', 'blue'),
        ('pregnancy_weight_gain_calculator', 'Pregnancy Weight Gain', 'Track healthy weight gain', 'green'),
        ('pregnancy_conception_calculator', 'Conception Calculator', 'Estimate conception date', 'purple'),
        ('ovulation_calculator', 'Ovulation Calculator', 'Track your fertile window', 'rose'),
        ('period_calculator', 'Period Calculator', 'Track your menstrual cycle', 'teal'),
        ('conception_calculator', 'Conception Date', 'When did conception occur', 'orange'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'yellow'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'indigo'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'emerald'),
    ],
    'due_date_calculator': [
        ('pregnancy_calculator', 'Pregnancy Calculator', 'Week-by-week pregnancy tracker', 'blue'),
        ('pregnancy_weight_gain_calculator', 'Pregnancy Weight Gain', 'Track healthy weight gain', 'green'),
        ('pregnancy_conception_calculator', 'Conception Calculator', 'Estimate conception date', 'purple'),
        ('conception_calculator', 'Conception Date', 'When did conception occur', 'orange'),
        ('ovulation_calculator', 'Ovulation Calculator', 'Track your fertile window', 'rose'),
        ('period_calculator', 'Period Calculator', 'Track your menstrual cycle', 'teal'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'yellow'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'indigo'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'emerald'),
    ],
    'conception_calculator': [
        ('pregnancy_calculator', 'Pregnancy Calculator', 'Week-by-week pregnancy tracker', 'blue'),
        ('due_date_calculator', 'Due Date Calculator', 'Calculate your due date', 'green'),
        ('pregnancy_conception_calculator', 'Conception Calculator', 'Estimate conception date', 'purple'),
        ('ovulation_calculator', 'Ovulation Calculator', 'Track your fertile window', 'rose'),
        ('period_calculator', 'Period Calculator', 'Track your menstrual cycle', 'teal'),
        ('pregnancy_weight_gain_calculator', 'Pregnancy Weight Gain', 'Track healthy weight gain', 'orange'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'yellow'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'indigo'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'emerald'),
    ],
    'pregnancy_conception_calculator': [
        ('pregnancy_calculator', 'Pregnancy Calculator', 'Week-by-week pregnancy tracker', 'blue'),
        ('due_date_calculator', 'Due Date Calculator', 'Calculate your due date', 'green'),
        ('conception_calculator', 'Conception Date', 'When did conception occur', 'orange'),
        ('ovulation_calculator', 'Ovulation Calculator', 'Track your fertile window', 'rose'),
        ('period_calculator', 'Period Calculator', 'Track your menstrual cycle', 'teal'),
        ('pregnancy_weight_gain_calculator', 'Pregnancy Weight Gain', 'Track healthy weight gain', 'purple'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'yellow'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'indigo'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'emerald'),
    ],
    'pregnancy_weight_gain_calculator': [
        ('pregnancy_calculator', 'Pregnancy Calculator', 'Week-by-week pregnancy tracker', 'blue'),
        ('due_date_calculator', 'Due Date Calculator', 'Calculate your due date', 'green'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'teal'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'emerald'),
        ('pregnancy_conception_calculator', 'Conception Calculator', 'Estimate conception date', 'purple'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'yellow'),
    ],
    'ovulation_calculator': [
        ('period_calculator', 'Period Calculator', 'Track your menstrual cycle', 'rose'),
        ('conception_calculator', 'Conception Date', 'When did conception occur', 'orange'),
        ('pregnancy_calculator', 'Pregnancy Calculator', 'Week-by-week pregnancy tracker', 'blue'),
        ('due_date_calculator', 'Due Date Calculator', 'Calculate your due date', 'green'),
        ('pregnancy_conception_calculator', 'Conception Calculator', 'Estimate conception date', 'purple'),
        ('pregnancy_weight_gain_calculator', 'Pregnancy Weight Gain', 'Track healthy weight gain', 'teal'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'yellow'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'indigo'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'emerald'),
    ],
    'period_calculator': [
        ('ovulation_calculator', 'Ovulation Calculator', 'Track your fertile window', 'rose'),
        ('conception_calculator', 'Conception Date', 'When did conception occur', 'orange'),
        ('pregnancy_calculator', 'Pregnancy Calculator', 'Week-by-week pregnancy tracker', 'blue'),
        ('due_date_calculator', 'Due Date Calculator', 'Calculate your due date', 'green'),
        ('pregnancy_conception_calculator', 'Conception Calculator', 'Estimate conception date', 'purple'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'yellow'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'teal'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'emerald'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'indigo'),
    ],
    'gfr_calculator': [
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('body_surface_area_calculator', 'Body Surface Area', 'Calculate your BSA', 'green'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'teal'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'purple'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'rose'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'emerald'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'yellow'),
    ],
    'bac_calculator': [
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('body_fat_calculator', 'Body Fat Calculator', 'Measure body fat percentage', 'purple'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'green'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'teal'),
        ('bmr_calculator', 'BMR Calculator', 'Find your basal metabolic rate', 'emerald'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'indigo'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('lean_body_mass_calculator', 'Lean Body Mass', 'Calculate lean body mass', 'yellow'),
    ],
    'weight_watcher_points_calculator': [
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('fat_intake_calculator', 'Fat Intake Calculator', 'Daily fat intake needs', 'yellow'),
        ('carbohydrate_calculator', 'Carb Calculator', 'Daily carbohydrate needs', 'teal'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('ideal_weight_calculator', 'Ideal Weight', 'Find your ideal body weight', 'green'),
        ('healthy_weight_calculator', 'Healthy Weight', 'Check healthy weight range', 'emerald'),
    ],
    'chipotle_nutrition_calculator': [
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('carbohydrate_calculator', 'Carb Calculator', 'Daily carbohydrate needs', 'teal'),
        ('fat_intake_calculator', 'Fat Intake Calculator', 'Daily fat intake needs', 'yellow'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'green'),
        ('starbucks_calorie_calculator', 'Starbucks Calories', 'Starbucks drink nutrition', 'emerald'),
    ],
    'starbucks_calorie_calculator': [
        ('calorie_calculator', 'Calorie Calculator', 'Daily caloric needs estimate', 'orange'),
        ('macro_calculator', 'Macro Calculator', 'Protein, carbs & fat ratios', 'rose'),
        ('carbohydrate_calculator', 'Carb Calculator', 'Daily carbohydrate needs', 'teal'),
        ('fat_intake_calculator', 'Fat Intake Calculator', 'Daily fat intake needs', 'yellow'),
        ('protein_calculator', 'Protein Calculator', 'Daily protein requirements', 'indigo'),
        ('tdee_calculator', 'TDEE Calculator', 'Total daily energy expenditure', 'purple'),
        ('bmi_calculator', 'BMI Calculator', 'Calculate your body mass index', 'blue'),
        ('calories_burned_calculator', 'Calories Burned', 'Track exercise calorie burn', 'green'),
        ('chipotle_nutrition_calculator', 'Chipotle Nutrition', 'Chipotle meal nutrition', 'emerald'),
    ],
}

# Color mappings
COLOR_MAP = {
    'blue': ('from-blue-50 to-indigo-50', 'border-blue-200', 'hover:border-blue-400', 'bg-blue-100', 'group-hover:bg-blue-200', 'group-hover:text-blue-700', 'text-blue-600'),
    'green': ('from-green-50 to-emerald-50', 'border-green-200', 'hover:border-green-400', 'bg-green-100', 'group-hover:bg-green-200', 'group-hover:text-green-700', 'text-green-600'),
    'purple': ('from-purple-50 to-violet-50', 'border-purple-200', 'hover:border-purple-400', 'bg-purple-100', 'group-hover:bg-purple-200', 'group-hover:text-purple-700', 'text-purple-600'),
    'orange': ('from-orange-50 to-amber-50', 'border-orange-200', 'hover:border-orange-400', 'bg-orange-100', 'group-hover:bg-orange-200', 'group-hover:text-orange-700', 'text-orange-600'),
    'rose': ('from-rose-50 to-pink-50', 'border-rose-200', 'hover:border-rose-400', 'bg-rose-100', 'group-hover:bg-rose-200', 'group-hover:text-rose-700', 'text-rose-600'),
    'yellow': ('from-yellow-50 to-amber-50', 'border-yellow-200', 'hover:border-yellow-400', 'bg-yellow-100', 'group-hover:bg-yellow-200', 'group-hover:text-yellow-700', 'text-yellow-600'),
    'teal': ('from-teal-50 to-cyan-50', 'border-teal-200', 'hover:border-teal-400', 'bg-teal-100', 'group-hover:bg-teal-200', 'group-hover:text-teal-700', 'text-teal-600'),
    'indigo': ('from-indigo-50 to-blue-50', 'border-indigo-200', 'hover:border-indigo-400', 'bg-indigo-100', 'group-hover:bg-indigo-200', 'group-hover:text-indigo-700', 'text-indigo-600'),
    'emerald': ('from-emerald-50 to-green-50', 'border-emerald-200', 'hover:border-emerald-400', 'bg-emerald-100', 'group-hover:bg-emerald-200', 'group-hover:text-emerald-700', 'text-emerald-600'),
}

ICONS = {
    'blue': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    'green': 'M13 10V3L4 14h7v7l9-11h-7z',
    'purple': 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z',
    'orange': 'M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z',
    'rose': 'M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z',
    'yellow': 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
    'teal': 'M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3',
    'indigo': 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z',
    'emerald': 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
}


def generate_card(url_name, display_name, description, color):
    grad, border, hover_border, bg, hover_bg, hover_text, icon_color = COLOR_MAP[color]
    icon_path = ICONS[color]
    return f'''                                <a href="{{% url 'fitness_and_health_calculators:{url_name}' %}}" class="flex items-center p-3 bg-gradient-to-r {grad} rounded-lg border {border} hover:shadow-md {hover_border} transition-all duration-200 group">
                                    <div class="w-10 h-10 {bg} rounded-lg flex items-center justify-center mr-3 {hover_bg} transition-colors">
                                        <svg class="w-5 h-5 {icon_color}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{icon_path}"></path></svg>
                                    </div>
                                    <div>
                                        <p class="text-sm font-semibold text-gray-900 {hover_text}">{{% trans "{display_name}" %}}</p>
                                        <p class="text-xs text-gray-500">{{% trans "{description}" %}}</p>
                                    </div>
                                </a>'''


def generate_section(calculators):
    cards = '\n'.join(generate_card(*calc) for calc in calculators)
    return f'''
                        <!-- Related Health & Fitness Calculators Section -->
                        <div>
                            <h3 class="text-xl font-semibold text-gray-900 mb-4">{{% trans "Related Health & Fitness Calculators" %}}</h3>
                            <p class="text-gray-700 text-sm leading-relaxed mb-4">
                                {{% blocktrans trimmed %}}Explore more health and fitness calculators to get a complete picture of your wellness:{{% endblocktrans %}}
                            </p>
                            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
{cards}
                            </div>
                        </div>
'''


def process_template(filepath, template_name):
    """Insert Related Calculators section before </div></div> that precedes <script>."""
    with open(filepath, 'r') as f:
        content = f.read()

    if 'Related Health & Fitness Calculators' in content:
        print(f"  SKIP (already has related section): {template_name}")
        return False

    calc_key = template_name.replace('.html', '')
    if calc_key not in RELATED_MAP:
        print(f"  SKIP (no mapping): {template_name}")
        return False

    section_html = generate_section(RELATED_MAP[calc_key])

    # Find the main <script> tag (the JS block after content, not CDN/JSON-LD scripts)
    # The main script tag is always a bare <script> at column 0, after closing </div> tags
    
    lines = content.split('\n')
    
    # Find the LAST bare <script> tag (not <script type="..." or <script src="...")
    script_line_idx = None
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped == '<script>' or stripped == '<script >':
            script_line_idx = i
            break
    
    if script_line_idx is None:
        print(f"  SKIP (no <script> tag found): {template_name}")
        return False

    # Count back from <script> through empty lines and </div> lines
    # to find the right insertion point
    # We need to find the line that has "</div>" at a deep indentation
    # (the one that closes "space-y-6" div)
    
    # Walk backwards from script_line to find consecutive </div> lines
    i = script_line_idx - 1
    while i >= 0 and lines[i].strip() == '':
        i -= 1
    
    # Now i should be on the last </div> (outermost wrapper)
    # Count the </div> chain
    div_chain_end = i
    div_count = 0
    while i >= 0 and lines[i].strip() == '</div>':
        div_count += 1
        i -= 1
    
    # The closing divs typically are 5-6 levels:
    # </div> closes: page wrapper, container, grid, column, content card, space-y-6
    # We want to insert BEFORE the </div> that closes space-y-6
    # That's the FIRST </div> in the chain (deepest indentation, found last when going backwards)
    # Which is at position: div_chain_end - div_count + 1
    
    # Actually, let's find by indentation. The space-y-6 closer has the most indent
    # in the chain. Let's find the </div> with the most leading whitespace.
    chain_start = i + 1  # first </div> line (deepest nesting)
    
    # Insert BEFORE the first </div> in the chain (most indented one)
    insert_idx = chain_start
    
    # Build new content
    new_lines = lines[:insert_idx] + [section_html] + lines[insert_idx:]
    new_content = '\n'.join(new_lines)
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print(f"  DONE: {template_name} (inserted before line {insert_idx + 1}, {div_count} closing divs)")
    return True


def main():
    templates = [f for f in os.listdir(TEMPLATE_DIR) 
                 if f.endswith('.html') and f not in ('index.html', 'bmi_calculator.html')]
    templates.sort()
    
    updated = 0
    skipped = 0
    
    for template in templates:
        filepath = os.path.join(TEMPLATE_DIR, template)
        if process_template(filepath, template):
            updated += 1
        else:
            skipped += 1
    
    print(f"\nDone! Updated: {updated}, Skipped: {skipped}")


if __name__ == '__main__':
    main()
