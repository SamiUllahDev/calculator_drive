from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from blog.models import Post, Category, Tag
from django.utils.text import slugify
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Deletes all old blog posts and creates 6 new calculator-related blog posts'
    
    def handle(self, *args, **options):
        # Delete all existing posts
        deleted_count = Post.objects.all().delete()[0]
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} old blog post(s)'))
        
        # Get or create categories
        categories_data = [
            {'name': 'Calculator Guides', 'slug': 'calculator-guides', 'description': 'Comprehensive guides on using various calculators'},
            {'name': 'Math Tips', 'slug': 'math-tips', 'description': 'Tips and tricks for mathematical calculations'},
            {'name': 'Financial Planning', 'slug': 'financial-planning', 'description': 'Financial calculator guides and tips'},
            {'name': 'Health & Fitness', 'slug': 'health-fitness', 'description': 'Health and fitness calculator guides'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description']
                }
            )
            categories[cat_data['slug']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
        
        # Get or create tags
        tags_data = ['calculators', 'math', 'finance', 'health', 'tips', 'guides', 'tutorials']
        tags_dict = {}
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(
                slug=slugify(tag_name),
                defaults={'name': tag_name}
            )
            tags_dict[tag_name] = tag
        
        # Get admin user
        user = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first()
        if not user:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
                return
        
        # New blog posts with calculator-related content
        posts_data = [
            {
                'title': 'How to Use Scientific Calculators: A Complete Beginner\'s Guide',
                'excerpt': 'Master scientific calculators with our comprehensive guide. Learn essential functions, operations, and tips for students and professionals.',
                'content': '''
<h2>Introduction to Scientific Calculators</h2>
<p>Scientific calculators are powerful tools that go far beyond basic arithmetic. Whether you're a student tackling algebra, trigonometry, or calculus, or a professional working with complex mathematical operations, understanding how to use a scientific calculator effectively can save time and improve accuracy.</p>

<h2>Essential Functions</h2>
<h3>Basic Operations</h3>
<p>Scientific calculators handle all standard arithmetic operations:</p>
<ul>
<li><strong>Addition (+):</strong> Simple addition of numbers</li>
<li><strong>Subtraction (-):</strong> Subtracting one number from another</li>
<li><strong>Multiplication (×):</strong> Multiplying numbers</li>
<li><strong>Division (÷):</strong> Dividing numbers</li>
<li><strong>Exponentiation (^ or x^y):</strong> Raising numbers to powers</li>
</ul>

<h3>Trigonometric Functions</h3>
<p>Most scientific calculators include trigonometric functions essential for geometry and physics:</p>
<ul>
<li><strong>sin, cos, tan:</strong> Basic trigonometric functions</li>
<li><strong>sin⁻¹, cos⁻¹, tan⁻¹:</strong> Inverse trigonometric functions</li>
<li><strong>Degrees vs Radians:</strong> Always check which mode your calculator is in</li>
</ul>

<h3>Logarithmic Functions</h3>
<p>Logarithmic functions are crucial for solving exponential equations:</p>
<ul>
<li><strong>log:</strong> Base 10 logarithm</li>
<li><strong>ln:</strong> Natural logarithm (base e)</li>
<li><strong>e^x:</strong> Exponential function</li>
</ul>

<h2>Advanced Features</h2>
<h3>Memory Functions</h3>
<p>Learn to use memory storage (M+, M-, MR, MC) to store intermediate results and perform complex calculations efficiently.</p>

<h3>Parentheses and Order of Operations</h3>
<p>Understanding how to use parentheses correctly ensures your calculations follow the proper order of operations (PEMDAS).</p>

<h2>Tips for Success</h2>
<ul>
<li>Always double-check your input before pressing equals</li>
<li>Use parentheses liberally to ensure correct order of operations</li>
<li>Familiarize yourself with your specific calculator model</li>
<li>Practice with sample problems to build confidence</li>
</ul>

<h2>Common Mistakes to Avoid</h2>
<ul>
<li>Forgetting to switch between degrees and radians</li>
<li>Not using parentheses when needed</li>
<li>Entering numbers incorrectly</li>
<li>Forgetting to clear memory between calculations</li>
</ul>

<p>With practice and understanding of these fundamental concepts, you'll be able to tackle complex mathematical problems with confidence using your scientific calculator.</p>
                ''',
                'category': 'calculator-guides',
                'tags': ['calculators', 'math', 'guides', 'tutorials'],
                'meta_title': 'Scientific Calculator Guide - Complete Beginner Tutorial',
                'meta_description': 'Learn how to use scientific calculators effectively. Complete guide covering essential functions, operations, and tips for students and professionals.',
                'meta_keywords': 'scientific calculator, calculator guide, math calculator, how to use calculator'
            },
            {
                'title': 'Financial Calculator Tips: Mastering Loan and Mortgage Calculations',
                'excerpt': 'Learn how to use financial calculators for loans, mortgages, and investments. Master key formulas and calculator functions for better financial planning.',
                'content': '''
<h2>Understanding Financial Calculators</h2>
<p>Financial calculators are specialized tools designed to solve complex financial problems quickly and accurately. Whether you're calculating loan payments, mortgage rates, or investment returns, these calculators can save significant time and reduce errors.</p>

<h2>Loan Calculations</h2>
<h3>Basic Loan Payment Formula</h3>
<p>The standard loan payment formula helps you understand how much you'll pay monthly:</p>
<p><strong>M = P × [r(1+r)^n] / [(1+r)^n - 1]</strong></p>
<ul>
<li>M = Monthly payment</li>
<li>P = Principal loan amount</li>
<li>r = Monthly interest rate</li>
<li>n = Number of payments</li>
</ul>

<h3>Using Financial Calculators</h3>
<p>Most financial calculators use these key variables:</p>
<ul>
<li><strong>PV (Present Value):</strong> The loan amount</li>
<li><strong>FV (Future Value):</strong> Usually 0 for loans</li>
<li><strong>PMT (Payment):</strong> Monthly payment amount</li>
<li><strong>N (Number of periods):</strong> Total number of payments</li>
<li><strong>I/Y (Interest rate):</strong> Annual interest rate</li>
</ul>

<h2>Mortgage Calculations</h2>
<p>Mortgage calculations follow similar principles but often include additional factors:</p>
<ul>
<li>Property taxes</li>
<li>Homeowner's insurance</li>
<li>Private Mortgage Insurance (PMI)</li>
<li>HOA fees</li>
</ul>

<h2>Investment Calculations</h2>
<h3>Compound Interest</h3>
<p>Understanding compound interest is crucial for investment planning:</p>
<p><strong>A = P(1 + r/n)^(nt)</strong></p>
<ul>
<li>A = Final amount</li>
<li>P = Principal investment</li>
<li>r = Annual interest rate</li>
<li>n = Compounding frequency</li>
<li>t = Time in years</li>
</ul>

<h2>Practical Tips</h2>
<ul>
<li>Always verify calculator results manually for important financial decisions</li>
<li>Understand the difference between APR and interest rate</li>
<li>Consider all costs, not just the principal and interest</li>
<li>Use online calculators to double-check your work</li>
</ul>

<h2>Common Financial Calculator Functions</h2>
<ul>
<li><strong>Amortization schedules:</strong> See how payments are split between principal and interest</li>
<li><strong>Future value calculations:</strong> Determine investment growth over time</li>
<li><strong>Present value calculations:</strong> Calculate current worth of future payments</li>
<li><strong>Internal rate of return:</strong> Evaluate investment profitability</li>
</ul>

<p>Mastering financial calculators empowers you to make informed decisions about loans, mortgages, and investments, helping you achieve your financial goals more effectively.</p>
                ''',
                'category': 'financial-planning',
                'tags': ['calculators', 'finance', 'guides', 'tips'],
                'meta_title': 'Financial Calculator Guide - Loan & Mortgage Tips',
                'meta_description': 'Master financial calculators for loans, mortgages, and investments. Learn key formulas and calculator functions for better financial planning.',
                'meta_keywords': 'financial calculator, loan calculator, mortgage calculator, investment calculator'
            },
            {
                'title': 'BMI Calculator: Understanding Your Body Mass Index',
                'excerpt': 'Learn how BMI calculators work and how to interpret your results. Understand the relationship between weight, height, and health indicators.',
                'content': '''
<h2>What is BMI?</h2>
<p>Body Mass Index (BMI) is a widely used measure to assess whether a person has a healthy body weight for their height. It's calculated using a simple formula that provides a numerical value indicating weight status.</p>

<h2>BMI Calculation Formula</h2>
<p>The BMI formula is straightforward:</p>
<p><strong>BMI = weight (kg) / height (m)²</strong></p>
<p>Or in imperial units:</p>
<p><strong>BMI = (weight in pounds × 703) / (height in inches)²</strong></p>

<h2>BMI Categories</h2>
<p>BMI results are categorized as follows:</p>
<ul>
<li><strong>Underweight:</strong> BMI less than 18.5</li>
<li><strong>Normal weight:</strong> BMI 18.5 to 24.9</li>
<li><strong>Overweight:</strong> BMI 25 to 29.9</li>
<li><strong>Obesity:</strong> BMI 30 or higher</li>
</ul>

<h2>Using BMI Calculators</h2>
<p>Online BMI calculators make it easy to determine your BMI:</p>
<ol>
<li>Enter your weight</li>
<li>Enter your height</li>
<li>Select your measurement system (metric or imperial)</li>
<li>Click calculate</li>
</ol>

<h2>Understanding Your Results</h2>
<h3>Limitations of BMI</h3>
<p>While BMI is a useful screening tool, it has limitations:</p>
<ul>
<li>Doesn't distinguish between muscle and fat</li>
<li>May not be accurate for athletes with high muscle mass</li>
<li>Doesn't account for bone density</li>
<li>May not be suitable for children or elderly individuals</li>
</ul>

<h2>When to Use BMI</h2>
<p>BMI is most useful for:</p>
<ul>
<li>General population health screening</li>
<li>Tracking weight changes over time</li>
<li>Identifying potential health risks</li>
<li>Setting weight management goals</li>
</ul>

<h2>Beyond BMI</h2>
<p>For a complete health assessment, consider additional factors:</p>
<ul>
<li>Waist circumference</li>
<li>Body fat percentage</li>
<li>Muscle mass</li>
<li>Overall fitness level</li>
<li>Medical history</li>
</ul>

<h2>Tips for Healthy Weight Management</h2>
<ul>
<li>Focus on balanced nutrition</li>
<li>Engage in regular physical activity</li>
<li>Get adequate sleep</li>
<li>Manage stress effectively</li>
<li>Consult healthcare professionals for personalized advice</li>
</ul>

<p>Remember, BMI is just one tool in assessing health. Always consult with healthcare professionals for comprehensive health evaluations and personalized recommendations.</p>
                ''',
                'category': 'health-fitness',
                'tags': ['calculators', 'health', 'bmi', 'tips'],
                'meta_title': 'BMI Calculator Guide - Understanding Body Mass Index',
                'meta_description': 'Learn how BMI calculators work and interpret your results. Understand weight, height, and health indicators for better wellness.',
                'meta_keywords': 'BMI calculator, body mass index, health calculator, weight calculator'
            },
            {
                'title': 'Percentage Calculator: Quick Tips for Everyday Calculations',
                'excerpt': 'Master percentage calculations with our easy guide. Learn formulas, shortcuts, and practical examples for discounts, tips, and more.',
                'content': '''
<h2>Understanding Percentages</h2>
<p>Percentages are everywhere in daily life - from calculating discounts and tips to understanding statistics and financial data. Mastering percentage calculations can make many tasks quicker and easier.</p>

<h2>Basic Percentage Formula</h2>
<p>The fundamental percentage formula is:</p>
<p><strong>Percentage = (Part / Whole) × 100</strong></p>

<h2>Common Percentage Calculations</h2>
<h3>Finding a Percentage of a Number</h3>
<p>To find what percentage one number is of another:</p>
<p><strong>Example:</strong> What is 25% of 200?</p>
<p>25% × 200 = 0.25 × 200 = 50</p>

<h3>Finding What Percentage One Number Is of Another</h3>
<p><strong>Example:</strong> 30 is what percentage of 150?</p>
<p>(30 / 150) × 100 = 20%</p>

<h3>Percentage Increase or Decrease</h3>
<p>To calculate percentage change:</p>
<p><strong>Percentage Change = [(New Value - Old Value) / Old Value] × 100</strong></p>

<h2>Practical Applications</h2>
<h3>Calculating Discounts</h3>
<p>When shopping, quickly calculate sale prices:</p>
<ul>
<li>Original price: $100</li>
<li>Discount: 20%</li>
<li>Sale price: $100 - ($100 × 0.20) = $80</li>
</ul>

<h3>Calculating Tips</h3>
<p>For restaurant tips, common percentages are:</p>
<ul>
<li>15% for standard service</li>
<li>18% for good service</li>
<li>20% for excellent service</li>
</ul>
<p><strong>Example:</strong> Bill is $50, tip 18%</p>
<p>$50 × 0.18 = $9 tip</p>

<h3>Tax Calculations</h3>
<p>Calculate sales tax easily:</p>
<p><strong>Example:</strong> Item costs $75, tax is 8%</p>
<p>$75 × 0.08 = $6 tax</p>
<p>Total: $75 + $6 = $81</p>

<h2>Quick Calculation Tips</h2>
<ul>
<li><strong>10%:</strong> Move decimal point one place left</li>
<li><strong>5%:</strong> Calculate 10% and divide by 2</li>
<li><strong>20%:</strong> Calculate 10% and multiply by 2</li>
<li><strong>25%:</strong> Divide by 4</li>
<li><strong>50%:</strong> Divide by 2</li>
</ul>

<h2>Using Percentage Calculators</h2>
<p>Online percentage calculators can handle:</p>
<ul>
<li>Finding percentages of numbers</li>
<li>Calculating percentage increases/decreases</li>
<li>Converting between fractions and percentages</li>
<li>Solving percentage word problems</li>
</ul>

<h2>Common Mistakes to Avoid</h2>
<ul>
<li>Forgetting to convert percentage to decimal (divide by 100)</li>
<li>Confusing percentage increase with percentage of total</li>
<li>Not considering the base value correctly</li>
<li>Mixing up percentage points and percentages</li>
</ul>

<h2>Advanced Percentage Concepts</h2>
<h3>Compound Percentages</h3>
<p>When percentages are applied multiple times, use compound calculations carefully.</p>

<h3>Percentage Points vs. Percentages</h3>
<p>Understand the difference: a change from 5% to 7% is a 2 percentage point increase, but a 40% relative increase.</p>

<p>With these tips and formulas, you'll be able to handle percentage calculations confidently in everyday situations and professional contexts.</p>
                ''',
                'category': 'math-tips',
                'tags': ['calculators', 'math', 'percentage', 'tips'],
                'meta_title': 'Percentage Calculator Guide - Quick Calculation Tips',
                'meta_description': 'Master percentage calculations with easy formulas and shortcuts. Learn to calculate discounts, tips, taxes, and more efficiently.',
                'meta_keywords': 'percentage calculator, percentage formula, discount calculator, tip calculator'
            },
            {
                'title': 'Area Calculator: Measuring Shapes and Spaces Accurately',
                'excerpt': 'Learn how to calculate areas of various shapes using area calculators. Master formulas for rectangles, circles, triangles, and complex shapes.',
                'content': '''
<h2>Understanding Area Calculations</h2>
<p>Calculating area is essential for countless practical applications - from home improvement projects to academic studies. Area calculators simplify these calculations, but understanding the underlying formulas helps ensure accuracy.</p>

<h2>Basic Shape Formulas</h2>
<h3>Rectangle</h3>
<p><strong>Area = length × width</strong></p>
<p>The simplest area calculation, perfect for rooms, gardens, and rectangular spaces.</p>

<h3>Square</h3>
<p><strong>Area = side²</strong></p>
<p>A special case of rectangle where all sides are equal.</p>

<h3>Circle</h3>
<p><strong>Area = π × radius²</strong></p>
<p>Essential for circular spaces, with π approximately equal to 3.14159.</p>

<h3>Triangle</h3>
<p><strong>Area = (base × height) / 2</strong></p>
<p>Useful for triangular spaces and as building blocks for complex shapes.</p>

<h2>Complex Shape Calculations</h2>
<h3>Trapezoid</h3>
<p><strong>Area = [(a + b) / 2] × height</strong></p>
<p>Where a and b are the lengths of the parallel sides.</p>

<h3>Parallelogram</h3>
<p><strong>Area = base × height</strong></p>
<p>Similar to rectangle but with slanted sides.</p>

<h3>Ellipse</h3>
<p><strong>Area = π × a × b</strong></p>
<p>Where a and b are the semi-major and semi-minor axes.</p>

<h2>Practical Applications</h2>
<h3>Home Improvement</h3>
<ul>
<li>Calculating floor area for flooring materials</li>
<li>Determining paint coverage</li>
<li>Planning garden layouts</li>
<li>Measuring wall areas for wallpaper</li>
</ul>

<h3>Construction</h3>
<ul>
<li>Site planning and development</li>
<li>Material quantity estimation</li>
<li>Cost calculations based on area</li>
</ul>

<h2>Using Area Calculators</h2>
<p>Online area calculators offer several advantages:</p>
<ul>
<li>Quick calculations for multiple shapes</li>
<li>Automatic unit conversions</li>
<li>Step-by-step solutions</li>
<li>Visual representations</li>
</ul>

<h2>Unit Conversions</h2>
<p>Common area units and conversions:</p>
<ul>
<li>Square meters (m²)</li>
<li>Square feet (ft²)</li>
<li>Square inches (in²)</li>
<li>Acres</li>
<li>Hectares</li>
</ul>
<p><strong>Conversion tip:</strong> 1 square meter = 10.764 square feet</p>

<h2>Tips for Accurate Measurements</h2>
<ul>
<li>Measure twice, calculate once</li>
<li>Use consistent units throughout</li>
<li>Account for irregular shapes by breaking them into simpler parts</li>
<li>Consider measurement precision</li>
<li>Double-check calculator inputs</li>
</ul>

<h2>Common Mistakes</h2>
<ul>
<li>Mixing units (meters with feet)</li>
<li>Confusing area with perimeter</li>
<li>Using diameter instead of radius for circles</li>
<li>Forgetting to divide by 2 for triangles</li>
</ul>

<h2>Advanced Techniques</h2>
<h3>Composite Shapes</h3>
<p>Break complex shapes into simpler components, calculate each area, then add or subtract as needed.</p>

<h3>Irregular Shapes</h3>
<p>For irregular shapes, use approximation methods or divide into smaller regular shapes.</p>

<p>Mastering area calculations empowers you to tackle projects confidently, whether you're renovating your home, planning a garden, or solving academic problems.</p>
                ''',
                'category': 'calculator-guides',
                'tags': ['calculators', 'math', 'area', 'guides'],
                'meta_title': 'Area Calculator Guide - Measure Shapes Accurately',
                'meta_description': 'Learn to calculate areas of rectangles, circles, triangles, and complex shapes. Master formulas and use area calculators effectively.',
                'meta_keywords': 'area calculator, area formula, shape calculator, measurement calculator'
            },
            {
                'title': 'Calorie Calculator: Understanding Your Daily Energy Needs',
                'excerpt': 'Discover how calorie calculators work and learn to determine your daily caloric needs. Master BMR, TDEE, and weight management calculations.',
                'content': '''
<h2>Understanding Calories</h2>
<p>Calories are units of energy that our bodies use for all functions - from breathing and thinking to physical activity. Understanding your daily caloric needs is fundamental to achieving health and fitness goals.</p>

<h2>Key Concepts</h2>
<h3>BMR (Basal Metabolic Rate)</h3>
<p>BMR represents the calories your body burns at rest to maintain basic functions. It accounts for 60-75% of total daily energy expenditure.</p>

<h3>TDEE (Total Daily Energy Expenditure)</h3>
<p>TDEE includes BMR plus calories burned through physical activity and digestion. This is your total daily calorie needs.</p>

<h2>Calorie Calculation Formulas</h2>
<h3>Harris-Benedict Equation</h3>
<p><strong>Men:</strong> BMR = 88.362 + (13.397 × weight in kg) + (4.799 × height in cm) - (5.677 × age)</p>
<p><strong>Women:</strong> BMR = 447.593 + (9.247 × weight in kg) + (3.098 × height in cm) - (4.330 × age)</p>

<h3>Mifflin-St Jeor Equation</h3>
<p>Considered more accurate:</p>
<p><strong>Men:</strong> BMR = (10 × weight in kg) + (6.25 × height in cm) - (5 × age) + 5</p>
<p><strong>Women:</strong> BMR = (10 × weight in kg) + (6.25 × height in cm) - (5 × age) - 161</p>

<h2>Activity Multipliers</h2>
<p>Multiply BMR by activity level to get TDEE:</p>
<ul>
<li><strong>Sedentary:</strong> BMR × 1.2</li>
<li><strong>Lightly active:</strong> BMR × 1.375</li>
<li><strong>Moderately active:</strong> BMR × 1.55</li>
<li><strong>Very active:</strong> BMR × 1.725</li>
<li><strong>Extra active:</strong> BMR × 1.9</li>
</ul>

<h2>Using Calorie Calculators</h2>
<p>Online calorie calculators simplify these calculations:</p>
<ol>
<li>Enter your age, gender, height, and weight</li>
<li>Select your activity level</li>
<li>Choose your goal (maintain, lose, or gain weight)</li>
<li>Get personalized calorie recommendations</li>
</ol>

<h2>Weight Management Goals</h2>
<h3>Weight Loss</h3>
<p>To lose weight, create a calorie deficit:</p>
<ul>
<li>Moderate deficit: 500 calories per day (1 lb/week loss)</li>
<li>Aggressive deficit: 1000 calories per day (2 lbs/week loss)</li>
</ul>

<h3>Weight Gain</h3>
<p>To gain weight, create a calorie surplus:</p>
<ul>
<li>Moderate surplus: 300-500 calories per day</li>
<li>Focus on quality nutrition, not just calories</li>
</ul>

<h2>Factors Affecting Calorie Needs</h2>
<ul>
<li>Age (metabolism slows with age)</li>
<li>Gender (men typically need more calories)</li>
<li>Body composition (muscle burns more calories)</li>
<li>Activity level</li>
<li>Genetics</li>
<li>Medical conditions</li>
</ul>

<h2>Tips for Accurate Tracking</h2>
<ul>
<li>Use a food scale for precise measurements</li>
<li>Track everything you eat and drink</li>
<li>Be honest about portion sizes</li>
<li>Account for cooking methods and added ingredients</li>
<li>Review and adjust based on results</li>
</ul>

<h2>Beyond Calories</h2>
<p>While calories matter, also consider:</p>
<ul>
<li>Macronutrient balance (protein, carbs, fats)</li>
<li>Nutrient density</li>
<li>Meal timing</li>
<li>Food quality</li>
</ul>

<h2>Common Mistakes</h2>
<ul>
<li>Underestimating portion sizes</li>
<li>Not accounting for beverages</li>
<li>Overestimating activity level</li>
<li>Setting unrealistic calorie goals</li>
<li>Ignoring hunger and satiety signals</li>
</ul>

<p>Understanding your caloric needs through accurate calculations helps you make informed decisions about nutrition and achieve your health and fitness goals more effectively.</p>
                ''',
                'category': 'health-fitness',
                'tags': ['calculators', 'health', 'calories', 'fitness'],
                'meta_title': 'Calorie Calculator Guide - Daily Energy Needs',
                'meta_description': 'Learn how calorie calculators work. Understand BMR, TDEE, and calculate your daily caloric needs for weight management.',
                'meta_keywords': 'calorie calculator, BMR calculator, TDEE calculator, weight management'
            }
        ]
        
        # Create posts with staggered dates
        base_date = timezone.now()
        created_count = 0
        
        for i, post_data in enumerate(posts_data):
            category = categories[post_data['category']]
            
            # Create post
            post = Post(
                title=post_data['title'],
                author=user,
                category=category,
                content=post_data['content'].strip(),
                excerpt=post_data['excerpt'],
                status='published',
                published_date=base_date - timedelta(days=i),
                meta_title=post_data.get('meta_title', ''),
                meta_description=post_data.get('meta_description', ''),
                meta_keywords=post_data.get('meta_keywords', ''),
            )
            post.save()
            
            # Add tags
            for tag_name in post_data['tags']:
                if tag_name in tags_dict:
                    post.tags.add(tags_dict[tag_name])
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created post: {post.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} new blog posts!'))
