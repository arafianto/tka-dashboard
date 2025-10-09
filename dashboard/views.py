from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Count
from django.http import HttpResponse
from django.core.paginator import Paginator
import csv
from django.contrib.auth.decorators import login_required

from .models import Company, Worker, Document, RenewalHistory
from .forms import CompanyForm, WorkerForm, WorkerWithDocumentsForm, DocumentForm, RenewalForm


def create_documents_from_form(worker, cleaned_data):
    """Helper function to create documents from form data"""
    document_types = [
        ('rptka', 'RPTKA'),
        ('imta', 'IMTA'),
        ('visa', 'VISA'),
        ('kitas', 'KITAS'),
        ('sktt', 'SKTT'),
        ('passport', 'PASSPORT'),
    ]
    
    for prefix, doc_type in document_types:
        number_field = f"{prefix}_number"
        issue_field = f"{prefix}_issue"
        expiry_field = f"{prefix}_expiry"
        
        # Handle passport differently since it has a different field name
        if prefix == 'passport':
            number_field = f"{prefix}_number_doc"
        
        if cleaned_data.get(number_field) and cleaned_data.get(issue_field) and cleaned_data.get(expiry_field):
            Document.objects.create(
                worker=worker,
                type=doc_type,
                document_number=cleaned_data[number_field],
                issue_date=cleaned_data[issue_field],
                expiry_date=cleaned_data[expiry_field],
                status=Document.Status.ACTIVE
            )


@login_required
def dashboard(request):
    total_workers = Worker.objects.count()
    total_active_docs = Document.objects.filter(status=Document.Status.ACTIVE).count()
    total_expired_docs = Document.objects.filter(status=Document.Status.EXPIRED).count()

    today = timezone.localdate()
    d30 = today + timezone.timedelta(days=30)
    d60 = today + timezone.timedelta(days=60)
    d90 = today + timezone.timedelta(days=90)

    # Base queryset: only active docs within next 90 days
    base_qs = (
        Document.objects.select_related('worker', 'worker__company')
        .filter(status=Document.Status.ACTIVE, expiry_date__gte=today, expiry_date__lte=d90)
        .order_by('expiry_date')
    )

    # Scope data for client users
    profile = getattr(request.user, 'profile', None)
    if profile and getattr(profile, 'role', None) == 'CLIENT' and profile.company_id:
        base_qs = base_qs.filter(worker__company_id=profile.company_id)

    bucket_30 = base_qs.filter(expiry_date__lte=d30)
    bucket_60 = base_qs.filter(expiry_date__gt=d30, expiry_date__lte=d60)
    bucket_90 = base_qs.filter(expiry_date__gt=d60, expiry_date__lte=d90)

    def group_by_worker(docs):
        grouped = {}
        for doc in docs:
            grouped.setdefault(doc.worker, []).append(doc)
        return grouped

    context = {
        'total_workers': total_workers,
        'total_active_docs': total_active_docs,
        'total_expired_docs': total_expired_docs,
        'bucket30': group_by_worker(bucket_30),
        'bucket60': group_by_worker(bucket_60),
        'bucket90': group_by_worker(bucket_90),
        'today': today,
    }
    return render(request, 'core/dashboard.html', context)


# Companies CRUD
@login_required
def company_list(request):
    profile = getattr(request.user, 'profile', None)
    companies = Company.objects.all().order_by('name')
    if profile and profile.role == 'CLIENT' and profile.company_id:
        companies = companies.filter(id=profile.company_id)
    return render(request, 'core/company_list.html', {'companies': companies})


@login_required
def company_create(request):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'CLIENT':
        return redirect('company_list')
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('company_list')
    else:
        form = CompanyForm()
    return render(request, 'core/form.html', {'form': form, 'title': 'Tambah Perusahaan'})


@login_required
def company_update(request, pk):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'CLIENT':
        return redirect('company_list')
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect('company_list')
    else:
        form = CompanyForm(instance=company)
    return render(request, 'core/form.html', {'form': form, 'title': 'Edit Perusahaan'})


@login_required
def company_delete(request, pk):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.role == 'CLIENT':
        return redirect('company_list')
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        company.delete()
        return redirect('company_list')
    return render(request, 'core/confirm_delete.html', {'obj': company, 'title': 'Hapus Perusahaan'})


