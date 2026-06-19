from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random

from core.models import (
    Profile, Roles, Patients, Wards, Beds, Visits, Admissions,
    Diagnosis, Treatments, LabResults, Billing, Complaints, Consents
)


class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Starting sample data population...')

        # Create roles
        self.create_roles()
        
        # Create users and profiles
        self.create_users()
        
        # Create wards and beds
        self.create_wards_and_beds()
        
        # Create patients
        self.create_patients()
        
        # Create visits, admissions, and related records
        self.create_visits_and_records()
        
        self.stdout.write(self.style.SUCCESS('Sample data population completed successfully!'))

    def create_roles(self):
        roles = ['admin', 'doctor', 'nurse', 'heo', 'mrc', 'pharmacy', 'lab']
        for role in roles:
            Roles.objects.get_or_create(name=role)
        self.stdout.write('[OK] Roles created')

    def create_users(self):
        users_data = [
            {'username': 'admin', 'password': 'admin123', 'email': 'admin@hospital.com', 'first_name': 'Admin', 'role': 'admin'},
            {'username': 'doctor1', 'password': 'doc123', 'email': 'doctor1@hospital.com', 'first_name': 'Dr. John', 'last_name': 'Smith', 'role': 'doctor'},
            {'username': 'doctor2', 'password': 'doc123', 'email': 'doctor2@hospital.com', 'first_name': 'Dr. Sarah', 'last_name': 'Johnson', 'role': 'doctor'},
            {'username': 'nurse1', 'password': 'nurse123', 'email': 'nurse1@hospital.com', 'first_name': 'Nurse', 'last_name': 'Alice', 'role': 'nurse'},
            {'username': 'nurse2', 'password': 'nurse123', 'email': 'nurse2@hospital.com', 'first_name': 'Nurse', 'last_name': 'Bob', 'role': 'nurse'},
            {'username': 'heo1', 'password': 'heo123', 'email': 'heo1@hospital.com', 'first_name': 'HEO', 'last_name': 'Moyo', 'role': 'heo'},
            {'username': 'mrc1', 'password': 'mrc123', 'email': 'mrc1@hospital.com', 'first_name': 'MRC', 'last_name': 'Clerk', 'role': 'mrc'},
            {'username': 'pharmacist1', 'password': 'pharm123', 'email': 'pharmacist1@hospital.com', 'first_name': 'Pharmacist', 'last_name': 'Mike', 'role': 'pharmacy'},
            {'username': 'lab1', 'password': 'lab123', 'email': 'lab1@hospital.com', 'first_name': 'Lab Tech', 'last_name': 'Emma', 'role': 'lab'},
        ]

        for user_data in users_data:
            username = user_data.pop('username')
            password = user_data.pop('password')
            role = user_data.pop('role')
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': user_data.get('email'), 'first_name': user_data.get('first_name', '')}
            )
            
            # Always set password to ensure it's correct
            user.set_password(password)
            user.save()
            
            Profile.objects.get_or_create(user=user, defaults={'role': role})
        
        self.stdout.write('[OK] Users and profiles created')

    def create_wards_and_beds(self):
        wards_data = [
            {'name': 'General Ward', 'total_beds': 20},
            {'name': 'ICU', 'total_beds': 10},
            {'name': 'Maternity', 'total_beds': 15},
            {'name': 'Pediatric', 'total_beds': 12},
        ]

        for ward_data in wards_data:
            ward, created = Wards.objects.get_or_create(
                name=ward_data['name'],
                defaults={'total_beds': ward_data['total_beds'], 'created_at': timezone.now()}
            )
            
            if created:
                # Create beds for this ward
                for i in range(1, ward_data['total_beds'] + 1):
                    Beds.objects.get_or_create(
                        bed_number=f"{ward_data['name'][:3]}-{i:02d}",
                        ward=ward,
                        defaults={
                            'bed_type': 'Standard' if i % 3 else 'ICU',
                            'status': 'available'
                        }
                    )
        
        self.stdout.write('[OK] Wards and beds created')

    def create_patients(self):
        first_names = ['James', 'Mary', 'Robert', 'Patricia', 'Michael', 'Jennifer', 'William', 'Linda']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
        villages = ['Chitungwiza', 'Harare', 'Bulawayo', 'Mutare', 'Gweru']
        districts = ['Harare', 'Bulawayo', 'Manicaland', 'Midlands', 'Mashonaland']
        current_prefix = f"241{timezone.now().strftime('%y%m')}"

        for i in range(20):
            mrn = f"{current_prefix}{i + 1:04d}"
            patient, created = Patients.objects.get_or_create(
                mrn=mrn,
                defaults={
                    'first_name': random.choice(first_names),
                    'last_name': random.choice(last_names),
                    'gender': random.choice(['M', 'F']),
                    'dob': timezone.now() - timedelta(days=random.randint(18*365, 80*365)),
                    'phone': f"+263772{random.randint(100000, 999999)}",
                    'email': f"patient{i}@email.com",
                    'village': random.choice(villages),
                    'district': random.choice(districts),
                    'address': f"{random.randint(1, 100)} Main Street",
                    'next_of_kin_name': f"Next of Kin {i}",
                    'next_of_kin_phone': f"+263772{random.randint(100000, 999999)}",
                    'marital_status': random.choice(['Single', 'Married', 'Divorced', 'Widowed']),
                    'occupation': random.choice(['Teacher', 'Nurse', 'Engineer', 'Farmer', 'Business']),
                    'religion': random.choice(['Christian', 'Muslim', 'Hindu', 'Jewish']),
                    'insurance_type': random.choice(['NHIMA', 'Private', 'None']),
                }
            )

        self.stdout.write('[OK] Patients created')

    def create_visits_and_records(self):
        patients = Patients.objects.all()[:10]
        # Get doctors from the custom Users model, not Django User
        # For now, just create visits without doctor assignment if Users are empty
        
        for patient in patients:
            # Create 2-3 visits per patient
            for _ in range(random.randint(1, 3)):
                visit_date = timezone.now() - timedelta(days=random.randint(1, 30))
                visit, created = Visits.objects.get_or_create(
                    patient=patient,
                    visit_date=visit_date.date(),
                    visit_time=visit_date.time(),
                    defaults={
                        'visit_type': random.choice(['Outpatient', 'Emergency', 'Follow-up']),
                        'department': random.choice(['General', 'Cardiology', 'Pediatrics', 'Surgery']),
                        'doctor': None,  # Can be filled in later
                        'created_at': timezone.now(),
                    }
                )
                
                if created:
                    # Create complaints
                    Complaints.objects.get_or_create(
                        visit=visit,
                        defaults={
                            'complaint': random.choice(['Fever', 'Headache', 'Body pain', 'Cough']),
                            'symptom_duration': random.choice(['1 day', '3 days', '1 week']),
                            'past_medical_history': 'None documented',
                            'family_history': 'None documented',
                            'current_medication': 'None',
                        }
                    )
                    
                    # Create diagnosis
                    Diagnosis.objects.get_or_create(
                        visit=visit,
                        defaults={
                            'diagnosis': random.choice(['Malaria', 'Flu', 'Hypertension', 'Diabetes']),
                            'findings': 'Clinical assessment completed',
                            'diagnosis_date': visit_date.date(),
                        }
                    )
                    
                    # Create treatment
                    Treatments.objects.get_or_create(
                        visit=visit,
                        defaults={
                            'medication': random.choice(['Aspirin', 'Amoxicillin', 'Metformin']),
                            'dosage': random.choice(['500mg', '1000mg', '2000mg']),
                            'duration': random.choice(['7 days', '14 days', '30 days']),
                            'review_date': (visit_date + timedelta(days=7)).date(),
                        }
                    )
                    
                    # Create billing
                    Billing.objects.get_or_create(
                        patient=patient,
                        visit=visit,
                        defaults={
                            'amount': random.randint(500, 5000),
                            'service': random.choice(['Consultation', 'Tests', 'Medication', 'Procedures']),
                            'payment_type': random.choice(['Cash', 'Insurance', 'Pending']),
                            'billing_date': timezone.now(),
                        }
                    )
                    
                    # Create lab results for some visits
                    if random.random() > 0.5:
                        LabResults.objects.get_or_create(
                            visit=visit,
                            defaults={
                                'test_type': random.choice(['Blood Test', 'Urine Test', 'X-Ray']),
                                'result': 'Awaiting analysis',
                                'result_date': (visit_date + timedelta(days=2)).date(),
                            }
                        )
        
        self.stdout.write('[OK] Visits and related records created')
