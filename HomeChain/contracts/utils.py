from django.template.loader import render_to_string
from django.utils.html import strip_tags
from weasyprint import HTML
import hashlib
import json
from datetime import datetime

def generate_contract_pdf(contract):
    """Generate PDF version of contract"""
    
    context = {
        'contract': contract,
        'employer': contract.employer,
        'worker': contract.worker,
        'job': contract.job,
        'generated_at': datetime.now(),
    }
    
    # Render HTML template
    html_string = render_to_string('contracts/contract_template.html', context)
    
    # Generate PDF
    pdf_file = HTML(string=html_string).write_pdf()
    
    return pdf_file


def generate_contract_summary(contract):
    """Generate human-readable contract summary"""
    
    summary = f"""
    CONTRACT SUMMARY
    ================
    
    Contract ID: {contract.id}
    Title: {contract.title}
    Status: {contract.get_status_display()}
    
    PARTIES:
    Employer: {contract.employer.full_name}
    Worker: {contract.worker.full_name}
    
    JOB DETAILS:
    Title: {contract.job.title}
    Location: {contract.job.location}
    
    PAYMENT:
    Amount: ${contract.payment_amount}
    Schedule: {contract.get_payment_schedule_display()}
    
    DURATION:
    Start Date: {contract.start_date}
    End Date: {contract.end_date}
    Days Remaining: {contract.days_remaining}
    
    SIGNATURES:
    Employer: {'✓' if contract.employer_signed else '✗'} 
    Worker: {'✓' if contract.worker_signed else '✗'}
    
    Created: {contract.created_at.strftime('%Y-%m-%d %H:%M')}
    """
    
    return summary


def verify_contract_hash(contract):
    """Verify contract hash matches terms"""
    current_hash = contract.generate_hash()
    return current_hash == contract.contract_hash


def create_contract_from_template(job, template_id, **kwargs):
    """Create contract from template"""
    from .models import Contract, ContractTemplate
    
    template = ContractTemplate.objects.get(id=template_id)
    worker = job.worker
    employer = job.employer
    
    contract = Contract(
        job=job,
        employer=employer,
        worker=worker,
        title=f"Contract for {job.title}",
        description=job.description,
        terms=template.terms,
        payment_amount=job.budget,
        start_date=kwargs.get('start_date'),
        end_date=kwargs.get('end_date'),
        status='PENDING'
    )
    
    contract.save()
    return contract


def calculate_milestone_payments(total_amount, num_milestones):
    """Calculate equal milestone payments"""
    import math
    per_milestone = math.ceil(total_amount / num_milestones * 100) / 100
    payments = [per_milestone] * num_milestones
    
    # Adjust last payment to match total
    total = sum(payments)
    if total != total_amount:
        payments[-1] = total_amount - (total - payments[-1])
    
    return payments