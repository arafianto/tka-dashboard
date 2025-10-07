from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Company(models.Model):
    name = models.CharField("Nama", max_length=255)
    industry = models.CharField("Industri", max_length=255, blank=True)
    address = models.TextField("Alamat", blank=True)
    contact_person = models.CharField("Kontak person", max_length=255, blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Perusahaan"
        verbose_name_plural = "Perusahaan"


class Worker(models.Model):
    name = models.CharField("Nama", max_length=255)
    passport_number = models.CharField("Nomor paspor", max_length=50, unique=True)
    nationality = models.CharField("Kewarganegaraan", max_length=100)
    birth_date = models.DateField("Tanggal lahir")
    company = models.ForeignKey(Company, verbose_name="Perusahaan", on_delete=models.CASCADE, related_name='workers')
    position = models.CharField("Jabatan", max_length=255)
    photo = models.ImageField("Foto", upload_to='workers/photos/', blank=True, null=True)
    start_date = models.DateField("Tanggal mulai kerja", null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.passport_number})"

    class Meta:
        verbose_name = "Pekerja"
        verbose_name_plural = "Pekerja"


class Document(models.Model):
    class DocumentType(models.TextChoices):
        RPTKA = 'RPTKA', 'RPTKA'
        IMTA = 'IMTA', 'IMTA/Notifikasi'
        VISA = 'VISA', 'Visa'
        KITAS = 'KITAS', 'KITAS'
        SKTT = 'SKTT', 'SKTT'
        PASSPORT = 'PASSPORT', 'Paspor'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Aktif'
        EXPIRED = 'EXPIRED', 'Kedaluwarsa'

    worker = models.ForeignKey(Worker, verbose_name="Pekerja", on_delete=models.CASCADE, related_name='documents')
    type = models.CharField("Jenis", max_length=20, choices=DocumentType.choices)
    document_number = models.CharField("Nomor dokumen", max_length=100)
    issue_date = models.DateField("Tanggal terbit")
    expiry_date = models.DateField("Tanggal berakhir")
    status = models.CharField("Status", max_length=20, choices=Status.choices, default=Status.ACTIVE)

    def __str__(self) -> str:
        return f"{self.type} - {self.document_number} ({self.worker.name})"

    @property
    def days_until_expiry(self) -> int:
        return (self.expiry_date - timezone.localdate()).days

    def is_expiring_in_days(self, days: int) -> bool:
        return 0 <= self.days_until_expiry <= days

    class Meta:
        verbose_name = "Dokumen"
        verbose_name_plural = "Dokumen"


class RenewalHistory(models.Model):
    class ProcessStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Disetujui'
        COMPLETED = 'COMPLETED', 'Selesai'

    document = models.ForeignKey(Document, verbose_name="Dokumen", on_delete=models.CASCADE, related_name='renewal_history')
    submission_date = models.DateField("Tanggal pengajuan", default=timezone.localdate)
    process_status = models.CharField("Status proses", max_length=20, choices=ProcessStatus.choices, default=ProcessStatus.PENDING)
    notes = models.TextField("Catatan", blank=True)

    # Snapshot of new data applied during renewal
    new_document_number = models.CharField("Nomor dokumen baru", max_length=100, blank=True)
    new_issue_date = models.DateField("Tanggal terbit baru", null=True, blank=True)
    new_expiry_date = models.DateField("Tanggal berakhir baru", null=True, blank=True)

    def __str__(self) -> str:
        return f"Perpanjangan {self.document} pada {self.submission_date}"

    class Meta:
        verbose_name = "Riwayat Perpanjangan"
        verbose_name_plural = "Riwayat Perpanjangan"


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin Perusahaan'
        CLIENT = 'CLIENT', 'Klien'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField("Peran", max_length=20, choices=Role.choices, default=Role.ADMIN)
    company = models.ForeignKey(Company, verbose_name="Perusahaan", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user.username} - {self.role}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

# Create your models here.
