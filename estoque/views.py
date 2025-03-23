from django.shortcuts import render

def page_not_found(request, exception):
    return render(request, '404.html', status=404)

def server_error(request):
    return render(request, '500.html', status=500)

def permission_denied(request, exception):
    return render(request, '401.html', status=401)

def index(request):
    return render(request, 'base.html')