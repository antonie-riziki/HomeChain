from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'index.html')

def employer_dashboard(request):
    return render(request, 'employer_dashboard.html')

def contract(request):
    return render(request, 'contract_agreement.html')

def job_post(request):
    return render(request, 'job_post.html')

def resolution(request):
    return render(request, 'resolution.html')

def role_selection(request):
    return render(request, 'role_selection.html')

def wallet(request):
    return render(request, 'wallet.html')

def worker_dashboard(request):
    return render(request, 'worker_dashboard.html')
