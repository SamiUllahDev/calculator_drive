from django import template
from django.utils.safestring import mark_safe
from user.models import Activity

register = template.Library()

@register.simple_tag
def user_activity_widget(user, limit=5):
    activities = Activity.objects.filter(user=user).order_by('-created_at')[:limit]
    
    html = []
    if activities:
        for activity in activities:
            html.append(f'''
                <div class="activity-item d-flex align-items-start mb-3">
                    <div class="activity-content flex-grow-1">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <small class="text-muted">{activity.created_at.strftime("%B %d, %Y %H:%M")}</small>
                        </div>
                        <p class="mb-0">{activity.description}</p>
                    </div>
                </div>
            ''')
    else:
        html.append('<p class="text-muted mb-0">No recent activity</p>')
    
    return mark_safe('\n'.join(html))
