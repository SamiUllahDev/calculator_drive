from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import ipaddress


@method_decorator(ensure_csrf_cookie, name='dispatch')
class IpSubnetCalculator(View):
    """
    IP Subnet Calculator — 5 calculation types.

    Calculation types
        • subnet_info        → full subnet info from IP + mask/CIDR
        • subnet_from_hosts  → find optimal CIDR for N hosts needed
        • subnet_from_subnets→ divide a network into N subnets
        • supernet           → aggregate/summarise multiple subnets
        • convert_mask       → convert between CIDR and dotted-decimal
    """
    template_name = 'other_calculators/ip_subnet_calculator.html'

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('IP Subnet Calculator'),
        })

    # ── POST ──────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'subnet_info')
            dispatch = {
                'subnet_info':        self._calc_subnet_info,
                'subnet_from_hosts':  self._calc_from_hosts,
                'subnet_from_subnets': self._calc_from_subnets,
                'supernet':           self._calc_supernet,
                'convert_mask':       self._calc_convert,
            }
            handler = dispatch.get(ct)
            if not handler:
                return self._err(_('Invalid calculation type.'))
            return handler(data)
        except json.JSONDecodeError:
            return self._err(_('Invalid JSON data.'))
        except (ValueError, TypeError) as e:
            return self._err(str(e))
        except Exception:
            return self._err(_('An error occurred during calculation.'), 500)

    # ── helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _err(msg, status=400):
        return JsonResponse({'success': False, 'error': str(msg)}, status=status)

    @staticmethod
    def _parse_ip(ip_str):
        try:
            return ipaddress.IPv4Address(ip_str.strip())
        except (ValueError, ipaddress.AddressValueError):
            raise ValueError(str(_('Invalid IP address: {ip}').format(ip=ip_str)))

    @staticmethod
    def _parse_cidr(mask_str):
        """Accept '/24', '24', or '255.255.255.0' → returns int CIDR."""
        s = mask_str.strip().lstrip('/')
        # Try as integer CIDR
        try:
            c = int(s)
            if 0 <= c <= 32:
                return c
        except ValueError:
            pass
        # Try as dotted-decimal mask
        try:
            m = int(ipaddress.IPv4Address(s))
            b = format(m, '032b')
            if '01' in b:
                raise ValueError(str(_('Invalid subnet mask.')))
            return b.count('1')
        except (ValueError, ipaddress.AddressValueError):
            raise ValueError(str(_('Invalid subnet mask or CIDR: {m}').format(m=mask_str)))

    @staticmethod
    def _cidr_to_mask(cidr):
        m = (0xffffffff >> (32 - cidr)) << (32 - cidr) if cidr else 0
        return str(ipaddress.IPv4Address(m))

    @staticmethod
    def _wildcard(cidr):
        m = (0xffffffff >> (32 - cidr)) << (32 - cidr) if cidr else 0
        return str(ipaddress.IPv4Address(0xffffffff ^ m))

    @staticmethod
    def _ip_class(ip):
        o = int(ip) >> 24
        if o < 128:   return 'A'
        if o < 192:   return 'B'
        if o < 224:   return 'C'
        if o < 240:   return 'D'
        return 'E'

    @staticmethod
    def _net_type(net):
        if net.is_loopback:     return str(_('Loopback'))
        if net.is_link_local:   return str(_('Link-Local'))
        if net.is_multicast:    return str(_('Multicast'))
        if net.is_reserved:     return str(_('Reserved'))
        if net.is_private:      return str(_('Private'))
        return str(_('Public'))

    @staticmethod
    def _ip_binary(ip):
        return '.'.join(format(o, '08b') for o in ip.packed)

    # ── 1) SUBNET INFO ───────────────────────────────────────────────
    def _calc_subnet_info(self, data):
        ip_str = (data.get('ip_address') or '').strip()
        mask_str = (data.get('subnet_mask') or '').strip()
        if not ip_str:
            return self._err(_('IP address is required.'))
        if not mask_str:
            return self._err(_('Subnet mask or CIDR is required.'))

        ip = self._parse_ip(ip_str)
        cidr = self._parse_cidr(mask_str)
        net = ipaddress.IPv4Network(f'{ip}/{cidr}', strict=False)

        mask = self._cidr_to_mask(cidr)
        wc = self._wildcard(cidr)
        total = net.num_addresses
        usable = max(0, total - 2)
        first = str(net.network_address + 1) if total > 2 else None
        last = str(net.broadcast_address - 1) if total > 2 else None
        cls = self._ip_class(ip)
        ntype = self._net_type(net)

        steps = [
            str(_('Step 1: Given values')),
            f'  • IP = {ip_str}',
            f'  • {_("Mask")} = {mask_str} → /{cidr}',
            '',
            str(_('Step 2: Convert IP and mask to binary')),
            f'  IP:   {self._ip_binary(ip)}',
            f'  Mask: {self._ip_binary(ipaddress.IPv4Address(mask))}',
            '',
            str(_('Step 3: Network address (IP AND Mask)')),
            f'  {_("Network")} = {net.network_address}',
            '',
            str(_('Step 4: Broadcast address (Network OR ~Mask)')),
            f'  {_("Broadcast")} = {net.broadcast_address}',
            '',
            str(_('Step 5: Host range')),
            f'  {_("Total addresses")} = 2^(32−{cidr}) = {total}',
            f'  {_("Usable hosts")} = {total} − 2 = {usable}',
        ]
        if first and last:
            steps.append(f'  {_("First host")} = {first}')
            steps.append(f'  {_("Last host")} = {last}')
        steps += [
            '',
            str(_('Step 6: Classification')),
            f'  {_("Class")} = {cls}',
            f'  {_("Type")} = {ntype}',
            '',
            str(_('Result: Network {net}/{cidr}  —  {u} usable hosts').format(
                net=net.network_address, cidr=cidr, u=usable)),
        ]

        chart = {
            'main_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': [str(_('Usable Hosts')), str(_('Reserved'))],
                    'datasets': [{
                        'data': [usable, total - usable],
                        'backgroundColor': ['rgba(16,185,129,0.8)', 'rgba(156,163,175,0.6)'],
                        'borderColor': ['#10b981', '#9ca3af'],
                        'borderWidth': 2,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {
                        'legend': {'display': True, 'position': 'bottom'},
                        'title': {'display': True,
                                  'text': str(_('Host Distribution — /{c}').format(c=cidr))},
                    },
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'subnet_info',
            'result': str(net.network_address), 'result_label': str(_('Network Address')),
            'ip_address': ip_str, 'cidr': cidr,
            'network_address': str(net.network_address),
            'broadcast_address': str(net.broadcast_address),
            'subnet_mask': mask, 'wildcard_mask': wc,
            'total_hosts': total, 'usable_hosts': usable,
            'first_host': first, 'last_host': last,
            'ip_class': cls, 'network_type': ntype,
            'formula': f'{net.network_address}/{cidr}  ({usable} hosts)',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Network')), 'value': str(net.network_address), 'color': 'blue'},
                {'label': str(_('Broadcast')), 'value': str(net.broadcast_address), 'color': 'green'},
                {'label': str(_('Subnet Mask')), 'value': mask, 'color': 'yellow'},
                {'label': str(_('Usable Hosts')), 'value': f'{usable:,}', 'color': 'purple'},
                {'label': str(_('Wildcard')), 'value': wc, 'color': 'indigo'},
                {'label': str(_('Class / Type')), 'value': f'{cls} / {ntype}', 'color': 'pink'},
            ],
        })

    # ── 2) SUBNET FROM HOSTS ─────────────────────────────────────────
    def _calc_from_hosts(self, data):
        ip_str = (data.get('ip_address') or '').strip()
        hosts_str = data.get('hosts_needed')
        if not ip_str:
            return self._err(_('IP address is required.'))
        if hosts_str is None or hosts_str == '':
            return self._err(_('Number of hosts is required.'))

        ip = self._parse_ip(ip_str)
        hosts = int(hosts_str)
        if hosts < 1:
            return self._err(_('Hosts needed must be at least 1.'))
        if hosts > 16777214:
            return self._err(_('Maximum hosts is 16,777,214.'))

        required = hosts + 2
        host_bits = math.ceil(math.log2(required))
        cidr = 32 - host_bits
        if cidr < 0:
            return self._err(_('Cannot accommodate that many hosts.'))

        net = ipaddress.IPv4Network(f'{ip}/{cidr}', strict=False)
        mask = self._cidr_to_mask(cidr)
        total = net.num_addresses
        usable = max(0, total - 2)

        steps = [
            str(_('Step 1: Given values')),
            f'  • IP = {ip_str}',
            f'  • {_("Hosts needed")} = {hosts:,}',
            '',
            str(_('Step 2: Calculate required addresses')),
            f'  {_("Required")} = {hosts} + 2 ({_("network + broadcast")}) = {required}',
            '',
            str(_('Step 3: Find host bits')),
            f'  2^n ≥ {required}  →  n = ⌈log₂({required})⌉ = {host_bits}',
            '',
            str(_('Step 4: Calculate CIDR')),
            f'  CIDR = 32 − {host_bits} = /{cidr}',
            f'  {_("Mask")} = {mask}',
            '',
            str(_('Step 5: Verify')),
            f'  2^{host_bits} = {total} {_("total")}  →  {usable} {_("usable")}  ≥  {hosts} ✓',
            '',
            str(_('Result: /{cidr} ({mask})  —  {u} usable hosts').format(
                cidr=cidr, mask=mask, u=usable)),
        ]

        chart = {
            'main_chart': {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Hosts Needed')), str(_('Usable Hosts')), str(_('Total Addresses'))],
                    'datasets': [{
                        'label': str(_('Count')),
                        'data': [hosts, usable, total],
                        'backgroundColor': ['rgba(251,191,36,0.7)', 'rgba(16,185,129,0.7)',
                                            'rgba(59,130,246,0.7)'],
                        'borderColor': ['#fbbf24', '#10b981', '#3b82f6'],
                        'borderWidth': 2, 'borderRadius': 6,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False},
                                'title': {'display': True,
                                          'text': str(_('Hosts Needed vs Available'))}},
                    'scales': {'y': {'beginAtZero': True}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'subnet_from_hosts',
            'result': f'/{cidr}', 'result_label': str(_('Required CIDR')),
            'ip_address': ip_str, 'hosts_needed': hosts,
            'cidr': cidr, 'subnet_mask': mask,
            'total_hosts': total, 'usable_hosts': usable,
            'network_address': str(net.network_address),
            'broadcast_address': str(net.broadcast_address),
            'formula': f'/{cidr}  ({mask})  →  {usable:,} usable',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': 'CIDR', 'value': f'/{cidr}', 'color': 'blue'},
                {'label': str(_('Mask')), 'value': mask, 'color': 'green'},
                {'label': str(_('Usable')), 'value': f'{usable:,}', 'color': 'yellow'},
                {'label': str(_('Total')), 'value': f'{total:,}', 'color': 'purple'},
            ],
        })

    # ── 3) SUBNET FROM SUBNETS ───────────────────────────────────────
    def _calc_from_subnets(self, data):
        ip_str = (data.get('ip_address') or '').strip()
        orig_cidr_str = data.get('original_cidr')
        subnets_str = data.get('subnets_needed')

        if not ip_str:
            return self._err(_('IP address is required.'))
        if orig_cidr_str is None or orig_cidr_str == '':
            return self._err(_('Original CIDR is required.'))
        if subnets_str is None or subnets_str == '':
            return self._err(_('Number of subnets is required.'))

        ip = self._parse_ip(ip_str)
        orig = int(orig_cidr_str)
        needed = int(subnets_str)

        if orig < 0 or orig > 30:
            return self._err(_('Original CIDR must be between 0 and 30.'))
        if needed < 2:
            return self._err(_('Subnets needed must be at least 2.'))

        extra_bits = math.ceil(math.log2(needed))
        new_cidr = orig + extra_bits
        if new_cidr > 32:
            return self._err(_('Cannot create that many subnets from /{o}.').format(o=orig))

        actual = 2 ** extra_bits
        net = ipaddress.IPv4Network(f'{ip}/{orig}', strict=False)
        subnets_list = list(net.subnets(new_prefix=new_cidr))
        hosts_per = max(0, 2 ** (32 - new_cidr) - 2)
        mask = self._cidr_to_mask(new_cidr)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Network")} = {ip_str}/{orig}',
            f'  • {_("Subnets needed")} = {needed}',
            '',
            str(_('Step 2: Calculate extra bits')),
            f'  2^n ≥ {needed}  →  n = ⌈log₂({needed})⌉ = {extra_bits}',
            '',
            str(_('Step 3: New CIDR')),
            f'  {_("New CIDR")} = {orig} + {extra_bits} = /{new_cidr}',
            f'  {_("Mask")} = {mask}',
            f'  {_("Actual subnets")} = 2^{extra_bits} = {actual}',
            '',
            str(_('Step 4: Hosts per subnet')),
            f'  2^(32−{new_cidr}) − 2 = {hosts_per}',
            '',
            str(_('Step 5: Subnet list (first 8)')),
        ]
        for i, sn in enumerate(subnets_list[:8]):
            steps.append(f'  • {_("Subnet")} {i+1}: {sn}')
        if len(subnets_list) > 8:
            steps.append(f'  … {_("and")} {len(subnets_list) - 8} {_("more")}')
        steps += [
            '',
            str(_('Result: /{new}  →  {a} subnets, {h} hosts each').format(
                new=new_cidr, a=actual, h=hosts_per)),
        ]

        chart = {
            'main_chart': {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Original CIDR')), str(_('New CIDR')), str(_('Subnets Created'))],
                    'datasets': [{
                        'label': str(_('Value')),
                        'data': [orig, new_cidr, actual],
                        'backgroundColor': ['rgba(59,130,246,0.7)', 'rgba(16,185,129,0.7)',
                                            'rgba(251,191,36,0.7)'],
                        'borderColor': ['#3b82f6', '#10b981', '#fbbf24'],
                        'borderWidth': 2, 'borderRadius': 6,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False},
                                'title': {'display': True,
                                          'text': str(_('Subnet Division'))}},
                    'scales': {'y': {'beginAtZero': True}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'subnet_from_subnets',
            'result': f'/{new_cidr}', 'result_label': str(_('New CIDR')),
            'ip_address': ip_str, 'original_cidr': orig,
            'new_cidr': new_cidr, 'actual_subnets': actual,
            'hosts_per_subnet': hosts_per, 'subnet_mask': mask,
            'subnets_needed': needed,
            'subnets_list': [str(s) for s in subnets_list[:16]],
            'formula': f'/{orig} → /{new_cidr}  ({actual} subnets × {hosts_per} hosts)',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Original')), 'value': f'/{orig}', 'color': 'blue'},
                {'label': str(_('New CIDR')), 'value': f'/{new_cidr}', 'color': 'green'},
                {'label': str(_('Subnets')), 'value': str(actual), 'color': 'yellow'},
                {'label': str(_('Hosts/Subnet')), 'value': f'{hosts_per:,}', 'color': 'purple'},
            ],
        })

    # ── 4) SUPERNET (Aggregate) ──────────────────────────────────────
    def _calc_supernet(self, data):
        nets_str = (data.get('networks') or '').strip()
        if not nets_str:
            return self._err(_('Networks list is required (one per line or comma-separated).'))

        raw = [n.strip() for n in nets_str.replace(',', '\n').split('\n') if n.strip()]
        if len(raw) < 2:
            return self._err(_('At least 2 networks are required for supernetting.'))
        if len(raw) > 32:
            return self._err(_('Maximum 32 networks for supernetting.'))

        try:
            nets = [ipaddress.IPv4Network(n, strict=False) for n in raw]
        except (ValueError, ipaddress.AddressValueError) as e:
            return self._err(str(_('Invalid network: {e}').format(e=str(e))))

        try:
            supernet = list(ipaddress.collapse_addresses(nets))
        except Exception:
            return self._err(_('Could not aggregate these networks.'))

        steps = [
            str(_('Step 1: Input networks')),
        ]
        for n in nets:
            steps.append(f'  • {n}')
        steps += [
            '',
            str(_('Step 2: Sort and align networks')),
        ]
        sorted_nets = sorted(nets, key=lambda x: int(x.network_address))
        for n in sorted_nets:
            steps.append(f'  • {n.network_address}  →  {self._ip_binary(n.network_address)}')
        steps += [
            '',
            str(_('Step 3: Aggregate (collapse)')),
        ]
        for s in supernet:
            steps.append(f'  • {s}  ({s.num_addresses:,} addresses)')
        steps += [
            '',
            str(_('Result: {n} networks → {s} supernet(s)').format(n=len(nets), s=len(supernet))),
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'supernet',
            'result': ', '.join(str(s) for s in supernet),
            'result_label': str(_('Supernet')),
            'input_networks': [str(n) for n in nets],
            'supernets': [str(s) for s in supernet],
            'input_count': len(nets),
            'output_count': len(supernet),
            'formula': f'{len(nets)} → {len(supernet)} supernet(s)',
            'step_by_step': steps,
            'detail_cards': [
                {'label': str(_('Input')), 'value': f'{len(nets)} networks', 'color': 'blue'},
                {'label': str(_('Output')), 'value': f'{len(supernet)} supernet(s)', 'color': 'green'},
            ],
        })

    # ── 5) CONVERT MASK ──────────────────────────────────────────────
    def _calc_convert(self, data):
        val = (data.get('value') or '').strip()
        if not val:
            return self._err(_('Mask value is required.'))

        from_fmt = data.get('from_format', 'cidr')
        to_fmt = data.get('to_format', 'decimal')

        if from_fmt == 'cidr':
            try:
                cidr = int(val.lstrip('/'))
            except ValueError:
                return self._err(_('Invalid CIDR value.'))
            if cidr < 0 or cidr > 32:
                return self._err(_('CIDR must be between 0 and 32.'))
            mask = self._cidr_to_mask(cidr)
        elif from_fmt == 'decimal':
            try:
                m = ipaddress.IPv4Address(val)
                b = format(int(m), '032b')
                if '01' in b:
                    return self._err(_('Invalid subnet mask.'))
                cidr = b.count('1')
                mask = val
            except (ValueError, ipaddress.AddressValueError):
                return self._err(_('Invalid dotted-decimal mask.'))
        else:
            return self._err(_('Invalid source format.'))

        wc = self._wildcard(cidr)
        total = 2 ** (32 - cidr)
        usable = max(0, total - 2)
        result_val = str(cidr) if to_fmt == 'cidr' else mask

        binary = self._ip_binary(ipaddress.IPv4Address(mask))
        steps = [
            str(_('Step 1: Given value')),
            f'  {val} ({from_fmt})',
            '',
            str(_('Step 2: Binary representation')),
            f'  {binary}',
            f'  {_("Network bits")} = {cidr},  {_("Host bits")} = {32 - cidr}',
            '',
            str(_('Step 3: All representations')),
            f'  CIDR: /{cidr}',
            f'  {_("Decimal")}: {mask}',
            f'  {_("Wildcard")}: {wc}',
            f'  {_("Total addresses")}: {total:,}',
            f'  {_("Usable hosts")}: {usable:,}',
            '',
            str(_('Result: /{c}  =  {m}  (wildcard {w})').format(c=cidr, m=mask, w=wc)),
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'convert_mask',
            'result': result_val,
            'result_label': str(_('Converted Mask')),
            'cidr': cidr, 'subnet_mask': mask,
            'wildcard_mask': wc, 'binary': binary,
            'total_hosts': total, 'usable_hosts': usable,
            'formula': f'/{cidr} = {mask} (wildcard {wc})',
            'step_by_step': steps,
            'detail_cards': [
                {'label': 'CIDR', 'value': f'/{cidr}', 'color': 'blue'},
                {'label': str(_('Mask')), 'value': mask, 'color': 'green'},
                {'label': str(_('Wildcard')), 'value': wc, 'color': 'yellow'},
                {'label': str(_('Usable')), 'value': f'{usable:,}', 'color': 'purple'},
            ],
        })
