from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import Document


class Command(BaseCommand):
    help = 'Kirim reminder dokumen yang akan habis dalam 30/60/90 hari (placeholder: cetak ke stdout)'

    def handle(self, *args, **options):
        today = timezone.localdate()
        d30 = today + timezone.timedelta(days=30)
        d60 = today + timezone.timedelta(days=60)
        d90 = today + timezone.timedelta(days=90)

        qs = Document.objects.select_related('worker', 'worker__company').filter(
            status=Document.Status.ACTIVE,
            expiry_date__gte=today,
            expiry_date__lte=d90,
        ).order_by('expiry_date')

        bucket = {
            '30': qs.filter(expiry_date__lte=d30),
            '60': qs.filter(expiry_date__gt=d30, expiry_date__lte=d60),
            '90': qs.filter(expiry_date__gt=d60, expiry_date__lte=d90),
        }

        for label, docs in bucket.items():
            count = docs.count()
            self.stdout.write(self.style.SUCCESS(f"Reminder {label} hari: {count} dokumen"))
            for d in docs:
                self.stdout.write(
                    f"- {d.worker.company.name} / {d.worker.name} / {d.type} {d.document_number} berakhir {d.expiry_date} ({d.days_until_expiry} hari)"
                )