# Workers CRUD & detail
@login_required
def worker_list(request):
    query = request.GET.get('q', '')
    profile = getattr(request.user, 'profile', None)
    workers = Worker.objects.all()
    if profile and profile.role == 'CLIENT' and profile.company_id:
        workers = workers.filter(company_id=profile.company_id)
    if query:
        workers = workers.filter(
            Q(name__icontains=query)
            | Q(passport_number__icontains=query)
            | Q(company__name__icontains=query)
            | Q(nationality__icontains=query)
        )
    workers = workers.select_related('company').prefetch_related('documents').order_by('name')
    paginator = Paginator(workers, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/worker_list.html', {'workers': page_obj, 'q': query, 'page_obj': page_obj})


@login_required
def worker_detail(request, pk):
    profile = getattr(request.user, 'profile', None)
    qs = Worker.objects.all()
    if profile and profile.role == 'CLIENT' and profile.company_id:
        qs = qs.filter(company_id=profile.company_id)
    worker = get_object_or_404(qs, pk=pk)
    documents = worker.documents.all().order_by('type')
    return render(request, 'core/worker_detail.html', {'worker': worker, 'documents': documents})


@login_required
def worker_create(request):
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        form = WorkerWithDocumentsForm(request.POST, request.FILES)
        if profile and profile.role == 'CLIENT' and profile.company_id:
            # enforce company to client's company
            if form.is_valid():
                worker = form.save(commit=False)
                worker.company_id = profile.company_id
                worker.save()
                # Create documents if provided
                create_documents_from_form(worker, form.cleaned_data)
                return redirect('worker_detail', pk=worker.id)
        if form.is_valid():
            worker = form.save()
            # Create documents if provided
            create_documents_from_form(worker, form.cleaned_data)
            return redirect('worker_detail', pk=worker.id)
    else:
        form = WorkerWithDocumentsForm()
    if profile and profile.role == 'CLIENT' and profile.company_id:
        form.fields['company'].queryset = Company.objects.filter(id=profile.company_id)
    return render(request, 'core/worker_form_with_documents.html', {'form': form, 'title': 'Tambah Pekerja & Dokumen'})


@login_required
def worker_update(request, pk):
    profile = getattr(request.user, 'profile', None)
    qs = Worker.objects.all()
    if profile and profile.role == 'CLIENT' and profile.company_id:
        qs = qs.filter(company_id=profile.company_id)
    worker = get_object_or_404(qs, pk=pk)
    if request.method == 'POST':
        form = WorkerForm(request.POST, request.FILES, instance=worker)
        if form.is_valid():
            obj = form.save(commit=False)
            if profile and profile.role == 'CLIENT' and profile.company_id:
                obj.company_id = profile.company_id
            obj.save()
            return redirect('worker_list')
    else:
        form = WorkerForm(instance=worker)
    if profile and profile.role == 'CLIENT' and profile.company_id:
        form.fields['company'].queryset = Company.objects.filter(id=profile.company_id)
    return render(request, 'core/form.html', {'form': form, 'title': 'Edit Pekerja'})


@login_required
def worker_delete(request, pk):
    profile = getattr(request.user, 'profile', None)
    qs = Worker.objects.all()
    if profile and profile.role == 'CLIENT' and profile.company_id:
        qs = qs.filter(company_id=profile.company_id)
    worker = get_object_or_404(qs, pk=pk)
    if request.method == 'POST':
        worker.delete()
        return redirect('worker_list')
    return render(request, 'core/confirm_delete.html', {'obj': worker, 'title': 'Hapus Pekerja'})


# Documents CRUD
@login_required
def document_list(request):
    profile = getattr(request.user, 'profile', None)
    documents = Document.objects.select_related('worker', 'worker__company').all().order_by('expiry_date')
    if profile and profile.role == 'CLIENT' and profile.company_id:
        documents = documents.filter(worker__company_id=profile.company_id)
    paginator = Paginator(documents, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/document_list.html', {'documents': page_obj, 'page_obj': page_obj})


@login_required
def document_create(request):
    profile = getattr(request.user, 'profile', None)
    worker_id = request.GET.get('worker')
    
    if request.method == 'POST':
        form = DocumentForm(request.POST)
        if form.is_valid():
            doc = form.save(commit=False)
            # enforce worker belongs to client's company
            if profile and profile.role == 'CLIENT' and profile.company_id:
                if doc.worker.company_id != profile.company_id:
                    return redirect('document_list')
            doc.save()
            # Redirect back to worker detail if came from there
            if worker_id:
                return redirect('worker_detail', pk=worker_id)
            return redirect('document_list')
    else:
        form = DocumentForm()
        # Pre-select worker if specified in URL
        if worker_id:
            try:
                worker = Worker.objects.get(id=worker_id)
                form.fields['worker'].initial = worker
            except Worker.DoesNotExist:
                pass
    
    if profile and profile.role == 'CLIENT' and profile.company_id:
        form.fields['worker'].queryset = Worker.objects.filter(company_id=profile.company_id)
    
    return render(request, 'core/form.html', {'form': form, 'title': 'Tambah Dokumen'})


@login_required
def document_update(request, pk):
    profile = getattr(request.user, 'profile', None)
    qs = Document.objects.select_related('worker', 'worker__company')
    if profile and profile.role == 'CLIENT' and profile.company_id:
        qs = qs.filter(worker__company_id=profile.company_id)
    document = get_object_or_404(qs, pk=pk)
    if request.method == 'POST':
        form = DocumentForm(request.POST, instance=document)
        if form.is_valid():
            doc = form.save(commit=False)
            if profile and profile.role == 'CLIENT' and profile.company_id:
                if doc.worker.company_id != profile.company_id:
                    return redirect('document_list')
            doc.save()
            return redirect('document_list')
    else:
        form = DocumentForm(instance=document)
    if profile and profile.role == 'CLIENT' and profile.company_id:
        form.fields['worker'].queryset = Worker.objects.filter(company_id=profile.company_id)
    return render(request, 'core/form.html', {'form': form, 'title': 'Edit Dokumen'})


@login_required
def document_delete(request, pk):
    profile = getattr(request.user, 'profile', None)
    qs = Document.objects.select_related('worker', 'worker__company')
    if profile and profile.role == 'CLIENT' and profile.company_id:
        qs = qs.filter(worker__company_id=profile.company_id)
    document = get_object_or_404(qs, pk=pk)
    if request.method == 'POST':
        document.delete()
        return redirect('document_list')
    return render(request, 'core/confirm_delete.html', {'obj': document, 'title': 'Hapus Dokumen'})


# Renewal
@login_required
def document_renew(request, pk):
    profile = getattr(request.user, 'profile', None)
    qs = Document.objects.select_related('worker', 'worker__company')
    if profile and profile.role == 'CLIENT' and profile.company_id:
        qs = qs.filter(worker__company_id=profile.company_id)
    document = get_object_or_404(qs, pk=pk)
    if request.method == 'POST':
        form = RenewalForm(request.POST)
        if form.is_valid():
            renewal: RenewalHistory = form.save(commit=False)
            renewal.document = document
            renewal.save()
            # Update document with new data if provided
            if renewal.new_document_number:
                document.document_number = renewal.new_document_number
            if renewal.new_issue_date:
                document.issue_date = renewal.new_issue_date
            if renewal.new_expiry_date:
                document.expiry_date = renewal.new_expiry_date
            # Recalculate status
            document.status = (
                Document.Status.ACTIVE
                if document.expiry_date >= timezone.localdate()
                else Document.Status.EXPIRED
            )
            document.save()
            return redirect('document_list')
    else:
        form = RenewalForm()
    return render(request, 'core/renew_form.html', {'form': form, 'document': document, 'title': 'Perpanjang Dokumen'})


# Exports
@login_required
def export_workers_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="workers.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Nama', 'No Paspor', 'Kewarganegaraan', 'Tanggal Lahir', 'Perusahaan', 'Jabatan', 'Tanggal Mulai'
    ])
    profile = getattr(request.user, 'profile', None)
    qs = Worker.objects.select_related('company').all()
    if profile and profile.role == 'CLIENT' and profile.company_id:
        qs = qs.filter(company_id=profile.company_id)
    for w in qs:
        writer.writerow([
            w.name,
            w.passport_number,
            w.nationality,
            w.birth_date,
            w.company.name if w.company else '',
            w.position,
            w.start_date or '',
        ])
    return response


@login_required
def export_documents_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="documents.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Pekerja', 'Jenis', 'No Dokumen', 'Tanggal Terbit', 'Tanggal Berakhir', 'Status', 'Sisa Hari'
    ])
    profile = getattr(request.user, 'profile', None)
    qs = Document.objects.select_related('worker').all()
    if profile and profile.role == 'CLIENT' and profile.company_id:
        qs = qs.filter(worker__company_id=profile.company_id)
    for d in qs:
        writer.writerow([
            d.worker.name,
            d.type,
            d.document_number,
            d.issue_date,
            d.expiry_date,
            d.status,
            d.days_until_expiry,
        ])
    return response

# Create your views here.
