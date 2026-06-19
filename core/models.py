

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('heo', 'HEO'),
        ('nurse', 'Nurse'),
        ('mrc', 'MRC'),
        ('pharmacy', 'Pharmacist'),
        ('lab', 'Pathologist'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


class UserActivity(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='targeted_activities'
    )
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Admissions(models.Model):
    patient = models.ForeignKey('Patients', models.DO_NOTHING, blank=True, null=True)
    visit = models.ForeignKey('Visits', models.DO_NOTHING, blank=True, null=True)
    ward = models.ForeignKey('Wards', models.DO_NOTHING, blank=True, null=True)
    bed = models.ForeignKey('Beds', models.DO_NOTHING, blank=True, null=True)
    admission_date = models.DateTimeField(blank=True, null=True)
    discharge_date = models.DateTimeField(blank=True, null=True)
    attending_doctor = models.ForeignKey('Users', models.DO_NOTHING, db_column='attending_doctor', blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'admissions'


class Beds(models.Model):
    ward = models.ForeignKey('Wards', models.DO_NOTHING, blank=True, null=True)
    bed_number = models.CharField(max_length=10, blank=True, null=True)
    bed_type = models.CharField(max_length=20, blank=True, null=True)

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True)

    class Meta:
        db_table = 'beds'


class Billing(models.Model):
    patient = models.ForeignKey('Patients', models.DO_NOTHING, blank=True, null=True)
    visit = models.ForeignKey('Visits', models.DO_NOTHING, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    service = models.CharField(max_length=100, blank=True, null=True)
    payment_type = models.CharField(max_length=50, blank=True, null=True)
    billing_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'billing'


class Complaints(models.Model):
    visit = models.ForeignKey('Visits', models.DO_NOTHING, blank=True, null=True)
    complaint = models.TextField(blank=True, null=True)
    history = models.TextField(blank=True, null=True)
    symptom_duration = models.CharField(max_length=50, blank=True, null=True)
    past_medical_history = models.TextField(blank=True, null=True)
    family_history = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    current_medication = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'complaints'


class Consents(models.Model):
    patient = models.ForeignKey('Patients', models.DO_NOTHING, blank=True, null=True)
    consent_text = models.TextField(blank=True, null=True)
    signed = models.BooleanField(blank=True, null=True)
    signed_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'consents'


class Deaths(models.Model):
    patient = models.ForeignKey('Patients', models.DO_NOTHING, blank=True, null=True)
    cause = models.TextField(blank=True, null=True)
    death_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'deaths'


class Diagnosis(models.Model):
    visit = models.ForeignKey('Visits', models.DO_NOTHING, blank=True, null=True)
    findings = models.TextField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    diagnosis_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'diagnosis'


class LabResults(models.Model):
    visit = models.ForeignKey('Visits', models.DO_NOTHING, blank=True, null=True)
    test_type = models.CharField(max_length=100, blank=True, null=True)
    result = models.TextField(blank=True, null=True)
    result_date = models.DateField(blank=True, null=True)
    entered_by = models.ForeignKey('Users', models.DO_NOTHING, db_column='entered_by', blank=True, null=True)

    class Meta:
        db_table = 'lab_results'


class Patients(models.Model):
    mrn = models.CharField(unique=True, max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    next_of_kin_name = models.CharField(max_length=100, blank=True, null=True)
    next_of_kin_phone = models.CharField(max_length=20, blank=True, null=True)
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    religion = models.CharField(max_length=50, blank=True, null=True)
    insurance_type = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_mrn(self):
        current_timestamp = timezone.now()
        mrn_prefix = f"241{current_timestamp.strftime('%y%m')}"
        next_number = 1

        latest_patient = Patients.objects.filter(mrn__startswith=mrn_prefix).order_by('mrn').last()
        if latest_patient and latest_patient.mrn:
            try:
                next_number = int(latest_patient.mrn[-4:]) + 1
            except (TypeError, ValueError):
                next_number = 1

        while Patients.objects.filter(mrn=f"{mrn_prefix}{next_number:04d}").exists():
            next_number += 1

        return f"{mrn_prefix}{next_number:04d}"

    def save(self, *args, **kwargs):
        if not self.mrn:
            self.mrn = self.generate_mrn()
        return super().save(*args, **kwargs)

    class Meta:
        db_table = 'patients'


class Roles(models.Model):
    name = models.CharField(unique=True, max_length=50)

    class Meta:
        db_table = 'roles'


class Treatments(models.Model):
    visit = models.ForeignKey('Visits', models.DO_NOTHING, blank=True, null=True)
    medication = models.CharField(max_length=100, blank=True, null=True)
    dosage = models.CharField(max_length=50, blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    review_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'treatments'


class Users(models.Model):
    full_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(unique=True, max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        default='active',
    )
    password = models.TextField()
    role = models.ForeignKey(Roles, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'users'


class Visits(models.Model):
    patient = models.ForeignKey(Patients, models.DO_NOTHING, blank=True, null=True)
    visit_date = models.DateField(blank=True, null=True)
    visit_time = models.TimeField(blank=True, null=True)
    visit_type = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    doctor = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='scheduled')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'visits'


class Wards(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    total_beds = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'wards'


