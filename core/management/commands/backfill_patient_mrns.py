import re

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Patients


class Command(BaseCommand):
    help = 'Backfill MRNs for legacy or invalid patient records.'

    def handle(self, *args, **options):
        mrn_prefix = f"241{timezone.now().strftime('%y%m')}"
        valid_mrns = Patients.objects.filter(mrn__startswith=mrn_prefix)
        existing_suffixes = set()

        for mrn in valid_mrns.values_list('mrn', flat=True):
            suffix = str(mrn)[-4:]
            if suffix.isdigit():
                existing_suffixes.add(int(suffix))

        next_number = max(existing_suffixes, default=0) + 1
        updated = 0
        skipped = 0

        for patient in Patients.objects.order_by('created_at', 'id'):
            current_mrn = patient.mrn or ''
            if re.fullmatch(r'241\d{8}', current_mrn):
                skipped += 1
                continue

            while next_number in existing_suffixes:
                next_number += 1

            patient.mrn = f"{mrn_prefix}{next_number:04d}"
            patient.save(update_fields=['mrn'])
            existing_suffixes.add(next_number)
            next_number += 1
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Backfilled {updated} patient MRNs. Skipped {skipped} patients already using the current format.'
            )
        )
