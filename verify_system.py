#!/usr/bin/env python
"""
Hospital Management System - Quick Verification Script
Tests all major components to ensure the system is working correctly.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms.settings')
django.setup()

from core.models import Patients, Visits, Admissions, Beds, Wards, Billing, Profile, User
from django.contrib.auth.models import User as DjangoUser

def print_header(text):
    print("\n" + "="*60)
    print("  " + text)
    print("="*60)

def print_success(text):
    print("[OK] " + text)

def print_error(text):
    print("[ERROR] " + text)

def verify_database():
    print_header("Database Verification")
    try:
        # Check model counts
        patient_count = Patients.objects.count()
        visit_count = Visits.objects.count()
        admission_count = Admissions.objects.count()
        bed_count = Beds.objects.count()
        ward_count = Wards.objects.count()
        billing_count = Billing.objects.count()
        
        print_success("Patients: " + str(patient_count))
        print_success("Visits: " + str(visit_count))
        print_success("Admissions: " + str(admission_count))
        print_success("Beds: " + str(bed_count))
        print_success("Wards: " + str(ward_count))
        print_success("Billing Records: " + str(billing_count))
        
        if patient_count > 0 and bed_count > 0:
            print_success("Database is properly populated with sample data!")
            return True
        else:
            print_error("Sample data not found. Run: python manage.py populate_sample_data")
            return False
    except Exception as e:
        print_error("Database verification failed: " + str(e))
        return False

def verify_authentication():
    print_header("Authentication Verification")
    try:
        # Check for demo users
        admin_user = DjangoUser.objects.filter(username='admin').first()
        doctor_user = DjangoUser.objects.filter(username='doctor1').first()
        nurse_user = DjangoUser.objects.filter(username='nurse1').first()
        
        if admin_user:
            print_success("Admin user exists")
        else:
            print_error("Admin user not found")
        
        if doctor_user:
            print_success("Doctor user exists")
        else:
            print_error("Doctor user not found")
        
        if nurse_user:
            print_success("Nurse user exists")
        else:
            print_error("Nurse user not found")
        
        # Check profiles
        admin_profile = Profile.objects.filter(user__username='admin').first()
        if admin_profile and admin_profile.role == 'admin':
            print_success("Admin profile configured correctly")
        else:
            print_error("Admin profile not configured")
        
        return bool(admin_user and doctor_user and nurse_user and admin_profile)
    except Exception as e:
        print_error("Authentication verification failed: " + str(e))
        return False

def verify_models():
    print_header("Model Verification")
    try:
        models_to_check = [
            ('Patients', Patients),
            ('Visits', Visits),
            ('Admissions', Admissions),
            ('Beds', Beds),
            ('Wards', Wards),
            ('Billing', Billing),
        ]
        
        all_good = True
        for name, model in models_to_check:
            try:
                count = model.objects.count()
                print_success(name + " model is accessible (" + str(count) + " records)")
            except Exception as e:
                print_error(name + " model error: " + str(e))
                all_good = False
        
        return all_good
    except Exception as e:
        print_error("Model verification failed: " + str(e))
        return False

def verify_templates():
    print_header("Template Files Verification")
    
    templates_to_check = [
        'index.html',
        'login.html',
        'base.html',
        'dashboard.html',
        'patients.html',
        'visits.html',
        'admissions.html',
        'billing.html',
        'pharmacy.html',
        'lab.html',
        'wards.html',
        'users.html',
    ]
    
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    
    all_found = True
    for template in templates_to_check:
        path = os.path.join(template_dir, template)
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            print_success(template + " (" + str(file_size) + " bytes)")
        else:
            print_error(template + " not found")
            all_found = False
    
    return all_found

def main():
    print("\n" + "="*60)
    print(" Hospital Management System - System Verification")
    print("="*60)
    
    results = {
        'Database': verify_database(),
        'Authentication': verify_authentication(),
        'Models': verify_models(),
        'Templates': verify_templates(),
    }
    
    print_header("Verification Summary")
    
    for check, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(status + " " + check)
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("  [SUCCESS] System is ready to use!")
        print("  Start the server with: python manage.py runserver")
        print("  Then visit: http://localhost:8000/")
        print("  Login with: admin / admin123")
    else:
        print("  [WARNING] Some checks failed. See details above.")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print_error("Fatal error: " + str(e))
        sys.exit(1)
