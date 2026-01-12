from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
import ipaddress
from sympy import symbols, Eq, simplify, latex


@method_decorator(ensure_csrf_cookie, name='dispatch')
class IpSubnetCalculator(View):
    """
    Professional IP Subnet Calculator with Comprehensive Features
    
    This calculator provides IP subnet calculations with:
    - Calculate subnet information from IP and subnet mask/CIDR
    - Calculate network address, broadcast address, host range
    - Calculate number of hosts and usable hosts
    - Convert between subnet mask formats
    - Calculate subnet from IP and number of hosts
    - Calculate subnet from IP and number of subnets
    
    Features:
    - Supports IPv4 addresses
    - Handles CIDR notation and subnet masks
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/ip_subnet_calculator.html'
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        return unit
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('IP Subnet Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'subnet_info')
            
            if calc_type == 'subnet_info':
                return self._calculate_subnet_info(data)
            elif calc_type == 'subnet_from_hosts':
                return self._calculate_subnet_from_hosts(data)
            elif calc_type == 'subnet_from_subnets':
                return self._calculate_subnet_from_subnets(data)
            elif calc_type == 'convert_mask':
                return self._convert_subnet_mask(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation type.')
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid JSON data.')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _parse_ip_address(self, ip_str):
        """Parse and validate IP address"""
        try:
            ip = ipaddress.IPv4Address(ip_str.strip())
            return ip
        except (ValueError, ipaddress.AddressValueError) as e:
            raise ValueError(_('Invalid IP address: {ip}').format(ip=ip_str))
    
    def _parse_subnet_mask(self, mask_str):
        """Parse subnet mask (CIDR or dotted decimal)"""
        try:
            # Try CIDR notation first
            if '/' in mask_str:
                cidr = int(mask_str.split('/')[1])
                if cidr < 0 or cidr > 32:
                    raise ValueError(_('CIDR must be between 0 and 32.'))
                return cidr
            else:
                # Try dotted decimal
                try:
                    mask_ip = ipaddress.IPv4Address(mask_str.strip())
                    # Convert to CIDR
                    mask_int = int(mask_ip)
                    # Count leading 1s
                    cidr = bin(mask_int).count('1')
                    # Validate it's a valid subnet mask
                    if not self._is_valid_subnet_mask(mask_int):
                        raise ValueError(_('Invalid subnet mask.'))
                    return cidr
                except (ValueError, ipaddress.AddressValueError):
                    # Try as CIDR number
                    cidr = int(mask_str)
                    if cidr < 0 or cidr > 32:
                        raise ValueError(_('CIDR must be between 0 and 32.'))
                    return cidr
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(_('Invalid subnet mask format.'))
    
    def _is_valid_subnet_mask(self, mask_int):
        """Check if integer represents a valid subnet mask"""
        # Valid subnet masks are sequences of 1s followed by 0s
        mask_bin = format(mask_int, '032b')
        found_zero = False
        for bit in mask_bin:
            if bit == '0':
                found_zero = True
            elif bit == '1' and found_zero:
                return False
        return True
    
    def _cidr_to_mask(self, cidr):
        """Convert CIDR to dotted decimal subnet mask"""
        mask_int = (0xffffffff >> (32 - cidr)) << (32 - cidr)
        return str(ipaddress.IPv4Address(mask_int))
    
    def _calculate_subnet_info(self, data):
        """Calculate subnet information from IP and subnet mask"""
        try:
            if 'ip_address' not in data or not data.get('ip_address'):
                return JsonResponse({
                    'success': False,
                    'error': _('IP address is required.')
                }, status=400)
            
            if 'subnet_mask' not in data or not data.get('subnet_mask'):
                return JsonResponse({
                    'success': False,
                    'error': _('Subnet mask or CIDR is required.')
                }, status=400)
            
            ip_str = data.get('ip_address', '').strip()
            mask_str = data.get('subnet_mask', '').strip()
            
            try:
                ip = self._parse_ip_address(ip_str)
                cidr = self._parse_subnet_mask(mask_str)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            # Create network object
            network_str = f"{ip}/{cidr}"
            try:
                network = ipaddress.IPv4Network(network_str, strict=False)
            except (ValueError, ipaddress.NetmaskValueError) as e:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid network configuration: {error}').format(error=str(e))
                }, status=400)
            
            # Calculate subnet information
            network_address = str(network.network_address)
            broadcast_address = str(network.broadcast_address)
            subnet_mask = self._cidr_to_mask(cidr)
            wildcard_mask = str(ipaddress.IPv4Address(int(network.hostmask)))
            
            # Calculate host information
            total_hosts = network.num_addresses
            usable_hosts = max(0, total_hosts - 2)  # Subtract network and broadcast
            
            # First and last usable host
            if total_hosts > 2:
                first_host = str(network.network_address + 1)
                last_host = str(network.broadcast_address - 1)
            else:
                first_host = None
                last_host = None
            
            # IP class
            ip_class = self._get_ip_class(ip)
            
            # Network type
            if network.is_private:
                network_type = _('Private')
            elif network.is_loopback:
                network_type = _('Loopback')
            elif network.is_link_local:
                network_type = _('Link Local')
            elif network.is_multicast:
                network_type = _('Multicast')
            elif network.is_reserved:
                network_type = _('Reserved')
            else:
                network_type = _('Public')
            
            steps = self._prepare_subnet_info_steps(ip_str, mask_str, cidr, network_address, broadcast_address, subnet_mask, total_hosts, usable_hosts, first_host, last_host)
            
            chart_data = self._prepare_subnet_info_chart_data(total_hosts, usable_hosts)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'subnet_info',
                'ip_address': ip_str,
                'subnet_mask': mask_str,
                'cidr': cidr,
                'network_address': network_address,
                'broadcast_address': broadcast_address,
                'subnet_mask_decimal': subnet_mask,
                'wildcard_mask': wildcard_mask,
                'total_hosts': total_hosts,
                'usable_hosts': usable_hosts,
                'first_host': first_host,
                'last_host': last_host,
                'ip_class': ip_class,
                'network_type': network_type,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating subnet info: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_subnet_from_hosts(self, data):
        """Calculate subnet from IP and number of hosts needed"""
        try:
            if 'ip_address' not in data or not data.get('ip_address'):
                return JsonResponse({
                    'success': False,
                    'error': _('IP address is required.')
                }, status=400)
            
            if 'hosts_needed' not in data or data.get('hosts_needed') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Number of hosts needed is required.')
                }, status=400)
            
            ip_str = data.get('ip_address', '').strip()
            
            try:
                hosts_needed = int(data.get('hosts_needed', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid number of hosts. Please enter an integer.')
                }, status=400)
            
            if hosts_needed < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Number of hosts must be non-negative.')
                }, status=400)
            
            if hosts_needed > 16777214:  # 2^24 - 2
                return JsonResponse({
                    'success': False,
                    'error': _('Number of hosts exceeds maximum (16,777,214).')
                }, status=400)
            
            try:
                ip = self._parse_ip_address(ip_str)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            # Calculate required CIDR
            # We need: 2^(32-cidr) - 2 >= hosts_needed
            # So: 32 - cidr >= log2(hosts_needed + 2)
            # So: cidr <= 32 - log2(hosts_needed + 2)
            
            if hosts_needed == 0:
                required_hosts = 2  # At least network and broadcast
            else:
                required_hosts = hosts_needed + 2  # Add network and broadcast
            
            # Calculate minimum CIDR
            cidr = int(32 - math.ceil(math.log2(required_hosts)))
            
            if cidr < 0 or cidr > 30:
                return JsonResponse({
                    'success': False,
                    'error': _('Cannot create subnet for this number of hosts.')
                }, status=400)
            
            # Create network
            network_str = f"{ip}/{cidr}"
            try:
                network = ipaddress.IPv4Network(network_str, strict=False)
            except (ValueError, ipaddress.NetmaskValueError) as e:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid network configuration: {error}').format(error=str(e))
                }, status=400)
            
            subnet_mask = self._cidr_to_mask(cidr)
            total_hosts = network.num_addresses
            usable_hosts = max(0, total_hosts - 2)
            
            steps = self._prepare_subnet_from_hosts_steps(ip_str, hosts_needed, required_hosts, cidr, subnet_mask, total_hosts, usable_hosts)
            
            chart_data = self._prepare_subnet_from_hosts_chart_data(total_hosts, usable_hosts, hosts_needed)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'subnet_from_hosts',
                'ip_address': ip_str,
                'hosts_needed': hosts_needed,
                'cidr': cidr,
                'subnet_mask': subnet_mask,
                'total_hosts': total_hosts,
                'usable_hosts': usable_hosts,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating subnet from hosts: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_subnet_from_subnets(self, data):
        """Calculate subnet from IP and number of subnets needed"""
        try:
            if 'ip_address' not in data or not data.get('ip_address'):
                return JsonResponse({
                    'success': False,
                    'error': _('IP address is required.')
                }, status=400)
            
            if 'subnets_needed' not in data or data.get('subnets_needed') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Number of subnets needed is required.')
                }, status=400)
            
            if 'original_cidr' not in data or data.get('original_cidr') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Original CIDR is required.')
                }, status=400)
            
            ip_str = data.get('ip_address', '').strip()
            
            try:
                subnets_needed = int(data.get('subnets_needed', 0))
                original_cidr = int(data.get('original_cidr', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input. Please enter integers.')
                }, status=400)
            
            if subnets_needed < 1:
                return JsonResponse({
                    'success': False,
                    'error': _('Number of subnets must be at least 1.')
                }, status=400)
            
            if original_cidr < 0 or original_cidr > 32:
                return JsonResponse({
                    'success': False,
                    'error': _('Original CIDR must be between 0 and 32.')
                }, status=400)
            
            try:
                ip = self._parse_ip_address(ip_str)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            # Calculate required CIDR for subnets
            # We need: 2^(new_cidr - original_cidr) >= subnets_needed
            # So: new_cidr - original_cidr >= log2(subnets_needed)
            # So: new_cidr >= original_cidr + log2(subnets_needed)
            
            new_cidr = int(original_cidr + math.ceil(math.log2(subnets_needed)))
            
            if new_cidr > 32:
                return JsonResponse({
                    'success': False,
                    'error': _('Cannot create this many subnets from the original network.')
                }, status=400)
            
            # Create network
            network_str = f"{ip}/{new_cidr}"
            try:
                network = ipaddress.IPv4Network(network_str, strict=False)
            except (ValueError, ipaddress.NetmaskValueError) as e:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid network configuration: {error}').format(error=str(e))
                }, status=400)
            
            subnet_mask = self._cidr_to_mask(new_cidr)
            total_hosts = network.num_addresses
            usable_hosts = max(0, total_hosts - 2)
            actual_subnets = 2 ** (new_cidr - original_cidr)
            
            steps = self._prepare_subnet_from_subnets_steps(ip_str, subnets_needed, original_cidr, new_cidr, subnet_mask, total_hosts, usable_hosts, actual_subnets)
            
            chart_data = self._prepare_subnet_from_subnets_chart_data(original_cidr, new_cidr, actual_subnets)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'subnet_from_subnets',
                'ip_address': ip_str,
                'subnets_needed': subnets_needed,
                'original_cidr': original_cidr,
                'new_cidr': new_cidr,
                'subnet_mask': subnet_mask,
                'total_hosts': total_hosts,
                'usable_hosts': usable_hosts,
                'actual_subnets': actual_subnets,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating subnet from subnets: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_subnet_mask(self, data):
        """Convert between subnet mask formats"""
        try:
            if 'value' not in data or not data.get('value'):
                return JsonResponse({
                    'success': False,
                    'error': _('Subnet mask value is required.')
                }, status=400)
            
            value_str = data.get('value', '').strip()
            from_format = data.get('from_format', 'cidr')
            to_format = data.get('to_format', 'decimal')
            
            try:
                if from_format == 'cidr':
                    cidr = int(value_str)
                    if cidr < 0 or cidr > 32:
                        return JsonResponse({
                            'success': False,
                            'error': _('CIDR must be between 0 and 32.')
                        }, status=400)
                    subnet_mask = self._cidr_to_mask(cidr)
                elif from_format == 'decimal':
                    mask_ip = ipaddress.IPv4Address(value_str)
                    mask_int = int(mask_ip)
                    if not self._is_valid_subnet_mask(mask_int):
                        return JsonResponse({
                            'success': False,
                            'error': _('Invalid subnet mask.')
                        }, status=400)
                    # Count leading 1s
                    cidr = bin(mask_int).count('1')
                    subnet_mask = value_str
                else:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid from format.')
                    }, status=400)
            except (ValueError, ipaddress.AddressValueError) as e:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid subnet mask value: {error}').format(error=str(e))
                }, status=400)
            
            # Convert to target format
            if to_format == 'cidr':
                result = cidr
            elif to_format == 'decimal':
                result = subnet_mask
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid to format.')
                }, status=400)
            
            steps = self._prepare_convert_mask_steps(value_str, from_format, to_format, cidr, subnet_mask, result)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert_mask',
                'value': value_str,
                'from_format': from_format,
                'to_format': to_format,
                'cidr': cidr,
                'subnet_mask': subnet_mask,
                'result': str(result),
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error converting subnet mask: {error}').format(error=str(e))
            }, status=500)
    
    def _get_ip_class(self, ip):
        """Get IP address class"""
        first_octet = int(ip) >> 24
        if first_octet < 128:
            return 'A'
        elif first_octet < 192:
            return 'B'
        elif first_octet < 224:
            return 'C'
        elif first_octet < 240:
            return 'D'
        else:
            return 'E'
    
    # Step-by-step solution preparation methods
    def _prepare_subnet_info_steps(self, ip_str, mask_str, cidr, network_address, broadcast_address, subnet_mask, total_hosts, usable_hosts, first_host, last_host):
        """Prepare step-by-step solution for subnet info calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('IP Address: {ip}').format(ip=ip_str))
        steps.append(_('Subnet Mask/CIDR: {mask}').format(mask=mask_str))
        steps.append(_('CIDR Notation: /{cidr}').format(cidr=cidr))
        steps.append('')
        steps.append(_('Step 2: Calculate subnet mask'))
        steps.append(_('Subnet Mask: {mask}').format(mask=subnet_mask))
        steps.append(_('CIDR: /{cidr} (means {cidr} bits for network)').format(cidr=cidr))
        steps.append('')
        steps.append(_('Step 3: Calculate network address'))
        steps.append(_('Network Address = IP Address AND Subnet Mask'))
        steps.append(_('Network Address: {net}').format(net=network_address))
        steps.append('')
        steps.append(_('Step 4: Calculate broadcast address'))
        steps.append(_('Broadcast Address: {broadcast}').format(broadcast=broadcast_address))
        steps.append('')
        steps.append(_('Step 5: Calculate host information'))
        steps.append(_('Total Hosts = 2^(32 - {cidr}) = {total}').format(cidr=cidr, total=total_hosts))
        steps.append(_('Usable Hosts = Total Hosts - 2 = {usable}').format(usable=usable_hosts))
        if first_host and last_host:
            steps.append(_('First Usable Host: {first}').format(first=first_host))
            steps.append(_('Last Usable Host: {last}').format(last=last_host))
        return steps
    
    def _prepare_subnet_from_hosts_steps(self, ip_str, hosts_needed, required_hosts, cidr, subnet_mask, total_hosts, usable_hosts):
        """Prepare step-by-step solution for subnet from hosts calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('IP Address: {ip}').format(ip=ip_str))
        steps.append(_('Hosts Needed: {hosts}').format(hosts=hosts_needed))
        steps.append('')
        steps.append(_('Step 2: Calculate required total hosts'))
        steps.append(_('Required Hosts = Hosts Needed + 2 (network + broadcast)'))
        steps.append(_('Required Hosts = {needed} + 2 = {required}').format(needed=hosts_needed, required=required_hosts))
        steps.append('')
        steps.append(_('Step 3: Calculate minimum CIDR'))
        steps.append(_('We need: 2^(32 - CIDR) >= {required}').format(required=required_hosts))
        steps.append(_('CIDR = 32 - log2({required}) = {cidr}').format(required=required_hosts, cidr=cidr))
        steps.append('')
        steps.append(_('Step 4: Calculate subnet information'))
        steps.append(_('Subnet Mask: {mask}').format(mask=subnet_mask))
        steps.append(_('Total Hosts: {total}').format(total=total_hosts))
        steps.append(_('Usable Hosts: {usable}').format(usable=usable_hosts))
        return steps
    
    def _prepare_subnet_from_subnets_steps(self, ip_str, subnets_needed, original_cidr, new_cidr, subnet_mask, total_hosts, usable_hosts, actual_subnets):
        """Prepare step-by-step solution for subnet from subnets calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('IP Address: {ip}').format(ip=ip_str))
        steps.append(_('Subnets Needed: {subnets}').format(subnets=subnets_needed))
        steps.append(_('Original CIDR: /{cidr}').format(cidr=original_cidr))
        steps.append('')
        steps.append(_('Step 2: Calculate required CIDR'))
        steps.append(_('We need: 2^(New CIDR - Original CIDR) >= {needed}').format(needed=subnets_needed))
        steps.append(_('New CIDR = Original CIDR + log2({needed})').format(needed=subnets_needed))
        steps.append(_('New CIDR = {orig} + {log} = {new}').format(orig=original_cidr, log=int(math.ceil(math.log2(subnets_needed))), new=new_cidr))
        steps.append('')
        steps.append(_('Step 3: Calculate subnet information'))
        steps.append(_('Subnet Mask: {mask}').format(mask=subnet_mask))
        steps.append(_('Actual Subnets Created: {actual}').format(actual=actual_subnets))
        steps.append(_('Hosts per Subnet: {hosts}').format(hosts=total_hosts))
        steps.append(_('Usable Hosts per Subnet: {usable}').format(usable=usable_hosts))
        return steps
    
    def _prepare_convert_mask_steps(self, value_str, from_format, to_format, cidr, subnet_mask, result):
        """Prepare step-by-step solution for subnet mask conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Subnet Mask: {value} ({format})').format(value=value_str, format=from_format))
        steps.append('')
        if from_format == 'decimal':
            steps.append(_('Step 2: Convert to CIDR'))
            steps.append(_('Count the number of leading 1s in the binary representation'))
            steps.append(_('CIDR: /{cidr}').format(cidr=cidr))
            steps.append('')
        if to_format == 'decimal':
            steps.append(_('Step 3: Convert CIDR to dotted decimal'))
            steps.append(_('Subnet Mask: {mask}').format(mask=subnet_mask))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('CIDR: /{result}').format(result=result))
        return steps
    
    # Chart data preparation methods
    def _prepare_subnet_info_chart_data(self, total_hosts, usable_hosts):
        """Prepare chart data for subnet info calculation"""
        try:
            chart_config = {
                'type': 'doughnut',
                'data': {
                    'labels': [_('Usable Hosts'), _('Reserved (Network + Broadcast)')],
                    'datasets': [{
                        'data': [usable_hosts, total_hosts - usable_hosts],
                        'backgroundColor': [
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(156, 163, 175, 0.8)'
                        ],
                        'borderColor': [
                            '#10b981',
                            '#9ca3af'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': True,
                            'position': 'bottom'
                        },
                        'title': {
                            'display': True,
                            'text': _('Host Distribution')
                        }
                    }
                }
            }
            return {'subnet_info_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_subnet_from_hosts_chart_data(self, total_hosts, usable_hosts, hosts_needed):
        """Prepare chart data for subnet from hosts calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Total Hosts'), _('Usable Hosts'), _('Hosts Needed')],
                    'datasets': [{
                        'label': _('Hosts'),
                        'data': [total_hosts, usable_hosts, hosts_needed],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Subnet from Hosts')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Hosts')
                            }
                        }
                    }
                }
            }
            return {'subnet_from_hosts_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_subnet_from_subnets_chart_data(self, original_cidr, new_cidr, actual_subnets):
        """Prepare chart data for subnet from subnets calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Original CIDR'), _('New CIDR'), _('Subnets Created')],
                    'datasets': [{
                        'label': _('Value'),
                        'data': [original_cidr, new_cidr, actual_subnets],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Subnet from Subnets')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value')
                            }
                        }
                    }
                }
            }
            return {'subnet_from_subnets_chart': chart_config}
        except Exception as e:
            return None
