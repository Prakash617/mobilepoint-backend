from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

@staff_member_required
def filehub_embed(request):
    return render(request, "filehub_embed.html")



# from django.shortcuts import redirect

def analytic_dashboard(request):
    # Redirect or embed FileHub in iframe
    return render(request, "admin/analytics_dashboard_iframe.html")  # or render iframe template