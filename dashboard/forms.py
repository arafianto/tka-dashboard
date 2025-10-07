from django import forms
from .models import Company, Worker, Document, RenewalHistory


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "industry", "address", "contact_person"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nama perusahaan"}),
            "industry": forms.TextInput(attrs={"class": "form-control", "placeholder": "Industri"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Alamat"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control", "placeholder": "Kontak person"}),
        }


class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = [
            "name",
            "passport_number",
            "nationality",
            "birth_date",
            "company",
            "position",
            "photo",
            "start_date",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nama pekerja"}),
            "passport_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nomor paspor"}),
            "nationality": forms.TextInput(attrs={"class": "form-control", "placeholder": "Kewarganegaraan"}),
            "birth_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "company": forms.Select(attrs={"class": "form-select"}),
            "position": forms.TextInput(attrs={"class": "form-control", "placeholder": "Jabatan"}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            "worker",
            "type",
            "document_number",
            "issue_date",
            "expiry_date",
            "status",
        ]
        widgets = {
            "worker": forms.Select(attrs={"class": "form-select"}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "document_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nomor dokumen"}),
            "issue_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "expiry_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class RenewalForm(forms.ModelForm):
    class Meta:
        model = RenewalHistory
        fields = [
            "submission_date",
            "process_status",
            "notes",
            "new_document_number",
            "new_issue_date",
            "new_expiry_date",
        ]
        widgets = {
            "submission_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "process_status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Catatan (opsional)"}),
            "new_document_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nomor dokumen baru"}),
            "new_issue_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "new_expiry_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

