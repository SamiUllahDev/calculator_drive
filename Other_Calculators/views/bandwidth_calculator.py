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
    Bandwidth Calculator — 6 calculation types.

    Calculation types
        • transfer_time   → time to transfer a file at given bandwidth
        • bandwidth_req   → bandwidth needed to transfer in given time
        • file_size       → max file size for bandwidth × time
        • real_world      → accounts for protocol overhead
        • comparison      → compare connection types side-by-side
        • recommendation  → suggest bandwidth for use-case
    """
    template_name = 'other_calculators/bandwidth_calculator.html'

    # ── constants ─────────────────────────────────────────────────────
    # file-size → bits  (binary: 1 KB = 1024 bytes)
    FS = {
        'bits': 1, 'bytes': 8,
        'KB': 8 * 1024, 'MB': 8 * 1024**2,
        'GB': 8 * 1024**3, 'TB': 8 * 1024**4,
    }
    # bandwidth → bits/s  (decimal: 1 Kbps = 1000 bps)
    BW = {
        'bps': 1, 'Kbps': 1e3,
        'Mbps': 1e6, 'Gbps': 1e9, 'Tbps': 1e12,
    }
    TIME = {'seconds': 1, 'minutes': 60, 'hours': 3600, 'days': 86400}
    OVERHEAD = {
        'none': 0, 'tcp': 0.10, 'udp': 0.05,
        'http': 0.12, 'https': 0.15, 'ftp': 0.08,
    }
    CONNS = [
        ('Dial-up',   56,    'Kbps'),
        ('DSL',       8,     'Mbps'),
        ('Cable',     100,   'Mbps'),
        ('Fiber',     500,   'Mbps'),
        ('4G LTE',    50,    'Mbps'),
        ('5G',        1000,  'Mbps'),
        ('Gigabit',   1000,  'Mbps'),
        ('10 Gig',    10000, 'Mbps'),
    ]
    USE_CASES = {
        'web':       (2,   'Web Browsing'),
        'email':     (1,   'Email'),
        'hd':        (5,   'HD Streaming'),
        '4k':        (25,  '4K Streaming'),
        'video_call':(4,   'Video Calls'),
        'gaming':    (5,   'Online Gaming'),
        'remote':    (10,  'Remote Work'),
        'general':   (5,   'General Use'),
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Bandwidth Calculator'),
        })

    # ── POST ──────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'transfer_time')
            dispatch = {
                'transfer_time':   self._calc_transfer_time,
                'bandwidth_req':   self._calc_bandwidth_req,
                'file_size':       self._calc_file_size,
                'real_world':      self._calc_real_world,
                'comparison':      self._calc_comparison,
                'recommendation':  self._calc_recommendation,
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

    def _to_bits(self, val, unit):
        f = self.FS.get(unit)
        if f is None:
            raise ValueError(str(_('Unknown file-size unit: {u}').format(u=unit)))
        return float(val) * f

    def _to_bps(self, val, unit):
        f = self.BW.get(unit)
        if f is None:
            raise ValueError(str(_('Unknown bandwidth unit: {u}').format(u=unit)))
        return float(val) * f

    def _to_sec(self, val, unit):
        f = self.TIME.get(unit)
        if f is None:
            raise ValueError(str(_('Unknown time unit: {u}').format(u=unit)))
        return float(val) * f

    @staticmethod
    def _fmt_time(s):
        if s < 0.01:
            return f'{s*1000:.2f} ms'
        if s < 60:
            return f'{s:.2f} sec'
        if s < 3600:
            return f'{s/60:.2f} min'
        if s < 86400:
            return f'{s/3600:.2f} hr'
        return f'{s/86400:.2f} days'

    @staticmethod
    def _fmt_bw(bps):
        if bps < 1e3:   return f'{bps:.2f} bps'
        if bps < 1e6:   return f'{bps/1e3:.2f} Kbps'
        if bps < 1e9:   return f'{bps/1e6:.2f} Mbps'
        if bps < 1e12:  return f'{bps/1e9:.2f} Gbps'
        return f'{bps/1e12:.2f} Tbps'

    @staticmethod
    def _fmt_fs(bits):
        b = bits / 8
        if b < 1024:        return f'{b:.2f} B'
        if b < 1024**2:     return f'{b/1024:.2f} KB'
        if b < 1024**3:     return f'{b/1024**2:.2f} MB'
        if b < 1024**4:     return f'{b/1024**3:.2f} GB'
        return f'{b/1024**4:.2f} TB'

    def _time_breakdown(self, s):
        return {
            'seconds': round(s, 4), 'minutes': round(s/60, 4),
            'hours': round(s/3600, 4), 'days': round(s/86400, 4),
            'formatted': self._fmt_time(s),
        }

    def _bw_breakdown(self, bps):
        return {
            'bps': round(bps, 2), 'Kbps': round(bps/1e3, 4),
            'Mbps': round(bps/1e6, 4), 'Gbps': round(bps/1e9, 6),
            'formatted': self._fmt_bw(bps),
        }

    def _fs_breakdown(self, bits):
        b = bits / 8
        return {
            'bits': round(bits, 2), 'bytes': round(b, 2),
            'KB': round(b/1024, 4), 'MB': round(b/1024**2, 4),
            'GB': round(b/1024**3, 6), 'TB': round(b/1024**4, 8),
            'formatted': self._fmt_fs(bits),
        }

    # ── 1) TRANSFER TIME ─────────────────────────────────────────────
    def _calc_transfer_time(self, data):
        fs = data.get('file_size')
        fu = data.get('file_size_unit', 'MB')
        bw = data.get('bandwidth')
        bu = data.get('bandwidth_unit', 'Mbps')

        if not fs or not bw:
            return self._err(_('File size and bandwidth are required.'))

        bits = self._to_bits(fs, fu)
        bps = self._to_bps(bw, bu)
        if bits <= 0 or bps <= 0:
            return self._err(_('Values must be greater than zero.'))

        t = bits / bps
        tb = self._time_breakdown(t)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("File")} = {fs} {fu}',
            f'  • {_("Bandwidth")} = {bw} {bu}',
            '',
            str(_('Step 2: Convert to bits and bps')),
            f'  {_("File")} = {fs} {fu} × {self.FS[fu]:,} = {int(bits):,} bits',
            f'  {_("Bandwidth")} = {bw} {bu} × {self.BW[bu]:,.0f} = {int(bps):,} bps',
            '',
            str(_('Step 3: Calculate time')),
            f'  {_("Time")} = {int(bits):,} ÷ {int(bps):,} = {t:.4f} {_("seconds")}',
            '',
            str(_('Step 4: Time breakdown')),
            f'  {_("Seconds")}: {tb["seconds"]}',
            f'  {_("Minutes")}: {tb["minutes"]}',
            f'  {_("Hours")}: {tb["hours"]}',
            f'  {_("Days")}: {tb["days"]}',
            '',
            str(_('Result: {t}').format(t=tb["formatted"])),
        ]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': [str(_('Seconds')), str(_('Minutes')), str(_('Hours')), str(_('Days'))],
                'datasets': [{
                    'label': str(_('Transfer Time')),
                    'data': [tb['seconds'], tb['minutes'], tb['hours'], tb['days']],
                    'backgroundColor': ['rgba(59,130,246,0.7)', 'rgba(16,185,129,0.7)',
                                        'rgba(245,158,11,0.7)', 'rgba(239,68,68,0.7)'],
                    'borderColor': ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
                    'borderWidth': 2, 'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Transfer Time Breakdown'))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'transfer_time',
            'result': tb['formatted'], 'result_label': str(_('Transfer Time')),
            'time_breakdown': tb,
            'formula': f'{fs} {fu} ÷ {bw} {bu} = {tb["formatted"]}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Seconds')), 'value': str(tb['seconds']), 'color': 'blue'},
                {'label': str(_('Minutes')), 'value': str(tb['minutes']), 'color': 'green'},
                {'label': str(_('Hours')), 'value': str(tb['hours']), 'color': 'yellow'},
                {'label': str(_('Days')), 'value': str(tb['days']), 'color': 'red'},
            ],
        })

    # ── 2) BANDWIDTH REQUIRED ────────────────────────────────────────
    def _calc_bandwidth_req(self, data):
        fs = data.get('file_size')
        fu = data.get('file_size_unit', 'MB')
        tv = data.get('time_value')
        tu = data.get('time_unit', 'seconds')

        if not fs or not tv:
            return self._err(_('File size and time are required.'))

        bits = self._to_bits(fs, fu)
        secs = self._to_sec(tv, tu)
        if bits <= 0 or secs <= 0:
            return self._err(_('Values must be greater than zero.'))

        bps = bits / secs
        bb = self._bw_breakdown(bps)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("File")} = {fs} {fu}',
            f'  • {_("Time")} = {tv} {tu}',
            '',
            str(_('Step 2: Convert')),
            f'  {_("File")} = {int(bits):,} bits',
            f'  {_("Time")} = {secs:.2f} seconds',
            '',
            str(_('Step 3: Calculate bandwidth')),
            f'  {_("Bandwidth")} = {int(bits):,} ÷ {secs:.2f} = {bps:.2f} bps',
            '',
            str(_('Step 4: Bandwidth breakdown')),
            f'  Kbps: {bb["Kbps"]}',
            f'  Mbps: {bb["Mbps"]}',
            f'  Gbps: {bb["Gbps"]}',
            '',
            str(_('Result: {b}').format(b=bb["formatted"])),
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'bandwidth_req',
            'result': bb['formatted'], 'result_label': str(_('Required Bandwidth')),
            'bandwidth_breakdown': bb,
            'formula': f'{fs} {fu} in {tv} {tu} → {bb["formatted"]}',
            'step_by_step': steps,
            'detail_cards': [
                {'label': 'bps',  'value': f'{bb["bps"]:,.0f}', 'color': 'blue'},
                {'label': 'Kbps', 'value': str(bb['Kbps']), 'color': 'green'},
                {'label': 'Mbps', 'value': str(bb['Mbps']), 'color': 'yellow'},
                {'label': 'Gbps', 'value': str(bb['Gbps']), 'color': 'purple'},
            ],
        })

    # ── 3) FILE SIZE ─────────────────────────────────────────────────
    def _calc_file_size(self, data):
        bw = data.get('bandwidth')
        bu = data.get('bandwidth_unit', 'Mbps')
        tv = data.get('time_value')
        tu = data.get('time_unit', 'seconds')

        if not bw or not tv:
            return self._err(_('Bandwidth and time are required.'))

        bps = self._to_bps(bw, bu)
        secs = self._to_sec(tv, tu)
        if bps <= 0 or secs <= 0:
            return self._err(_('Values must be greater than zero.'))

        bits = bps * secs
        fb = self._fs_breakdown(bits)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Bandwidth")} = {bw} {bu}',
            f'  • {_("Time")} = {tv} {tu}',
            '',
            str(_('Step 2: Convert')),
            f'  {_("Bandwidth")} = {bps:,.0f} bps',
            f'  {_("Time")} = {secs:.2f} seconds',
            '',
            str(_('Step 3: Calculate file size')),
            f'  {_("Size")} = {bps:,.0f} × {secs:.2f} = {bits:,.0f} bits',
            '',
            str(_('Step 4: File size breakdown')),
            f'  KB: {fb["KB"]}',
            f'  MB: {fb["MB"]}',
            f'  GB: {fb["GB"]}',
            '',
            str(_('Result: {s}').format(s=fb["formatted"])),
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'file_size',
            'result': fb['formatted'], 'result_label': str(_('Maximum File Size')),
            'file_size_breakdown': fb,
            'formula': f'{bw} {bu} × {tv} {tu} = {fb["formatted"]}',
            'step_by_step': steps,
            'detail_cards': [
                {'label': 'KB', 'value': str(fb['KB']), 'color': 'blue'},
                {'label': 'MB', 'value': str(fb['MB']), 'color': 'green'},
                {'label': 'GB', 'value': str(fb['GB']), 'color': 'yellow'},
                {'label': 'TB', 'value': str(fb['TB']), 'color': 'purple'},
            ],
        })

    # ── 4) REAL-WORLD SPEED ──────────────────────────────────────────
    def _calc_real_world(self, data):
        fs = data.get('file_size')
        fu = data.get('file_size_unit', 'MB')
        bw = data.get('bandwidth')
        bu = data.get('bandwidth_unit', 'Mbps')
        proto = data.get('protocol', 'tcp')

        if not fs or not bw:
            return self._err(_('File size and bandwidth are required.'))

        bits = self._to_bits(fs, fu)
        bps = self._to_bps(bw, bu)
        if bits <= 0 or bps <= 0:
            return self._err(_('Values must be greater than zero.'))

        oh_pct = self.OVERHEAD.get(proto, 0.10)
        eff_bps = bps * (1 - oh_pct)
        eff_pct = round((1 - oh_pct) * 100, 1)

        t_ideal = bits / bps
        t_real = bits / eff_bps

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("File")} = {fs} {fu}  ({int(bits):,} bits)',
            f'  • {_("Bandwidth")} = {bw} {bu}  ({int(bps):,} bps)',
            f'  • {_("Protocol")} = {proto.upper()}  ({oh_pct*100:.0f}% overhead)',
            '',
            str(_('Step 2: Calculate effective bandwidth')),
            f'  {_("Effective")} = {int(bps):,} × {eff_pct/100} = {eff_bps:,.0f} bps',
            f'  {_("Effective")} = {self._fmt_bw(eff_bps)}',
            '',
            str(_('Step 3: Calculate times')),
            f'  {_("Ideal time")} = {int(bits):,} ÷ {int(bps):,} = {self._fmt_time(t_ideal)}',
            f'  {_("Real time")} = {int(bits):,} ÷ {eff_bps:,.0f} = {self._fmt_time(t_real)}',
            f'  {_("Difference")} = {self._fmt_time(t_real - t_ideal)}',
            '',
            str(_('Result: {t} (real-world with {p} overhead)').format(
                t=self._fmt_time(t_real), p=proto.upper())),
        ]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': [str(_('Ideal Time (sec)')), str(_('Real Time (sec)'))],
                'datasets': [{
                    'label': str(_('Seconds')),
                    'data': [round(t_ideal, 4), round(t_real, 4)],
                    'backgroundColor': ['rgba(16,185,129,0.7)', 'rgba(239,68,68,0.7)'],
                    'borderColor': ['#10b981', '#ef4444'],
                    'borderWidth': 2, 'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Ideal vs Real-World'))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'real_world',
            'result': self._fmt_time(t_real),
            'result_label': str(_('Real-World Transfer Time')),
            'ideal_time': self._fmt_time(t_ideal),
            'real_time': self._fmt_time(t_real),
            'efficiency': eff_pct,
            'protocol': proto,
            'overhead_pct': oh_pct * 100,
            'effective_bw': self._fmt_bw(eff_bps),
            'formula': f'{fs} {fu} @ {bw} {bu} ({proto.upper()}) → {self._fmt_time(t_real)}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Ideal')), 'value': self._fmt_time(t_ideal), 'color': 'green'},
                {'label': str(_('Real')), 'value': self._fmt_time(t_real), 'color': 'red'},
                {'label': str(_('Efficiency')), 'value': f'{eff_pct}%', 'color': 'blue'},
                {'label': str(_('Effective BW')), 'value': self._fmt_bw(eff_bps), 'color': 'purple'},
            ],
        })

    # ── 5) CONNECTION COMPARISON ─────────────────────────────────────
    def _calc_comparison(self, data):
        fs = data.get('file_size')
        fu = data.get('file_size_unit', 'MB')

        if not fs:
            return self._err(_('File size is required.'))

        bits = self._to_bits(fs, fu)
        if bits <= 0:
            return self._err(_('File size must be greater than zero.'))

        rows = []
        labels, times_sec = [], []
        for name, speed, unit in self.CONNS:
            bps = speed * self.BW[unit]
            t = bits / bps
            rows.append({'name': name, 'speed': f'{speed} {unit}', 'time': self._fmt_time(t), 'seconds': round(t, 4)})
            labels.append(name)
            times_sec.append(round(t, 4))

        steps = [
            str(_('Step 1: File size')),
            f'  {fs} {fu} = {int(bits):,} bits',
            '',
            str(_('Step 2: Transfer time for each connection')),
        ]
        for r in rows:
            steps.append(f'  • {r["name"]} ({r["speed"]}): {r["time"]}')
        steps += ['', str(_('Result: Fastest = {n}  ({t})').format(n=rows[-1]['name'], t=rows[-1]['time']))]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Seconds')),
                    'data': times_sec,
                    'backgroundColor': 'rgba(59,130,246,0.7)',
                    'borderColor': '#3b82f6',
                    'borderWidth': 2, 'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'indexAxis': 'y',
                'plugins': {'legend': {'display': False},
                            'title': {'display': True,
                                      'text': str(_('Transfer Time by Connection'))}},
                'scales': {'x': {'beginAtZero': True,
                                 'title': {'display': True, 'text': str(_('Seconds'))}}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'comparison',
            'result': f'{len(rows)} connections compared',
            'result_label': str(_('Connection Comparison')),
            'file_size': fs, 'file_size_unit': fu,
            'connections': rows,
            'formula': f'{fs} {fu} across {len(rows)} connection types',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': rows[0]['name'], 'value': rows[0]['time'], 'color': 'red'},
                {'label': rows[-1]['name'], 'value': rows[-1]['time'], 'color': 'green'},
                {'label': str(_('File')), 'value': f'{fs} {fu}', 'color': 'blue'},
                {'label': str(_('Types')), 'value': str(len(rows)), 'color': 'purple'},
            ],
        })

    # ── 6) RECOMMENDATION ────────────────────────────────────────────
    def _calc_recommendation(self, data):
        uc = data.get('use_case', 'general')
        users = int(data.get('num_users', 1))
        streams = int(data.get('concurrent_streams', 1))

        if users < 1: users = 1
        if streams < 1: streams = 1
        if users > 100:
            return self._err(_('Maximum 100 users.'))

        base, label = self.USE_CASES.get(uc, self.USE_CASES['general'])
        total = base * users * streams
        recommended = round(total * 1.2, 2)  # 20 % headroom

        suitable = [(n, s, u) for n, s, u in self.CONNS
                     if s * (self.BW[u] / 1e6) >= recommended]

        steps = [
            str(_('Step 1: Use case')),
            f'  • {label}',
            f'  • {_("Base")} = {base} Mbps {_("per user per stream")}',
            '',
            str(_('Step 2: Total requirement')),
            f'  {base} × {users} {_("users")} × {streams} {_("streams")} = {total} Mbps',
            '',
            str(_('Step 3: Add 20% headroom')),
            f'  {total} × 1.2 = {recommended} Mbps',
            '',
            str(_('Step 4: Suitable connections')),
        ]
        for n, s, u in suitable:
            steps.append(f'  ✓ {n} ({s} {u})')
        if not suitable:
            steps.append(f'  {_("No standard connection meets this requirement.")}')
        steps += ['', str(_('Result: Recommended {r} Mbps for {l}').format(r=recommended, l=label))]

        return JsonResponse({
            'success': True, 'calc_type': 'recommendation',
            'result': f'{recommended} Mbps',
            'result_label': str(_('Recommended Bandwidth')),
            'use_case': label,
            'base_per_user': base,
            'users': users, 'streams': streams,
            'total_raw': total, 'recommended': recommended,
            'suitable': [{'name': n, 'speed': f'{s} {u}'} for n, s, u in suitable],
            'formula': f'{base} × {users} × {streams} × 1.2 = {recommended} Mbps',
            'step_by_step': steps,
            'detail_cards': [
                {'label': str(_('Base')), 'value': f'{base} Mbps', 'color': 'blue'},
                {'label': str(_('Users')), 'value': str(users), 'color': 'green'},
                {'label': str(_('Streams')), 'value': str(streams), 'color': 'yellow'},
                {'label': str(_('Recommended')), 'value': f'{recommended} Mbps', 'color': 'purple'},
            ],
        })
