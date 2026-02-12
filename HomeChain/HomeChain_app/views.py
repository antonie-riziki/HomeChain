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

def login(request):
    return render(request, 'login.html')

def register(request):
    return render(request, 'register.html')

def browse_jobs(request):
    return render(request, 'browse_jobs.html')

def workers(request):
    return render(request, 'workers.html')

def about(request):
    return render(request, 'about.html')

def help_center(request):
    return render(request, 'help.html')

def contact(request):
    return render(request, 'contact.html')
