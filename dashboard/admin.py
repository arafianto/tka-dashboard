from django.contrib import admin
from .models import Company, Worker, Document, RenewalHistory, UserProfile


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "contact_person")
    search_fields = ("name", "industry", "contact_person")


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ("name", "passport_number", "nationality", "company", "position")
    search_fields = ("name", "passport_number", "nationality", "position", "company__name")
    list_filter = ("company", "nationality")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("type", "document_number", "worker", "issue_date", "expiry_date", "status")
    search_fields = ("document_number", "worker__name", "worker__passport_number")
    list_filter = ("type", "status")


@admin.register(RenewalHistory)
class RenewalHistoryAdmin(admin.ModelAdmin):
    list_display = ("document", "submission_date", "process_status")
    list_filter = ("process_status",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "company")
    list_filter = ("role", "company")

# Register your models here.
