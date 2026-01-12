from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import AdUnit, AdPlacement, AdStatistic


@staff_member_required
def ad_preview(request, ad_unit_id):
    """
    Preview an ad unit (admin only)
    """
    ad_unit = get_object_or_404(AdUnit, id=ad_unit_id)
    context = {
        'ad_unit': ad_unit,
    }
    return render(request, 'google_adsense/ad_preview.html', context)


@require_http_methods(["POST"])
def track_ad_display(request):
    """
    Track ad display (optional, for analytics)
    Called via AJAX when an ad is displayed
    """
    if not getattr(request, 'user', None):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    
    ad_unit_id = request.POST.get('ad_unit_id')
    placement = request.POST.get('placement', '')
    page_url = request.POST.get('page_url', request.path)
    
    try:
        ad_unit = AdUnit.objects.get(id=ad_unit_id, is_active=True)
        
        # Create statistic entry
        AdStatistic.objects.create(
            ad_unit=ad_unit,
            placement=placement,
            page_url=page_url,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=get_client_ip(request),
            is_mobile=request.user_agent.is_mobile if hasattr(request, 'user_agent') else False,
        )
        
        return JsonResponse({'status': 'success'})
    except AdUnit.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ad unit not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
