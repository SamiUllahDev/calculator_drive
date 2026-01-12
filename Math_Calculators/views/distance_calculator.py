from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DistanceCalculator(View):
    """
    Professional Distance Calculator
    Calculates various types of distances between points.
    Supports 2D, 3D, Manhattan, Minkowski, and geographic distances.
    """
    template_name = 'math_calculators/distance_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Distance Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value, name):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_euclidean_2d(self, x1, y1, x2, y2):
        """Calculate Euclidean distance in 2D"""
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return distance
    
    def _calculate_euclidean_3d(self, x1, y1, z1, x2, y2, z2):
        """Calculate Euclidean distance in 3D"""
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
        return distance
    
    def _calculate_manhattan_2d(self, x1, y1, x2, y2):
        """Calculate Manhattan distance in 2D"""
        distance = abs(x2 - x1) + abs(y2 - y1)
        return distance
    
    def _calculate_manhattan_3d(self, x1, y1, z1, x2, y2, z2):
        """Calculate Manhattan distance in 3D"""
        distance = abs(x2 - x1) + abs(y2 - y1) + abs(z2 - z1)
        return distance
    
    def _calculate_minkowski(self, point1, point2, p):
        """Calculate Minkowski distance"""
        if len(point1) != len(point2):
            return None, 'Points must have the same dimension.'
        
        if p <= 0:
            return None, 'p must be greater than 0.'
        
        if p == float('inf'):
            # Chebyshev distance
            distance = max(abs(point2[i] - point1[i]) for i in range(len(point1)))
        else:
            sum_powers = sum(abs(point2[i] - point1[i]) ** p for i in range(len(point1)))
            distance = sum_powers ** (1 / p)
        
        return distance, None
    
    def _calculate_geographic_distance(self, lat1, lon1, lat2, lon2):
        """Calculate geographic distance using Haversine formula"""
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        earth_radius_km = 6371.0
        
        # Distance in kilometers
        distance_km = earth_radius_km * c
        
        return distance_km
    
    def prepare_chart_data(self, distance_type, result_data):
        """Prepare chart data for distance visualization"""
        if not result_data:
            return {}
        
        if distance_type in ['euclidean_2d', 'manhattan_2d']:
            # 2D visualization
            x1 = result_data.get('x1', 0)
            y1 = result_data.get('y1', 0)
            x2 = result_data.get('x2', 0)
            y2 = result_data.get('y2', 0)
            distance = result_data.get('distance', 0)
            
            # Create scatter plot showing the two points and the distance
            chart_data = {
                'type': 'scatter',
                'data': {
                    'datasets': [
                        {
                            'label': 'Point 1',
                            'data': [{'x': x1, 'y': y1}],
                            'backgroundColor': 'rgba(59, 130, 246, 0.8)',
                            'borderColor': '#3b82f6',
                            'pointRadius': 8,
                            'pointHoverRadius': 10
                        },
                        {
                            'label': 'Point 2',
                            'data': [{'x': x2, 'y': y2}],
                            'backgroundColor': 'rgba(16, 185, 129, 0.8)',
                            'borderColor': '#10b981',
                            'pointRadius': 8,
                            'pointHoverRadius': 10
                        },
                        {
                            'label': 'Distance',
                            'data': [
                                {'x': x1, 'y': y1},
                                {'x': x2, 'y': y2}
                            ],
                            'type': 'line',
                            'backgroundColor': 'rgba(239, 68, 68, 0.3)',
                            'borderColor': '#ef4444',
                            'borderWidth': 2,
                            'pointRadius': 0,
                            'showLine': True
                        }
                    ]
                }
            }
            
            return {'distance_chart': chart_data}
        
        elif distance_type == 'euclidean_3d':
            # 3D visualization would require a 3D library, so we'll show a comparison chart
            distance = result_data.get('distance', 0)
            x_dist = abs(result_data.get('x2', 0) - result_data.get('x1', 0))
            y_dist = abs(result_data.get('y2', 0) - result_data.get('y1', 0))
            z_dist = abs(result_data.get('z2', 0) - result_data.get('z1', 0))
            
            chart_data = {
                'type': 'bar',
                'data': {
                    'labels': ['X Distance', 'Y Distance', 'Z Distance', 'Total Distance'],
                    'datasets': [{
                        'label': 'Distance Components',
                        'data': [x_dist, y_dist, z_dist, distance],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)',
                            'rgba(245, 158, 11, 0.6)',
                            'rgba(239, 68, 68, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b',
                            '#ef4444'
                        ],
                        'borderWidth': 2
                    }]
                }
            }
            
            return {'distance_chart': chart_data}
        
        elif distance_type == 'geographic':
            distance_km = result_data.get('distance_km', 0)
            distance_miles = result_data.get('distance_miles', 0)
            
            chart_data = {
                'type': 'doughnut',
                'data': {
                    'labels': ['Distance (km)', 'Distance (miles)'],
                    'datasets': [{
                        'data': [distance_km, distance_miles],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981'
                        ],
                        'borderWidth': 2
                    }]
                }
            }
            
            return {'distance_chart': chart_data}
        
        return {}
    
    def prepare_display_data(self, distance_type, result_data):
        """Prepare formatted display data for frontend"""
        display_data = {
            'distance_type': distance_type,
            'result_data': result_data,
            'formatted_results': []
        }
        
        if distance_type in ['euclidean_2d', 'manhattan_2d']:
            display_data['formatted_results'] = [
                {
                    'label': 'Point 1',
                    'value': f"({result_data.get('x1', 0):.6f}, {result_data.get('y1', 0):.6f})",
                    'is_primary': False
                },
                {
                    'label': 'Point 2',
                    'value': f"({result_data.get('x2', 0):.6f}, {result_data.get('y2', 0):.6f})",
                    'is_primary': False
                },
                {
                    'label': 'Distance',
                    'value': f"{result_data.get('distance', 0):.6f}",
                    'is_primary': True
                },
                {
                    'label': 'Distance Type',
                    'value': 'Euclidean' if distance_type == 'euclidean_2d' else 'Manhattan',
                    'is_primary': False
                }
            ]
        elif distance_type == 'euclidean_3d':
            display_data['formatted_results'] = [
                {
                    'label': 'Point 1',
                    'value': f"({result_data.get('x1', 0):.6f}, {result_data.get('y1', 0):.6f}, {result_data.get('z1', 0):.6f})",
                    'is_primary': False
                },
                {
                    'label': 'Point 2',
                    'value': f"({result_data.get('x2', 0):.6f}, {result_data.get('y2', 0):.6f}, {result_data.get('z2', 0):.6f})",
                    'is_primary': False
                },
                {
                    'label': 'Distance',
                    'value': f"{result_data.get('distance', 0):.6f}",
                    'is_primary': True
                },
                {
                    'label': 'X Distance',
                    'value': f"{abs(result_data.get('x2', 0) - result_data.get('x1', 0)):.6f}",
                    'is_primary': False
                },
                {
                    'label': 'Y Distance',
                    'value': f"{abs(result_data.get('y2', 0) - result_data.get('y1', 0)):.6f}",
                    'is_primary': False
                },
                {
                    'label': 'Z Distance',
                    'value': f"{abs(result_data.get('z2', 0) - result_data.get('z1', 0)):.6f}",
                    'is_primary': False
                }
            ]
        elif distance_type == 'geographic':
            display_data['formatted_results'] = [
                {
                    'label': 'Point 1 (Lat, Lon)',
                    'value': f"({result_data.get('lat1', 0):.6f}°, {result_data.get('lon1', 0):.6f}°)",
                    'is_primary': False
                },
                {
                    'label': 'Point 2 (Lat, Lon)',
                    'value': f"({result_data.get('lat2', 0):.6f}°, {result_data.get('lon2', 0):.6f}°)",
                    'is_primary': False
                },
                {
                    'label': 'Distance (Kilometers)',
                    'value': f"{result_data.get('distance_km', 0):.6f} km",
                    'is_primary': True
                },
                {
                    'label': 'Distance (Miles)',
                    'value': f"{result_data.get('distance_miles', 0):.6f} miles",
                    'is_primary': True
                }
            ]
        elif distance_type == 'minkowski':
            display_data['formatted_results'] = [
                {
                    'label': 'Point 1',
                    'value': str(result_data.get('point1', [])),
                    'is_primary': False
                },
                {
                    'label': 'Point 2',
                    'value': str(result_data.get('point2', [])),
                    'is_primary': False
                },
                {
                    'label': 'Distance (p=' + str(result_data.get('p', 0)) + ')',
                    'value': f"{result_data.get('distance', 0):.6f}",
                    'is_primary': True
                },
                {
                    'label': 'p value',
                    'value': str(result_data.get('p', 0)),
                    'is_primary': False
                }
            ]
        
        return display_data
    
    def prepare_step_by_step(self, distance_type, result_data):
        """Prepare step-by-step solution"""
        steps = []
        
        if distance_type == 'euclidean_2d':
            x1 = result_data.get('x1', 0)
            y1 = result_data.get('y1', 0)
            x2 = result_data.get('x2', 0)
            y2 = result_data.get('y2', 0)
            distance = result_data.get('distance', 0)
            
            steps.append(f"Given points:")
            steps.append(f"  Point 1: ({x1:.6f}, {y1:.6f})")
            steps.append(f"  Point 2: ({x2:.6f}, {y2:.6f})")
            steps.append(f"Step 1: Calculate the difference in x-coordinates")
            dx = x2 - x1
            steps.append(f"  Δx = x₂ - x₁ = {x2:.6f} - {x1:.6f} = {dx:.6f}")
            steps.append(f"Step 2: Calculate the difference in y-coordinates")
            dy = y2 - y1
            steps.append(f"  Δy = y₂ - y₁ = {y2:.6f} - {y1:.6f} = {dy:.6f}")
            steps.append(f"Step 3: Apply the Euclidean distance formula")
            steps.append(f"  d = √(Δx² + Δy²)")
            steps.append(f"  d = √({dx:.6f}² + {dy:.6f}²)")
            steps.append(f"  d = √({dx**2:.6f} + {dy**2:.6f})")
            steps.append(f"  d = √{dx**2 + dy**2:.6f}")
            steps.append(f"  d = {distance:.6f}")
        
        elif distance_type == 'manhattan_2d':
            x1 = result_data.get('x1', 0)
            y1 = result_data.get('y1', 0)
            x2 = result_data.get('x2', 0)
            y2 = result_data.get('y2', 0)
            distance = result_data.get('distance', 0)
            
            steps.append(f"Given points:")
            steps.append(f"  Point 1: ({x1:.6f}, {y1:.6f})")
            steps.append(f"  Point 2: ({x2:.6f}, {y2:.6f})")
            steps.append(f"Step 1: Calculate the absolute difference in x-coordinates")
            dx = abs(x2 - x1)
            steps.append(f"  |Δx| = |x₂ - x₁| = |{x2:.6f} - {x1:.6f}| = {dx:.6f}")
            steps.append(f"Step 2: Calculate the absolute difference in y-coordinates")
            dy = abs(y2 - y1)
            steps.append(f"  |Δy| = |y₂ - y₁| = |{y2:.6f} - {y1:.6f}| = {dy:.6f}")
            steps.append(f"Step 3: Apply the Manhattan distance formula")
            steps.append(f"  d = |Δx| + |Δy|")
            steps.append(f"  d = {dx:.6f} + {dy:.6f}")
            steps.append(f"  d = {distance:.6f}")
        
        elif distance_type == 'euclidean_3d':
            x1 = result_data.get('x1', 0)
            y1 = result_data.get('y1', 0)
            z1 = result_data.get('z1', 0)
            x2 = result_data.get('x2', 0)
            y2 = result_data.get('y2', 0)
            z2 = result_data.get('z2', 0)
            distance = result_data.get('distance', 0)
            
            steps.append(f"Given points:")
            steps.append(f"  Point 1: ({x1:.6f}, {y1:.6f}, {z1:.6f})")
            steps.append(f"  Point 2: ({x2:.6f}, {y2:.6f}, {z2:.6f})")
            steps.append(f"Step 1: Calculate differences in each coordinate")
            dx = x2 - x1
            dy = y2 - y1
            dz = z2 - z1
            steps.append(f"  Δx = {dx:.6f}, Δy = {dy:.6f}, Δz = {dz:.6f}")
            steps.append(f"Step 2: Apply the 3D Euclidean distance formula")
            steps.append(f"  d = √(Δx² + Δy² + Δz²)")
            steps.append(f"  d = √({dx**2:.6f} + {dy**2:.6f} + {dz**2:.6f})")
            steps.append(f"  d = {distance:.6f}")
        
        elif distance_type == 'geographic':
            lat1 = result_data.get('lat1', 0)
            lon1 = result_data.get('lon1', 0)
            lat2 = result_data.get('lat2', 0)
            lon2 = result_data.get('lon2', 0)
            distance_km = result_data.get('distance_km', 0)
            
            steps.append(f"Given coordinates:")
            steps.append(f"  Point 1: ({lat1:.6f}°, {lon1:.6f}°)")
            steps.append(f"  Point 2: ({lat2:.6f}°, {lon2:.6f}°)")
            steps.append(f"Step 1: Convert coordinates to radians")
            steps.append(f"  Using Haversine formula for great-circle distance")
            steps.append(f"Step 2: Calculate differences")
            dlat = math.radians(lat2) - math.radians(lat1)
            dlon = math.radians(lon2) - math.radians(lon1)
            steps.append(f"  Δlat = {dlat:.6f} radians, Δlon = {dlon:.6f} radians")
            steps.append(f"Step 3: Apply Haversine formula")
            steps.append(f"  a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)")
            steps.append(f"  c = 2 × atan2(√a, √(1-a))")
            steps.append(f"  d = R × c (where R = 6371 km)")
            steps.append(f"Step 4: Result")
            steps.append(f"  Distance = {distance_km:.6f} km")
            steps.append(f"  Distance = {distance_km * 0.621371:.6f} miles")
        
        elif distance_type == 'minkowski':
            point1 = result_data.get('point1', [])
            point2 = result_data.get('point2', [])
            p = result_data.get('p', 0)
            distance = result_data.get('distance', 0)
            
            steps.append(f"Given points:")
            steps.append(f"  Point 1: {point1}")
            steps.append(f"  Point 2: {point2}")
            steps.append(f"  p = {p}")
            steps.append(f"Step 1: Calculate differences for each dimension")
            differences = [abs(point2[i] - point1[i]) for i in range(len(point1))]
            for i, diff in enumerate(differences):
                steps.append(f"  |x₂[{i}] - x₁[{i}]| = {diff:.6f}")
            steps.append(f"Step 2: Apply Minkowski distance formula")
            if p == float('inf'):
                steps.append(f"  d = max(|x₂[i] - x₁[i]|) = {distance:.6f} (Chebyshev distance)")
            else:
                sum_powers = sum(diff ** p for diff in differences)
                steps.append(f"  d = (Σ|x₂[i] - x₁[i]|ᵖ)^(1/p)")
                steps.append(f"  d = ({sum_powers:.6f})^(1/{p})")
                steps.append(f"  d = {distance:.6f}")
        
        return steps
    
    def prepare_step_by_step_html(self, steps):
        """Prepare step-by-step solution as HTML structure"""
        if not steps or not isinstance(steps, list):
            return []
        
        return [{'step_number': idx + 1, 'content': step} for idx, step in enumerate(steps)]
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            distance_type = data.get('distance_type', 'euclidean_2d')
            result_data = {}
            distance = 0
            
            if distance_type == 'euclidean_2d':
                x1, error = self._validate_number(data.get('x1'), 'x1')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                y1, error = self._validate_number(data.get('y1'), 'y1')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                x2, error = self._validate_number(data.get('x2'), 'x2')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                y2, error = self._validate_number(data.get('y2'), 'y2')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                distance = self._calculate_euclidean_2d(x1, y1, x2, y2)
                result_data = {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'distance': distance}
            
            elif distance_type == 'euclidean_3d':
                x1, error = self._validate_number(data.get('x1'), 'x1')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                y1, error = self._validate_number(data.get('y1'), 'y1')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                z1, error = self._validate_number(data.get('z1'), 'z1')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                x2, error = self._validate_number(data.get('x2'), 'x2')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                y2, error = self._validate_number(data.get('y2'), 'y2')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                z2, error = self._validate_number(data.get('z2'), 'z2')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                distance = self._calculate_euclidean_3d(x1, y1, z1, x2, y2, z2)
                result_data = {'x1': x1, 'y1': y1, 'z1': z1, 'x2': x2, 'y2': y2, 'z2': z2, 'distance': distance}
            
            elif distance_type == 'manhattan_2d':
                x1, error = self._validate_number(data.get('x1'), 'x1')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                y1, error = self._validate_number(data.get('y1'), 'y1')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                x2, error = self._validate_number(data.get('x2'), 'x2')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                y2, error = self._validate_number(data.get('y2'), 'y2')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                distance = self._calculate_manhattan_2d(x1, y1, x2, y2)
                result_data = {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'distance': distance}
            
            elif distance_type == 'geographic':
                lat1, error = self._validate_number(data.get('lat1'), 'Latitude 1')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                if lat1 < -90 or lat1 > 90:
                    return JsonResponse({'success': False, 'error': 'Latitude must be between -90 and 90 degrees.'}, status=400)
                
                lon1, error = self._validate_number(data.get('lon1'), 'Longitude 1')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                if lon1 < -180 or lon1 > 180:
                    return JsonResponse({'success': False, 'error': 'Longitude must be between -180 and 180 degrees.'}, status=400)
                
                lat2, error = self._validate_number(data.get('lat2'), 'Latitude 2')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                if lat2 < -90 or lat2 > 90:
                    return JsonResponse({'success': False, 'error': 'Latitude must be between -90 and 90 degrees.'}, status=400)
                
                lon2, error = self._validate_number(data.get('lon2'), 'Longitude 2')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                if lon2 < -180 or lon2 > 180:
                    return JsonResponse({'success': False, 'error': 'Longitude must be between -180 and 180 degrees.'}, status=400)
                
                distance_km = self._calculate_geographic_distance(lat1, lon1, lat2, lon2)
                distance_miles = distance_km * 0.621371
                result_data = {
                    'lat1': lat1, 'lon1': lon1,
                    'lat2': lat2, 'lon2': lon2,
                    'distance_km': distance_km,
                    'distance_miles': distance_miles
                }
            
            elif distance_type == 'minkowski':
                point1_str = data.get('point1', '')
                point2_str = data.get('point2', '')
                p, error = self._validate_number(data.get('p'), 'p')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                if p <= 0:
                    return JsonResponse({'success': False, 'error': 'p must be greater than 0.'}, status=400)
                
                try:
                    if isinstance(point1_str, str):
                        point1 = [float(x.strip()) for x in point1_str.split(',')]
                    else:
                        point1 = point1_str
                    
                    if isinstance(point2_str, str):
                        point2 = [float(x.strip()) for x in point2_str.split(',')]
                    else:
                        point2 = point2_str
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid point format. Use comma-separated values.'}, status=400)
                
                distance, error = self._calculate_minkowski(point1, point2, p)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                result_data = {'point1': point1, 'point2': point2, 'p': p, 'distance': distance}
            else:
                return JsonResponse({'success': False, 'error': 'Invalid distance type.'}, status=400)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self.prepare_chart_data(distance_type, result_data)
            except Exception as chart_error:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Prepare display data
            display_data = self.prepare_display_data(distance_type, result_data)
            
            # Prepare step-by-step solution
            step_by_step = self.prepare_step_by_step(distance_type, result_data)
            step_by_step_html = self.prepare_step_by_step_html(step_by_step)
            
            # Prepare response
            response = {
                'success': True,
                'distance_type': distance_type,
                'result_data': result_data,
                'chart_data': chart_data,
                'display_data': display_data,
                'step_by_step': step_by_step,
                'step_by_step_html': step_by_step_html
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Distance Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
