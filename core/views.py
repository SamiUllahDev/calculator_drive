from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

# Create your views here.

class Index(View):  # Changed to PascalCase naming convention
    def get(self, request):
        return render(request, 'core/index.html')


class PrivacyPolicyView(TemplateView):
    template_name = 'core/privacy_policy.html'


class TermsOfServiceView(TemplateView):
    template_name = 'core/terms_of_service.html'


class CookiePolicyView(TemplateView):
    template_name = 'core/cookie_policy.html'


class SitemapView(View):
    def get(self, request):
        # Get all calculators from all apps
        from Math_Calculators.views.index import MathIndexView
        from Financial_Calculators.views.index import FinanceIndexView
        from Fitness_and_Health_Calculators.views.index import HealthIndexView
        from Other_Calculators.views.index import OtherIndexView
        
        calculators_by_app = {
            'math': {
                'name': 'Mathematics Calculators',
                'icon': 'bi-calculator',
                'color': 'purple',
                'calculators': MathIndexView().get_context_data().get('calculators', []),
                'base_url': '/math/',
            },
            'finance': {
                'name': 'Financial Calculators',
                'icon': 'bi-graph-up',
                'color': 'blue',
                'calculators': FinanceIndexView().get_context_data().get('calculators', []),
                'base_url': '/finance/',
            },
            'health': {
                'name': 'Health & Fitness Calculators',
                'icon': 'bi-heart-pulse',
                'color': 'green',
                'calculators': HealthIndexView().get_context_data().get('calculators', []),
                'base_url': '/health/',
            },
            'other': {
                'name': 'Other Calculators',
                'icon': 'bi-tools',
                'color': 'orange',
                'calculators': OtherIndexView().get_context_data().get('calculators', []),
                'base_url': '/other/',
            },
        }
        
        context = {
            'calculators_by_app': calculators_by_app,
            'total_calculators': sum(len(app['calculators']) for app in calculators_by_app.values()),
        }
        
        return render(request, 'core/sitemap.html', context)


class SearchView(View):
    def get_all_calculators(self):
        """Collect all calculators from all apps"""
        all_calculators = []
        
        # Math Calculators
        from Math_Calculators.views.index import MathIndexView
        math_view = MathIndexView()
        math_context = math_view.get_context_data()
        for calc in math_context.get('calculators', []):
            calc_copy = calc.copy()
            calc_copy['app'] = 'math'
            calc_copy['base_url'] = '/math/'
            all_calculators.append(calc_copy)
        
        # Finance Calculators
        from Financial_Calculators.views.index import FinanceIndexView
        finance_view = FinanceIndexView()
        finance_context = finance_view.get_context_data()
        for calc in finance_context.get('calculators', []):
            calc_copy = calc.copy()
            calc_copy['app'] = 'finance'
            calc_copy['base_url'] = '/finance/'
            all_calculators.append(calc_copy)
        
        # Health Calculators
        from Fitness_and_Health_Calculators.views.index import HealthIndexView
        health_view = HealthIndexView()
        health_context = health_view.get_context_data()
        for calc in health_context.get('calculators', []):
            calc_copy = calc.copy()
            calc_copy['app'] = 'health'
            calc_copy['base_url'] = '/health/'
            all_calculators.append(calc_copy)
        
        # Other Calculators
        from Other_Calculators.views.index import OtherIndexView
        other_view = OtherIndexView()
        other_context = other_view.get_context_data()
        for calc in other_context.get('calculators', []):
            calc_copy = calc.copy()
            calc_copy['app'] = 'other'
            calc_copy['base_url'] = '/other/'
            all_calculators.append(calc_copy)
        
        return all_calculators
    
    def search_calculators(self, query, calculators):
        """Search through calculators by name, description, or category"""
        if not query or not query.strip():
            return []
        
        query_lower = query.lower().strip()
        query_words = query_lower.split()
        
        results = []
        for calc in calculators:
            name = calc.get('name', '').lower()
            description = calc.get('description', '').lower()
            category = calc.get('category', '').lower()
            url = calc.get('url', '').lower()
            
            # Calculate relevance score
            score = 0
            
            # Exact match in name (highest priority)
            if query_lower == name:
                score += 200
            elif name.startswith(query_lower):
                score += 150
            elif query_lower in name:
                score += 100
            
            # Word matches in name
            for word in query_words:
                if word in name:
                    score += 50
                if name.startswith(word):
                    score += 30
                if name.endswith(word):
                    score += 20
            
            # Matches in description
            for word in query_words:
                if word in description:
                    score += 10
                if word in category:
                    score += 15
                if word in url:
                    score += 5
            
            # Partial word matches
            for word in query_words:
                if any(word in name_part for name_part in name.split()):
                    score += 25
                if any(word in desc_part for desc_part in description.split()):
                    score += 5
            
            if score > 0:
                calc['relevance_score'] = score
                results.append(calc)
        
        # Sort by relevance score (highest first)
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return results
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        calculators = self.get_all_calculators()
        results = []
        categories = set()
        apps = set()
        
        if query:
            results = self.search_calculators(query, calculators)
            # Get unique categories and apps from results
            for calc in results:
                if calc.get('category'):
                    categories.add(calc['category'])
                if calc.get('app'):
                    apps.add(calc['app'])
        
        # Group results by category
        results_by_category = {}
        for calc in results:
            category = calc.get('category', 'Other')
            if category not in results_by_category:
                results_by_category[category] = []
            results_by_category[category].append(calc)
        
        context = {
            'query': query,
            'results': results,
            'results_by_category': results_by_category,
            'total_results': len(results),
            'total_calculators': len(calculators),
            'categories': sorted(categories),
            'apps': sorted(apps),
        }
        
        return render(request, 'core/search_results.html', context)