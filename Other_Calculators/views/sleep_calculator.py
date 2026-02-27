from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SleepCalculator(View):
    """
    Sleep Calculator: optimal wake times, bed times, sleep now.
    BMI-style upgrade: _get_data, SafeJSONEncoder, dict returns, str(_()).
    """
    template_name = 'other_calculators/sleep_calculator.html'

    SLEEP_CYCLE = 90
    FALL_ASLEEP_TIME = 15

    def _get_data(self, request):
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = request.body
                if not body:
                    return {}
                return json.loads(body)
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        if request.body:
            try:
                return json.loads(request.body)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _val(self, data, key, default=None):
        v = data.get(key, default)
        return (v[0] if isinstance(v, list) and v else v) if v is not None else default

    def get(self, request):
        context = {'calculator_name': str(_('Sleep Calculator'))}
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return HttpResponse(
                    json.dumps({'success': False, 'error': str(_('Invalid request data.'))}, cls=SafeJSONEncoder),
                    content_type='application/json',
                    status=400
                )
            calc_type = self._val(data, 'calc_type', 'wake_time')
            if calc_type == 'wake_time':
                result = self._calculate_wake_time(data)
            elif calc_type == 'bed_time':
                result = self._calculate_bed_time(data)
            elif calc_type == 'sleep_now':
                result = self._calculate_sleep_now(data)
            else:
                return HttpResponse(
                    json.dumps({'success': False, 'error': str(_('Invalid calculation type.'))}, cls=SafeJSONEncoder),
                    content_type='application/json',
                    status=400
                )
            if isinstance(result, dict) and not result.get('success'):
                return HttpResponse(
                    json.dumps(result, cls=SafeJSONEncoder),
                    content_type='application/json',
                    status=400
                )
            return HttpResponse(json.dumps(result, cls=SafeJSONEncoder), content_type='application/json')
        except Exception as e:
            logger.exception("Sleep calculator failed: %s", e)
            from django.conf import settings
            err_msg = str(_('An error occurred during calculation.'))
            if getattr(settings, 'DEBUG', False):
                err_msg += ' [' + str(e).replace('"', "'") + ']'
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}, cls=SafeJSONEncoder),
                content_type='application/json',
                status=500
            )

    def _calculate_wake_time(self, data):
        bed_hour_raw = self._val(data, 'bed_hour')
        bed_minute_raw = self._val(data, 'bed_minute')
        if bed_hour_raw is None or bed_hour_raw == '':
            return {'success': False, 'error': str(_('Bedtime hour is required.'))}
        if bed_minute_raw is None or bed_minute_raw == '':
            return {'success': False, 'error': str(_('Bedtime minute is required.'))}
        try:
            bed_hour = int(bed_hour_raw)
            bed_minute = int(bed_minute_raw)
        except (ValueError, TypeError):
            return {'success': False, 'error': str(_('Invalid input type. Please enter valid numbers.'))}
        if not (0 <= bed_hour <= 23) or not (0 <= bed_minute <= 59):
            return {'success': False, 'error': str(_('Invalid time. Hour must be 0-23 and minute must be 0-59.'))}

        now = datetime.now()
        bed_time = now.replace(hour=bed_hour, minute=bed_minute, second=0, microsecond=0)
        if bed_time < now:
            bed_time += timedelta(days=1)
        fall_asleep_time = bed_time + timedelta(minutes=self.FALL_ASLEEP_TIME)

        wake_times = []
        for cycles in range(4, 7):
            sleep_duration = cycles * self.SLEEP_CYCLE
            wake_time = fall_asleep_time + timedelta(minutes=sleep_duration)
            total_hours = sleep_duration / 60
            wake_times.append({
                'cycles': cycles,
                'time': wake_time.strftime('%I:%M %p'),
                'time_24': wake_time.strftime('%H:%M'),
                'sleep_hours': round(total_hours, 1),
                'quality': self.get_sleep_quality(cycles)
            })

        steps = self._prepare_wake_time_steps(bed_time, fall_asleep_time, wake_times)
        chart_data = self._prepare_wake_time_chart_data(wake_times)
        return {
            'success': True,
            'calc_type': 'wake_time',
            'bed_time': bed_time.strftime('%I:%M %p'),
            'bed_time_24': bed_time.strftime('%H:%M'),
            'fall_asleep_time': fall_asleep_time.strftime('%I:%M %p'),
            'wake_times': wake_times,
            'recommended': wake_times[1] if len(wake_times) > 1 else wake_times[0],
            'step_by_step': steps,
            'chart_data': chart_data,
            'tips': self._get_sleep_tips()
        }

    def _calculate_bed_time(self, data):
        wake_hour_raw = self._val(data, 'wake_hour')
        wake_minute_raw = self._val(data, 'wake_minute')
        if wake_hour_raw is None or wake_hour_raw == '':
            return {'success': False, 'error': str(_('Wake time hour is required.'))}
        if wake_minute_raw is None or wake_minute_raw == '':
            return {'success': False, 'error': str(_('Wake time minute is required.'))}
        try:
            wake_hour = int(wake_hour_raw)
            wake_minute = int(wake_minute_raw)
        except (ValueError, TypeError):
            return {'success': False, 'error': str(_('Invalid input type. Please enter valid numbers.'))}
        if not (0 <= wake_hour <= 23) or not (0 <= wake_minute <= 59):
            return {'success': False, 'error': str(_('Invalid time. Hour must be 0-23 and minute must be 0-59.'))}

        now = datetime.now()
        wake_time = now.replace(hour=wake_hour, minute=wake_minute, second=0, microsecond=0)
        if wake_time < now:
            wake_time += timedelta(days=1)

        bed_times = []
        for cycles in range(4, 7):
            sleep_duration = cycles * self.SLEEP_CYCLE + self.FALL_ASLEEP_TIME
            bed_time = wake_time - timedelta(minutes=sleep_duration)
            total_hours = (cycles * self.SLEEP_CYCLE) / 60
            bed_times.append({
                'cycles': cycles,
                'time': bed_time.strftime('%I:%M %p'),
                'time_24': bed_time.strftime('%H:%M'),
                'sleep_hours': round(total_hours, 1),
                'quality': self.get_sleep_quality(cycles)
            })

        steps = self._prepare_bed_time_steps(wake_time, bed_times)
        chart_data = self._prepare_bed_time_chart_data(bed_times)
        return {
            'success': True,
            'calc_type': 'bed_time',
            'wake_time': wake_time.strftime('%I:%M %p'),
            'wake_time_24': wake_time.strftime('%H:%M'),
            'bed_times': bed_times,
            'recommended': bed_times[1] if len(bed_times) > 1 else bed_times[0],
            'step_by_step': steps,
            'chart_data': chart_data,
            'tips': self._get_sleep_tips()
        }

    def _calculate_sleep_now(self, data):
        now = datetime.now()
        fall_asleep_time = now + timedelta(minutes=self.FALL_ASLEEP_TIME)
        wake_times = []
        for cycles in range(4, 7):
            sleep_duration = cycles * self.SLEEP_CYCLE
            wake_time = fall_asleep_time + timedelta(minutes=sleep_duration)
            total_hours = sleep_duration / 60
            wake_times.append({
                'cycles': cycles,
                'time': wake_time.strftime('%I:%M %p'),
                'time_24': wake_time.strftime('%H:%M'),
                'sleep_hours': round(total_hours, 1),
                'quality': self.get_sleep_quality(cycles)
            })
        steps = self._prepare_sleep_now_steps(now, fall_asleep_time, wake_times)
        chart_data = self._prepare_wake_time_chart_data(wake_times)
        return {
            'success': True,
            'calc_type': 'sleep_now',
            'current_time': now.strftime('%I:%M %p'),
            'current_time_24': now.strftime('%H:%M'),
            'fall_asleep_time': fall_asleep_time.strftime('%I:%M %p'),
            'wake_times': wake_times,
            'recommended': wake_times[1] if len(wake_times) > 1 else wake_times[0],
            'step_by_step': steps,
            'chart_data': chart_data,
            'tips': self._get_sleep_tips()
        }

    def get_sleep_quality(self, cycles):
        if cycles == 6:
            return {'rating': str(_('Excellent')), 'color': 'green'}
        elif cycles == 5:
            return {'rating': str(_('Good')), 'color': 'blue'}
        elif cycles == 4:
            return {'rating': str(_('Fair')), 'color': 'yellow'}
        else:
            return {'rating': str(_('Poor')), 'color': 'red'}

    def _get_sleep_tips(self):
        return [
            str(_('Maintain a consistent sleep schedule')),
            str(_('Avoid screens 1 hour before bed')),
            str(_('Keep your room cool (65-68°F / 18-20°C)')),
            str(_('Avoid caffeine 6 hours before sleep')),
            str(_('Exercise regularly, but not before bed')),
            str(_('Create a relaxing bedtime routine')),
            str(_('Keep your bedroom dark and quiet')),
            str(_('Avoid large meals before bedtime'))
        ]

    def _prepare_wake_time_steps(self, bed_time, fall_asleep_time, wake_times):
        steps = []
        steps.append(str(_('Step 1: Identify bedtime')))
        steps.append(str(_('Bedtime')) + ': ' + bed_time.strftime('%I:%M %p'))
        steps.append('')
        steps.append(str(_('Step 2: Account for time to fall asleep')))
        steps.append(str(_('Average time to fall asleep')) + ': ' + str(self.FALL_ASLEEP_TIME) + ' ' + str(_('minutes')))
        steps.append(str(_('Fall asleep time')) + ': ' + fall_asleep_time.strftime('%I:%M %p'))
        steps.append('')
        steps.append(str(_('Step 3: Calculate wake times based on sleep cycles')))
        steps.append(str(_('Each sleep cycle lasts approximately')) + ' ' + str(self.SLEEP_CYCLE) + ' ' + str(_('minutes')))
        for wake_time in wake_times:
            steps.append(str(wake_time['cycles']) + ' ' + str(_('cycles')) + ' = ' + str(wake_time['sleep_hours']) + ' ' + str(_('hours')) + ' → ' + str(_('Wake at')) + ' ' + str(wake_time['time']) + ' (' + str(wake_time['quality']['rating']) + ')')
        steps.append('')
        steps.append(str(_('Step 4: Recommended wake time')))
        recommended = wake_times[1] if len(wake_times) > 1 else wake_times[0]
        steps.append(str(_('Recommended')) + ': ' + str(recommended['time']) + ' (' + str(recommended['cycles']) + ' ' + str(_('cycles')) + ', ' + str(recommended['sleep_hours']) + ' ' + str(_('hours')) + ')')
        return steps

    def _prepare_bed_time_steps(self, wake_time, bed_times):
        steps = []
        steps.append(str(_('Step 1: Identify desired wake time')))
        steps.append(str(_('Wake time')) + ': ' + wake_time.strftime('%I:%M %p'))
        steps.append('')
        steps.append(str(_('Step 2: Calculate bed times based on sleep cycles')))
        steps.append(str(_('Each sleep cycle lasts approximately')) + ' ' + str(self.SLEEP_CYCLE) + ' ' + str(_('minutes')))
        steps.append(str(_('Time to fall asleep')) + ': ' + str(self.FALL_ASLEEP_TIME) + ' ' + str(_('minutes')))
        for bed_time in bed_times:
            total_minutes = bed_time['cycles'] * self.SLEEP_CYCLE + self.FALL_ASLEEP_TIME
            steps.append(str(bed_time['cycles']) + ' ' + str(_('cycles')) + ' = ' + str(bed_time['sleep_hours']) + ' ' + str(_('hours')) + ' ' + str(_('sleep')) + ' + ' + str(self.FALL_ASLEEP_TIME) + ' min ' + str(_('fall asleep')) + ' = ' + str(total_minutes) + ' min ' + str(_('total')) + ' → ' + str(_('Bed at')) + ' ' + str(bed_time['time']) + ' (' + str(bed_time['quality']['rating']) + ')')
        steps.append('')
        steps.append(str(_('Step 3: Recommended bed time')))
        recommended = bed_times[1] if len(bed_times) > 1 else bed_times[0]
        steps.append(str(_('Recommended')) + ': ' + str(recommended['time']) + ' (' + str(recommended['cycles']) + ' ' + str(_('cycles')) + ', ' + str(recommended['sleep_hours']) + ' ' + str(_('hours')) + ' ' + str(_('sleep')) + ')')
        return steps

    def _prepare_sleep_now_steps(self, now, fall_asleep_time, wake_times):
        steps = []
        steps.append(str(_('Step 1: Current time')))
        steps.append(str(_('Current time')) + ': ' + now.strftime('%I:%M %p'))
        steps.append('')
        steps.append(str(_('Step 2: Account for time to fall asleep')))
        steps.append(str(_('Average time to fall asleep')) + ': ' + str(self.FALL_ASLEEP_TIME) + ' ' + str(_('minutes')))
        steps.append(str(_('Fall asleep time')) + ': ' + fall_asleep_time.strftime('%I:%M %p'))
        steps.append('')
        steps.append(str(_('Step 3: Calculate wake times based on sleep cycles')))
        steps.append(str(_('Each sleep cycle lasts approximately')) + ' ' + str(self.SLEEP_CYCLE) + ' ' + str(_('minutes')))
        for wake_time in wake_times:
            steps.append(str(wake_time['cycles']) + ' ' + str(_('cycles')) + ' = ' + str(wake_time['sleep_hours']) + ' ' + str(_('hours')) + ' → ' + str(_('Wake at')) + ' ' + str(wake_time['time']) + ' (' + str(wake_time['quality']['rating']) + ')')
        steps.append('')
        steps.append(str(_('Step 4: Recommended wake time')))
        recommended = wake_times[1] if len(wake_times) > 1 else wake_times[0]
        steps.append(str(_('Recommended')) + ': ' + str(recommended['time']) + ' (' + str(recommended['cycles']) + ' ' + str(_('cycles')) + ', ' + str(recommended['sleep_hours']) + ' ' + str(_('hours')) + ')')
        return steps

    def _prepare_wake_time_chart_data(self, wake_times):
        colors_bg = ['#6366f1', '#8b5cf6', '#a78bfa']
        colors_border = ['#4f46e5', '#7c3aed', '#8b5cf6']
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [str(wt['cycles']) + ' ' + str(_('cycles')) for wt in wake_times],
                'datasets': [{
                    'label': str(_('Sleep Hours')),
                    'data': [wt['sleep_hours'] for wt in wake_times],
                    'backgroundColor': [colors_bg[i] for i in range(len(wake_times))],
                    'borderColor': [colors_border[i] for i in range(len(wake_times))],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': False},
                    'title': {'display': True, 'text': str(_('Sleep Duration by Cycle Count'))}
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {'display': True, 'text': str(_('Hours'))}
                    }
                }
            }
        }
        return {'wake_time_chart': chart_config}

    def _prepare_bed_time_chart_data(self, bed_times):
        colors_bg = ['#6366f1', '#8b5cf6', '#a78bfa']
        colors_border = ['#4f46e5', '#7c3aed', '#8b5cf6']
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [str(bt['cycles']) + ' ' + str(_('cycles')) for bt in bed_times],
                'datasets': [{
                    'label': str(_('Sleep Hours')),
                    'data': [bt['sleep_hours'] for bt in bed_times],
                    'backgroundColor': [colors_bg[i] for i in range(len(bed_times))],
                    'borderColor': [colors_border[i] for i in range(len(bed_times))],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': False},
                    'title': {'display': True, 'text': str(_('Sleep Duration by Cycle Count'))}
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {'display': True, 'text': str(_('Hours'))}
                    }
                }
            }
        }
        return {'bed_time_chart': chart_config}
