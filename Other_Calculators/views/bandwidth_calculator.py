from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BandwidthCalculator(View):
    """
    Professional Bandwidth Calculator with Comprehensive Features
    
    This calculator provides bandwidth calculations with:
    - Data transfer time calculations
    - File size conversions
    - Bandwidth requirement analysis
    - Multiple unit conversions (bits, bytes, KB, MB, GB, TB)
    - Download/upload time estimates
    - Network speed analysis
    
    Features:
    - Supports multiple bandwidth units
    - Handles file size conversions
    - Calculates transfer times
    - Provides detailed breakdowns
    - Interactive visualizations
    """
    template_name = 'other_calculators/bandwidth_calculator.html'
    
    # Unit conversion factors (in bits)
    UNIT_FACTORS = {
        'bits': 1,
        'bytes': 8,
        'KB': 8 * 1024,
        'MB': 8 * 1024 * 1024,
        'GB': 8 * 1024 * 1024 * 1024,
        'TB': 8 * 1024 * 1024 * 1024 * 1024,
        'Kbps': 1000,
        'Mbps': 1000 * 1000,
        'Gbps': 1000 * 1000 * 1000,
        'Tbps': 1000 * 1000 * 1000 * 1000,
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Bandwidth Calculator'),
            'features': [
                _('Data transfer time calculations'),
                _('File size conversions'),
                _('Bandwidth requirement analysis'),
                _('Multiple unit conversions'),
                _('Download/upload time estimates'),
                _('Network speed analysis')
            ]
        }
        return render(request, self.template_name, context)
    
    # Protocol overhead percentages (approximate)
    PROTOCOL_OVERHEAD = {
        'tcp': 0.10,  # 10% overhead for TCP/IP
        'udp': 0.05,  # 5% overhead for UDP
        'http': 0.12,  # 12% overhead for HTTP
        'https': 0.15,  # 15% overhead for HTTPS
        'ftp': 0.08,  # 8% overhead for FTP
        'default': 0.10
    }
    
    # Common connection types with typical speeds
    CONNECTION_TYPES = {
        'dialup': {'speed': 56, 'unit': 'Kbps', 'name': _('Dial-up (56K)')},
        'isdn': {'speed': 128, 'unit': 'Kbps', 'name': _('ISDN (128K)')},
        'dsl': {'speed': 1.5, 'unit': 'Mbps', 'name': _('DSL (1.5 Mbps)')},
        'cable': {'speed': 25, 'unit': 'Mbps', 'name': _('Cable (25 Mbps)')},
        'fiber': {'speed': 100, 'unit': 'Mbps', 'name': _('Fiber (100 Mbps)')},
        '4g': {'speed': 50, 'unit': 'Mbps', 'name': _('4G Mobile (50 Mbps)')},
        '5g': {'speed': 200, 'unit': 'Mbps', 'name': _('5G Mobile (200 Mbps)')},
        'gigabit': {'speed': 1000, 'unit': 'Mbps', 'name': _('Gigabit (1 Gbps)')},
    }
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'transfer_time')
            
            if calc_type == 'transfer_time':
                return self._calculate_transfer_time(data)
            elif calc_type == 'bandwidth_required':
                return self._calculate_bandwidth_required(data)
            elif calc_type == 'file_size':
                return self._calculate_file_size(data)
            elif calc_type == 'real_world_speed':
                return self._calculate_real_world_speed(data)
            elif calc_type == 'batch_transfer':
                return self._calculate_batch_transfer(data)
            elif calc_type == 'connection_comparison':
                return self._calculate_connection_comparison(data)
            elif calc_type == 'cost_calculation':
                return self._calculate_cost(data)
            elif calc_type == 'bandwidth_recommendation':
                return self._get_bandwidth_recommendation(data)
            else:
                return JsonResponse({'success': False, 'error': _('Invalid calculation type.')}, status=400)
                
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: {error}').format(error=str(e))}, status=400)
        except Exception as e:
            import traceback
            print(f"Bandwidth Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
    
    def _calculate_transfer_time(self, data):
        """Calculate transfer time given file size and bandwidth"""
        file_size = float(data.get('file_size', 0))
        file_size_unit = data.get('file_size_unit', 'MB')
        bandwidth = float(data.get('bandwidth', 0))
        bandwidth_unit = data.get('bandwidth_unit', 'Mbps')
        
        if file_size <= 0 or bandwidth <= 0:
            return JsonResponse({'success': False, 'error': _('File size and bandwidth must be greater than zero.')}, status=400)
        
        # Convert to bits
        file_size_bits = file_size * self.UNIT_FACTORS.get(file_size_unit, 1)
        bandwidth_bits_per_sec = bandwidth * self.UNIT_FACTORS.get(bandwidth_unit, 1)
        
        # Calculate time in seconds
        time_seconds = file_size_bits / bandwidth_bits_per_sec
        
        # Convert to various time units
        time_breakdown = self._convert_time_units(time_seconds)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_transfer_time_steps(
            file_size, file_size_unit, bandwidth, bandwidth_unit,
            file_size_bits, bandwidth_bits_per_sec, time_seconds, time_breakdown
        )
        
        # Prepare chart data
        chart_data = self._prepare_transfer_time_chart_data(time_breakdown)
        
        result = {
            'success': True,
            'calc_type': 'transfer_time',
            'file_size': file_size,
            'file_size_unit': file_size_unit,
            'bandwidth': bandwidth,
            'bandwidth_unit': bandwidth_unit,
            'time_seconds': time_seconds,
            'time_breakdown': time_breakdown,
            'step_by_step': step_by_step,
            'chart_data': chart_data
        }
        
        return JsonResponse(result)
    
    def _calculate_bandwidth_required(self, data):
        """Calculate required bandwidth given file size and time"""
        file_size = float(data.get('file_size', 0))
        file_size_unit = data.get('file_size_unit', 'MB')
        time_value = float(data.get('time_value', 0))
        time_unit = data.get('time_unit', 'seconds')
        
        if file_size <= 0 or time_value <= 0:
            return JsonResponse({'success': False, 'error': _('File size and time must be greater than zero.')}, status=400)
        
        # Convert to bits and seconds
        file_size_bits = file_size * self.UNIT_FACTORS.get(file_size_unit, 1)
        time_seconds = self._convert_to_seconds(time_value, time_unit)
        
        if time_seconds <= 0:
            return JsonResponse({'success': False, 'error': _('Invalid time value.')}, status=400)
        
        # Calculate bandwidth in bits per second
        bandwidth_bps = file_size_bits / time_seconds
        
        # Convert to various bandwidth units
        bandwidth_breakdown = self._convert_bandwidth_units(bandwidth_bps)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_bandwidth_required_steps(
            file_size, file_size_unit, time_value, time_unit,
            file_size_bits, time_seconds, bandwidth_bps, bandwidth_breakdown
        )
        
        result = {
            'success': True,
            'calc_type': 'bandwidth_required',
            'file_size': file_size,
            'file_size_unit': file_size_unit,
            'time_value': time_value,
            'time_unit': time_unit,
            'bandwidth_bps': bandwidth_bps,
            'bandwidth_breakdown': bandwidth_breakdown,
            'step_by_step': step_by_step
        }
        
        return JsonResponse(result)
    
    def _calculate_file_size(self, data):
        """Calculate file size given bandwidth and time"""
        bandwidth = float(data.get('bandwidth', 0))
        bandwidth_unit = data.get('bandwidth_unit', 'Mbps')
        time_value = float(data.get('time_value', 0))
        time_unit = data.get('time_unit', 'seconds')
        
        if bandwidth <= 0 or time_value <= 0:
            return JsonResponse({'success': False, 'error': _('Bandwidth and time must be greater than zero.')}, status=400)
        
        # Convert to bits per second and seconds
        bandwidth_bps = bandwidth * self.UNIT_FACTORS.get(bandwidth_unit, 1)
        time_seconds = self._convert_to_seconds(time_value, time_unit)
        
        if time_seconds <= 0:
            return JsonResponse({'success': False, 'error': _('Invalid time value.')}, status=400)
        
        # Calculate file size in bits
        file_size_bits = bandwidth_bps * time_seconds
        
        # Convert to various file size units
        file_size_breakdown = self._convert_file_size_units(file_size_bits)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_file_size_steps(
            bandwidth, bandwidth_unit, time_value, time_unit,
            bandwidth_bps, time_seconds, file_size_bits, file_size_breakdown
        )
        
        result = {
            'success': True,
            'calc_type': 'file_size',
            'bandwidth': bandwidth,
            'bandwidth_unit': bandwidth_unit,
            'time_value': time_value,
            'time_unit': time_unit,
            'file_size_bits': file_size_bits,
            'file_size_breakdown': file_size_breakdown,
            'step_by_step': step_by_step
        }
        
        return JsonResponse(result)
    
    def _convert_time_units(self, seconds):
        """Convert seconds to various time units"""
        return {
            'seconds': seconds,
            'minutes': seconds / 60,
            'hours': seconds / 3600,
            'days': seconds / 86400,
            'weeks': seconds / 604800,
            'formatted': self._format_time(seconds)
        }
    
    def _format_time(self, seconds):
        """Format time in a human-readable way"""
        if seconds < 60:
            return _('{value:.2f} seconds').format(value=seconds)
        elif seconds < 3600:
            minutes = seconds / 60
            return _('{value:.2f} minutes').format(value=minutes)
        elif seconds < 86400:
            hours = seconds / 3600
            return _('{value:.2f} hours').format(value=hours)
        else:
            days = seconds / 86400
            return _('{value:.2f} days').format(value=days)
    
    def _convert_to_seconds(self, value, unit):
        """Convert time value to seconds"""
        conversions = {
            'seconds': 1,
            'minutes': 60,
            'hours': 3600,
            'days': 86400,
            'weeks': 604800
        }
        return value * conversions.get(unit, 1)
    
    def _convert_bandwidth_units(self, bps):
        """Convert bandwidth from bits per second to various units"""
        return {
            'bps': bps,
            'Kbps': bps / 1000,
            'Mbps': bps / (1000 * 1000),
            'Gbps': bps / (1000 * 1000 * 1000),
            'Tbps': bps / (1000 * 1000 * 1000 * 1000),
            'formatted': self._format_bandwidth(bps)
        }
    
    def _format_bandwidth(self, bps):
        """Format bandwidth in a human-readable way"""
        if bps < 1000:
            return _('{value:.2f} bps').format(value=bps)
        elif bps < 1000000:
            return _('{value:.2f} Kbps').format(value=bps / 1000)
        elif bps < 1000000000:
            return _('{value:.2f} Mbps').format(value=bps / 1000000)
        elif bps < 1000000000000:
            return _('{value:.2f} Gbps').format(value=bps / 1000000000)
        else:
            return _('{value:.2f} Tbps').format(value=bps / 1000000000000)
    
    def _convert_file_size_units(self, bits):
        """Convert file size from bits to various units"""
        return {
            'bits': bits,
            'bytes': bits / 8,
            'KB': bits / (8 * 1024),
            'MB': bits / (8 * 1024 * 1024),
            'GB': bits / (8 * 1024 * 1024 * 1024),
            'TB': bits / (8 * 1024 * 1024 * 1024 * 1024),
            'formatted': self._format_file_size(bits)
        }
    
    def _format_file_size(self, bits):
        """Format file size in a human-readable way"""
        bytes_val = bits / 8
        if bytes_val < 1024:
            return _('{value:.2f} bytes').format(value=bytes_val)
        elif bytes_val < 1024 * 1024:
            return _('{value:.2f} KB').format(value=bytes_val / 1024)
        elif bytes_val < 1024 * 1024 * 1024:
            return _('{value:.2f} MB').format(value=bytes_val / (1024 * 1024))
        elif bytes_val < 1024 * 1024 * 1024 * 1024:
            return _('{value:.2f} GB').format(value=bytes_val / (1024 * 1024 * 1024))
        else:
            return _('{value:.2f} TB').format(value=bytes_val / (1024 * 1024 * 1024 * 1024))
    
    def _prepare_transfer_time_steps(self, file_size, file_size_unit, bandwidth, bandwidth_unit,
                                     file_size_bits, bandwidth_bps, time_seconds, time_breakdown):
        """Prepare step-by-step solution for transfer time calculation"""
        steps = []
        steps.append(_("Step 1: Identify the Given Values"))
        steps.append(_("  File Size: {size} {unit}").format(size=file_size, unit=file_size_unit))
        steps.append(_("  Bandwidth: {bandwidth} {unit}").format(bandwidth=bandwidth, unit=bandwidth_unit))
        steps.append("")
        
        steps.append(_("Step 2: Convert to Common Units (Bits)"))
        steps.append(_("  File Size in Bits = {size} {unit} × {factor} = {bits:,} bits").format(
            size=file_size, unit=file_size_unit,
            factor=self.UNIT_FACTORS.get(file_size_unit, 1),
            bits=int(file_size_bits)
        ))
        steps.append(_("  Bandwidth in bps = {bandwidth} {unit} × {factor} = {bps:,} bps").format(
            bandwidth=bandwidth, unit=bandwidth_unit,
            factor=self.UNIT_FACTORS.get(bandwidth_unit, 1),
            bps=int(bandwidth_bps)
        ))
        steps.append("")
        
        steps.append(_("Step 3: Calculate Transfer Time"))
        steps.append(_("  Time = File Size ÷ Bandwidth"))
        steps.append(_("  Time = {bits:,} bits ÷ {bps:,} bps = {seconds:.2f} seconds").format(
            bits=int(file_size_bits), bps=int(bandwidth_bps), seconds=time_seconds
        ))
        steps.append("")
        
        steps.append(_("Step 4: Convert to Various Time Units"))
        steps.append(_("  Seconds: {seconds:.2f}").format(seconds=time_breakdown['seconds']))
        steps.append(_("  Minutes: {minutes:.2f}").format(minutes=time_breakdown['minutes']))
        steps.append(_("  Hours: {hours:.2f}").format(hours=time_breakdown['hours']))
        steps.append(_("  Days: {days:.2f}").format(days=time_breakdown['days']))
        steps.append("")
        
        steps.append(_("Step 5: Final Result"))
        steps.append(_("  Transfer Time: {formatted}").format(formatted=time_breakdown['formatted']))
        
        return [str(step) for step in steps]
    
    def _prepare_bandwidth_required_steps(self, file_size, file_size_unit, time_value, time_unit,
                                          file_size_bits, time_seconds, bandwidth_bps, bandwidth_breakdown):
        """Prepare step-by-step solution for bandwidth required calculation"""
        steps = []
        steps.append(_("Step 1: Identify the Given Values"))
        steps.append(_("  File Size: {size} {unit}").format(size=file_size, unit=file_size_unit))
        steps.append(_("  Time: {time} {unit}").format(time=time_value, unit=time_unit))
        steps.append("")
        
        steps.append(_("Step 2: Convert to Common Units"))
        steps.append(_("  File Size in Bits = {size} {unit} × {factor} = {bits:,} bits").format(
            size=file_size, unit=file_size_unit,
            factor=self.UNIT_FACTORS.get(file_size_unit, 1),
            bits=int(file_size_bits)
        ))
        steps.append(_("  Time in Seconds = {time} {unit} × {factor} = {seconds:.2f} seconds").format(
            time=time_value, unit=time_unit,
            factor=self._convert_to_seconds(1, time_unit),
            seconds=time_seconds
        ))
        steps.append("")
        
        steps.append(_("Step 3: Calculate Required Bandwidth"))
        steps.append(_("  Bandwidth = File Size ÷ Time"))
        steps.append(_("  Bandwidth = {bits:,} bits ÷ {seconds:.2f} seconds = {bps:.2f} bps").format(
            bits=int(file_size_bits), seconds=time_seconds, bps=bandwidth_bps
        ))
        steps.append("")
        
        steps.append(_("Step 4: Convert to Various Bandwidth Units"))
        steps.append(_("  bps: {bps:.2f}").format(bps=bandwidth_breakdown['bps']))
        steps.append(_("  Kbps: {kbps:.2f}").format(kbps=bandwidth_breakdown['Kbps']))
        steps.append(_("  Mbps: {mbps:.2f}").format(mbps=bandwidth_breakdown['Mbps']))
        steps.append(_("  Gbps: {gbps:.2f}").format(gbps=bandwidth_breakdown['Gbps']))
        steps.append("")
        
        steps.append(_("Step 5: Final Result"))
        steps.append(_("  Required Bandwidth: {formatted}").format(formatted=bandwidth_breakdown['formatted']))
        
        return [str(step) for step in steps]
    
    def _prepare_file_size_steps(self, bandwidth, bandwidth_unit, time_value, time_unit,
                                bandwidth_bps, time_seconds, file_size_bits, file_size_breakdown):
        """Prepare step-by-step solution for file size calculation"""
        steps = []
        steps.append(_("Step 1: Identify the Given Values"))
        steps.append(_("  Bandwidth: {bandwidth} {unit}").format(bandwidth=bandwidth, unit=bandwidth_unit))
        steps.append(_("  Time: {time} {unit}").format(time=time_value, unit=time_unit))
        steps.append("")
        
        steps.append(_("Step 2: Convert to Common Units"))
        steps.append(_("  Bandwidth in bps = {bandwidth} {unit} × {factor} = {bps:,} bps").format(
            bandwidth=bandwidth, unit=bandwidth_unit,
            factor=self.UNIT_FACTORS.get(bandwidth_unit, 1),
            bps=int(bandwidth_bps)
        ))
        steps.append(_("  Time in Seconds = {time} {unit} × {factor} = {seconds:.2f} seconds").format(
            time=time_value, unit=time_unit,
            factor=self._convert_to_seconds(1, time_unit),
            seconds=time_seconds
        ))
        steps.append("")
        
        steps.append(_("Step 3: Calculate File Size"))
        steps.append(_("  File Size = Bandwidth × Time"))
        steps.append(_("  File Size = {bps:,} bps × {seconds:.2f} seconds = {bits:,} bits").format(
            bps=int(bandwidth_bps), seconds=time_seconds, bits=int(file_size_bits)
        ))
        steps.append("")
        
        steps.append(_("Step 4: Convert to Various File Size Units"))
        steps.append(_("  Bits: {bits:.2f}").format(bits=file_size_breakdown['bits']))
        steps.append(_("  Bytes: {bytes:.2f}").format(bytes=file_size_breakdown['bytes']))
        steps.append(_("  KB: {kb:.2f}").format(kb=file_size_breakdown['KB']))
        steps.append(_("  MB: {mb:.2f}").format(mb=file_size_breakdown['MB']))
        steps.append(_("  GB: {gb:.2f}").format(gb=file_size_breakdown['GB']))
        steps.append("")
        
        steps.append(_("Step 5: Final Result"))
        steps.append(_("  File Size: {formatted}").format(formatted=file_size_breakdown['formatted']))
        
        return [str(step) for step in steps]
    
    def _prepare_transfer_time_chart_data(self, time_breakdown):
        """Prepare chart data for transfer time visualization"""
        chart_data = {}
        
        try:
            chart_data['time_units_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Seconds')), str(_('Minutes')), str(_('Hours')), str(_('Days'))],
                    'datasets': [{
                        'label': str(_('Time Units')),
                        'data': [
                            time_breakdown['seconds'],
                            time_breakdown['minutes'],
                            time_breakdown['hours'],
                            time_breakdown['days']
                        ],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)',
                            'rgba(245, 158, 11, 0.6)',
                            'rgba(239, 68, 68, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b',
                            '#ef4444'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'scales': {
                        'y': {
                            'beginAtZero': True
                        }
                    }
                }
            }
        except Exception as e:
            import traceback
            print(f"Chart data preparation error: {traceback.format_exc()}")
            chart_data = {}
        
        return chart_data
    
    def _calculate_real_world_speed(self, data):
        """Calculate real-world transfer speed accounting for protocol overhead"""
        file_size = float(data.get('file_size', 0))
        file_size_unit = data.get('file_size_unit', 'MB')
        bandwidth = float(data.get('bandwidth', 0))
        bandwidth_unit = data.get('bandwidth_unit', 'Mbps')
        protocol = data.get('protocol', 'default')
        
        if file_size <= 0 or bandwidth <= 0:
            return JsonResponse({'success': False, 'error': _('File size and bandwidth must be greater than zero.')}, status=400)
        
        # Get protocol overhead
        overhead_percent = self.PROTOCOL_OVERHEAD.get(protocol, self.PROTOCOL_OVERHEAD['default'])
        
        # Convert to bits
        file_size_bits = file_size * self.UNIT_FACTORS.get(file_size_unit, 1)
        bandwidth_bits_per_sec = bandwidth * self.UNIT_FACTORS.get(bandwidth_unit, 1)
        
        # Calculate theoretical time
        theoretical_time = file_size_bits / bandwidth_bits_per_sec
        
        # Calculate effective bandwidth (accounting for overhead)
        effective_bandwidth = bandwidth_bits_per_sec * (1 - overhead_percent)
        real_world_time = file_size_bits / effective_bandwidth
        
        # Calculate difference
        time_difference = real_world_time - theoretical_time
        efficiency = (theoretical_time / real_world_time) * 100
        
        result = {
            'success': True,
            'calc_type': 'real_world_speed',
            'theoretical_time': self._convert_time_units(theoretical_time),
            'real_world_time': self._convert_time_units(real_world_time),
            'time_difference': self._convert_time_units(time_difference),
            'efficiency': round(efficiency, 2),
            'overhead_percent': round(overhead_percent * 100, 2),
            'protocol': protocol,
            'effective_bandwidth': self._convert_bandwidth_units(effective_bandwidth)
        }
        
        return JsonResponse(result)
    
    def _calculate_batch_transfer(self, data):
        """Calculate transfer time for multiple files"""
        files = data.get('files', [])
        bandwidth = float(data.get('bandwidth', 0))
        bandwidth_unit = data.get('bandwidth_unit', 'Mbps')
        transfer_type = data.get('transfer_type', 'sequential')  # sequential or parallel
        
        if not files or len(files) == 0:
            return JsonResponse({'success': False, 'error': _('Please provide at least one file.')}, status=400)
        
        if bandwidth <= 0:
            return JsonResponse({'success': False, 'error': _('Bandwidth must be greater than zero.')}, status=400)
        
        bandwidth_bps = bandwidth * self.UNIT_FACTORS.get(bandwidth_unit, 1)
        
        total_size_bits = 0
        file_results = []
        
        for file_data in files:
            file_size = float(file_data.get('size', 0))
            file_size_unit = file_data.get('unit', 'MB')
            file_name = file_data.get('name', _('File'))
            
            file_size_bits = file_size * self.UNIT_FACTORS.get(file_size_unit, 1)
            file_time = file_size_bits / bandwidth_bps
            
            file_results.append({
                'name': file_name,
                'size': file_size,
                'unit': file_size_unit,
                'time': self._convert_time_units(file_time)
            })
            
            if transfer_type == 'sequential':
                total_size_bits += file_size_bits
            else:  # parallel
                total_size_bits = max(total_size_bits, file_size_bits)
        
        if transfer_type == 'sequential':
            total_time = total_size_bits / bandwidth_bps
        else:
            total_time = total_size_bits / bandwidth_bps
        
        result = {
            'success': True,
            'calc_type': 'batch_transfer',
            'transfer_type': transfer_type,
            'total_time': self._convert_time_units(total_time),
            'files': file_results,
            'total_files': len(files)
        }
        
        return JsonResponse(result)
    
    def _calculate_connection_comparison(self, data):
        """Compare transfer times across different connection types"""
        file_size = float(data.get('file_size', 0))
        file_size_unit = data.get('file_size_unit', 'MB')
        connection_types = data.get('connection_types', list(self.CONNECTION_TYPES.keys()))
        
        if file_size <= 0:
            return JsonResponse({'success': False, 'error': _('File size must be greater than zero.')}, status=400)
        
        file_size_bits = file_size * self.UNIT_FACTORS.get(file_size_unit, 1)
        comparisons = []
        
        for conn_type in connection_types:
            if conn_type in self.CONNECTION_TYPES:
                conn_info = self.CONNECTION_TYPES[conn_type]
                speed = conn_info['speed']
                unit = conn_info['unit']
                name = conn_info['name']
                
                bandwidth_bps = speed * self.UNIT_FACTORS.get(unit, 1)
                transfer_time = file_size_bits / bandwidth_bps
                
                comparisons.append({
                    'type': conn_type,
                    'name': str(name),
                    'speed': speed,
                    'unit': unit,
                    'transfer_time': self._convert_time_units(transfer_time)
                })
        
        # Sort by transfer time
        comparisons.sort(key=lambda x: x['transfer_time']['seconds'])
        
        result = {
            'success': True,
            'calc_type': 'connection_comparison',
            'file_size': file_size,
            'file_size_unit': file_size_unit,
            'comparisons': comparisons
        }
        
        return JsonResponse(result)
    
    def _calculate_cost(self, data):
        """Calculate data transfer costs"""
        file_size = float(data.get('file_size', 0))
        file_size_unit = data.get('file_size_unit', 'GB')
        cost_per_gb = float(data.get('cost_per_gb', 0))
        bandwidth = float(data.get('bandwidth', 0))
        bandwidth_unit = data.get('bandwidth_unit', 'Mbps')
        
        if file_size <= 0:
            return JsonResponse({'success': False, 'error': _('File size must be greater than zero.')}, status=400)
        
        # Convert file size to GB
        file_size_bits = file_size * self.UNIT_FACTORS.get(file_size_unit, 1)
        file_size_gb = file_size_bits / (8 * 1024 * 1024 * 1024)
        
        # Calculate cost
        total_cost = file_size_gb * cost_per_gb
        
        # Calculate transfer time if bandwidth provided
        transfer_time = None
        if bandwidth > 0:
            bandwidth_bps = bandwidth * self.UNIT_FACTORS.get(bandwidth_unit, 1)
            time_seconds = file_size_bits / bandwidth_bps
            transfer_time = self._convert_time_units(time_seconds)
        
        result = {
            'success': True,
            'calc_type': 'cost_calculation',
            'file_size_gb': round(file_size_gb, 4),
            'cost_per_gb': cost_per_gb,
            'total_cost': round(total_cost, 2),
            'transfer_time': transfer_time
        }
        
        return JsonResponse(result)
    
    def _get_bandwidth_recommendation(self, data):
        """Get bandwidth recommendations based on use case"""
        use_case = data.get('use_case', 'general')
        num_users = int(data.get('num_users', 1))
        concurrent_streams = int(data.get('concurrent_streams', 1))
        
        # Bandwidth requirements per use case (in Mbps per user/stream)
        requirements = {
            'web_browsing': 1,
            'email': 0.5,
            'video_call': 2,
            'hd_streaming': 5,
            '4k_streaming': 25,
            'gaming': 3,
            'file_sharing': 10,
            'video_conferencing': 4,
            'general': 5
        }
        
        base_requirement = requirements.get(use_case, requirements['general'])
        
        # Calculate total requirement
        if use_case in ['hd_streaming', '4k_streaming']:
            total_bandwidth = base_requirement * concurrent_streams
        else:
            total_bandwidth = base_requirement * num_users
        
        # Add 20% buffer for network overhead
        recommended_bandwidth = total_bandwidth * 1.2
        
        # Get connection recommendations
        suitable_connections = []
        for conn_type, conn_info in self.CONNECTION_TYPES.items():
            speed = conn_info['speed']
            if speed >= recommended_bandwidth:
                suitable_connections.append({
                    'type': conn_type,
                    'name': str(conn_info['name']),
                    'speed': speed,
                    'unit': conn_info['unit']
                })
        
        result = {
            'success': True,
            'calc_type': 'bandwidth_recommendation',
            'use_case': use_case,
            'num_users': num_users,
            'concurrent_streams': concurrent_streams,
            'base_requirement': round(base_requirement, 2),
            'recommended_bandwidth': round(recommended_bandwidth, 2),
            'suitable_connections': suitable_connections
        }
        
        return JsonResponse(result)
