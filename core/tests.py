from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from rest_framework.authtoken.models import Token

from .models import (
    Admissions,
    Billing,
    Beds,
    Consents,
    Deaths,
    Patients,
    Profile,
    Visits,
    Wards,
)


class DashboardFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='doctor1', password='doc123')
        Profile.objects.create(user=self.user, role='doctor')
        self.token = Token.objects.create(user=self.user)

        self.mrc_user = User.objects.create_user(username='mrc1', password='mrc123')
        Profile.objects.create(user=self.mrc_user, role='mrc')
        self.mrc_token = Token.objects.create(user=self.mrc_user)

        self.lab_user = User.objects.create_user(username='lab1', password='lab123')
        Profile.objects.create(user=self.lab_user, role='lab')
        self.lab_token = Token.objects.create(user=self.lab_user)

        self.nurse_user = User.objects.create_user(username='nurse1', password='nurse123')
        Profile.objects.create(user=self.nurse_user, role='nurse')
        self.nurse_token = Token.objects.create(user=self.nurse_user)

        self.patient = Patients.objects.create(
            first_name='Jane',
            last_name='Doe',
            gender='Female',
            dob='1995-02-02',
        )
        self.visit = Visits.objects.create(
            patient=self.patient,
            visit_date='2026-05-01',
            visit_time='10:00:00',
            visit_type='Outpatient',
            department='General',
            status='scheduled',
        )
        self.ward = Wards.objects.create(name='General Ward', total_beds=2)
        self.bed = Beds.objects.create(
            ward=self.ward,
            bed_number='GW-01',
            bed_type='Standard',
            status='available',
        )

    def create_user_with_role(self, username, password, role):
        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=user, role=role)
        token = Token.objects.create(user=user)
        return user, token

    def test_login_page_renders_form_without_auto_redirect(self):
        response = self.client.get('/login/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign In')
        self.assertContains(response, 'id="username"')
        self.assertContains(response, 'id="password"')
        self.assertNotContains(response, 'localStorage.getItem("token")')

    def test_login_redirects_non_admin_users_to_dashboard(self):
        response = self.client.get('/login/')

        self.assertContains(response, 'let destination = "/dashboard/";')
        self.assertContains(response, 'if (role === "pharmacy")')
        self.assertContains(response, 'destination = "/pharmacy/";')
        self.assertContains(response, 'destination = "/lab/";')
        self.assertContains(response, 'encodeURIComponent(token)')
        self.assertNotContains(response, 'window.location.href = "/doctor/?token=" + data.token')
        self.assertNotContains(response, 'window.location.href = "/nurse/?token=" + data.token')
        self.assertNotContains(response, 'window.location.href = "/heo/?token=" + data.token')
        self.assertNotContains(response, 'window.location.href = "/mrc/?token=" + data.token')

    def test_api_dashboard_requires_authentication(self):
        response = self.client.get('/api/dashboard/')

        self.assertEqual(response.status_code, 401)

    def test_api_dashboard_returns_json_for_valid_token(self):
        response = self.client.get(
            '/api/dashboard/',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('total_patients', response.json())
        self.assertIn('total_beds', response.json())
        self.assertIn('pending_billing', response.json())

    def test_dashboard_page_renders_with_token(self):
        response = self.client.get(f'/dashboard/?token={self.token.key}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'dashboard')

    def test_dashboard_page_shows_full_dashboard_sections(self):
        response = self.client.get(f'/dashboard/?token={self.token.key}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff schedules')
        self.assertContains(response, 'Quick Access')
        self.assertContains(response, 'Inpatients by ward')

    def test_dashboard_page_links_to_all_major_pages(self):
        response = self.client.get(f'/dashboard/?token={self.token.key}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/patients/"')
        self.assertContains(response, 'href="/visits/"')
        self.assertContains(response, 'href="/admissions/"')
        self.assertContains(response, 'href="/billing/"')
        self.assertContains(response, 'href="/wards/"')
        self.assertContains(response, 'href="/consents/"')
        self.assertContains(response, 'href="/pharmacy/"')
        self.assertContains(response, 'href="/lab/"')
        self.assertContains(response, 'href="/users/"')
        self.assertContains(response, 'href="/admin-dashboard/"')
        self.assertContains(response, 'href="/doctor/"')
        self.assertContains(response, 'href="/nurse/"')
        self.assertContains(response, 'href="/heo/"')
        self.assertContains(response, 'href="/mrc/"')

    def test_users_page_renders(self):
        response = self.client.get('/users/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff/User Management')
        self.assertContains(response, 'Add User')

    def test_api_dashboard_returns_daily_totals(self):
        Visits.objects.create(
            patient=self.patient,
            visit_date=timezone.localdate(),
            visit_time='09:15:00',
            visit_type='Outpatient',
            department='General',
            status='scheduled',
        )
        Admissions.objects.create(
            patient=self.patient,
            ward=self.ward,
            bed=self.bed,
            admission_date=timezone.now(),
            reason='Observation',
            status='admitted',
        )

        response = self.client.get(
            '/api/dashboard/',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['daily_visits'], 1)
        self.assertEqual(response.json()['daily_admissions'], 1)

    def test_admin_dashboard_page_does_not_call_invalid_api_endpoint(self):
        _, admin_token = self.create_user_with_role('admin2', 'admin123', 'admin')

        response = self.client.get(f'/admin-dashboard/?token={admin_token.key}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome Admin')
        self.assertNotContains(response, '/api/admin-dashboard/')

    def test_patient_creation_requires_authentication(self):
        response = self.client.post(
            '/api/patients/',
            data={
                'first_name': 'Jane',
                'last_name': 'Doe',
                'gender': 'Female',
                'dob': '1995-02-02',
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)

    def test_patient_mrn_is_generated_on_create(self):
        response = self.client.post(
            '/api/patients/',
            data={
                'first_name': 'Jane',
                'last_name': 'Doe',
                'gender': 'Female',
                'dob': '1995-02-02',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.mrc_token.key}',
        )

        self.assertEqual(response.status_code, 201)
        patient = Patients.objects.get(id=response.json()['id'])
        self.assertTrue(patient.mrn)
        self.assertRegex(patient.mrn, r'^241\d{4}\d{4}$')

    def test_patient_mrn_increments_for_each_new_registration(self):
        first_suffix = int(self.patient.mrn[-4:])

        response = self.client.post(
            '/api/patients/',
            data={
                'first_name': 'Alice',
                'last_name': 'Smith',
                'gender': 'Female',
                'dob': '1990-08-08',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.mrc_token.key}',
        )

        self.assertEqual(response.status_code, 201)
        new_patient = Patients.objects.get(id=response.json()['id'])
        self.assertEqual(int(new_patient.mrn[-4:]), first_suffix + 1)

    def test_patient_directory_lists_newest_records_first(self):
        newest_patient = None
        for idx in range(25):
            newest_patient = Patients.objects.create(
                first_name=f'Queue{idx}',
                last_name='Patient',
                gender='Female',
                dob='1990-01-01',
            )

        response = self.client.get(
            '/api/patients/',
            HTTP_AUTHORIZATION=f'Token {self.mrc_token.key}',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        results = payload.get('results', payload)
        self.assertTrue(results)
        self.assertEqual(results[0]['id'], newest_patient.id)

    def test_backfill_patient_mrns_command_updates_legacy_values(self):
        self.patient.mrn = 'LEGACY-SETUP'
        self.patient.save(update_fields=['mrn'])

        first_patient = Patients.objects.create(
            first_name='Legacy',
            last_name='One',
            gender='Female',
            dob='1988-02-02',
            mrn='LEGACY-ONE',
        )
        second_patient = Patients.objects.create(
            first_name='Legacy',
            last_name='Two',
            gender='Male',
            dob='1978-02-02',
            mrn='LEGACY-TWO',
        )

        call_command('backfill_patient_mrns')

        self.patient.refresh_from_db()
        first_patient.refresh_from_db()
        second_patient.refresh_from_db()

        prefix = f"241{timezone.now().strftime('%y%m')}"
        self.assertRegex(self.patient.mrn, rf'^{prefix}\d{{4}}$')
        self.assertRegex(first_patient.mrn, rf'^{prefix}\d{{4}}$')
        self.assertRegex(second_patient.mrn, rf'^{prefix}\d{{4}}$')
        self.assertEqual(self.patient.mrn[-4:], '0001')
        self.assertEqual(first_patient.mrn[-4:], '0002')
        self.assertEqual(second_patient.mrn[-4:], '0003')

    def test_doctor_can_create_complaint(self):
        response = self.client.post(
            '/api/complaints/',
            data={
                'visit': self.visit.id,
                'complaint': 'Headache',
                'symptom_duration': '2 days',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 201)

    def test_doctor_cannot_create_lab_result(self):
        response = self.client.post(
            '/api/lab-results/',
            data={
                'visit': self.visit.id,
                'test_type': 'Blood',
                'result': 'Normal',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 403)

    def test_lab_technician_can_create_lab_result(self):
        response = self.client.post(
            '/api/lab-results/',
            data={
                'visit': self.visit.id,
                'test_type': 'Blood',
                'result': 'Normal',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.lab_token.key}',
        )

        self.assertEqual(response.status_code, 201)

    def test_mrc_can_create_diagnosis(self):
        response = self.client.post(
            '/api/diagnosis/',
            data={
                'visit': self.visit.id,
                'diagnosis': 'Viral infection',
                'findings': 'Mild fever and fatigue',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.mrc_token.key}',
        )

        self.assertEqual(response.status_code, 201)

    def test_nurse_can_create_treatment(self):
        response = self.client.post(
            '/api/treatments/',
            data={
                'visit': self.visit.id,
                'medication': 'Paracetamol',
                'dosage': '500mg',
                'instructions': 'Take twice daily',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.nurse_token.key}',
        )

        self.assertEqual(response.status_code, 201)

    def test_mrc_can_create_admission(self):
        response = self.client.post(
            '/api/admissions/',
            data={
                'patient': self.patient.id,
                'ward': self.ward.id,
                'bed': self.bed.id,
                'admission_date': '2026-05-02',
                'reason': 'Chest pain',
                'status': 'admitted',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.mrc_token.key}',
        )

        self.assertEqual(response.status_code, 201)
        self.bed.refresh_from_db()
        self.assertEqual(self.bed.status, 'occupied')

    def test_doctor_cannot_create_admission(self):
        response = self.client.post(
            '/api/admissions/',
            data={
                'patient': self.patient.id,
                'ward': self.ward.id,
                'bed': self.bed.id,
                'admission_date': '2026-05-02',
                'reason': 'Chest pain',
                'status': 'admitted',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_can_view_admissions(self):
        Admissions = __import__('core.models', fromlist=['Admissions']).Admissions
        Admissions.objects.create(
            patient=self.patient,
            ward=self.ward,
            bed=self.bed,
            admission_date='2026-05-02',
            reason='Chest pain',
            status='admitted',
        )

        response = self.client.get(
            '/api/admissions/',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 200)

    def test_mrc_can_create_billing(self):
        response = self.client.post(
            '/api/billing/',
            data={
                'patient': self.patient.id,
                'visit': self.visit.id,
                'amount': '2500.00',
                'service': 'Consultation',
                'payment_type': 'Cash',
                'billing_date': '2026-05-02T10:00:00Z',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.mrc_token.key}',
        )

        self.assertEqual(response.status_code, 201)

    def test_doctor_cannot_create_billing(self):
        response = self.client.post(
            '/api/billing/',
            data={
                'patient': self.patient.id,
                'visit': self.visit.id,
                'amount': '2500.00',
                'service': 'Consultation',
                'payment_type': 'Cash',
                'billing_date': '2026-05-02T10:00:00Z',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 403)

    def test_nurse_can_create_consent(self):
        response = self.client.post(
            '/api/consents/',
            data={
                'patient': self.patient.id,
                'consent_text': 'Consent for treatment',
                'signed': True,
                'signed_date': '2026-05-02T10:00:00Z',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.nurse_token.key}',
        )

        self.assertEqual(response.status_code, 201)

    def test_authenticated_user_can_view_consents(self):
        Consents.objects.create(
            patient=self.patient,
            consent_text='Consent for treatment',
            signed=True,
            signed_date='2026-05-02T10:00:00Z',
        )

        response = self.client.get(
            '/api/consents/',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 200)

    def test_admissions_page_renders(self):
        response = self.client.get('/admissions/')

        self.assertEqual(response.status_code, 200)

    def test_billing_page_renders(self):
        response = self.client.get('/billing/')

        self.assertEqual(response.status_code, 200)

    def test_wards_page_renders(self):
        response = self.client.get('/wards/')

        self.assertEqual(response.status_code, 200)

    def test_consents_page_renders(self):
        response = self.client.get('/consents/')

        self.assertEqual(response.status_code, 200)

    def test_legacy_patient_and_bed_pages_render(self):
        patients_response = self.client.get('/patients/')
        beds_response = self.client.get('/beds/')

        self.assertEqual(patients_response.status_code, 200)
        self.assertContains(patients_response, 'Patients')
        self.assertContains(patients_response, 'Search patients')

        self.assertEqual(beds_response.status_code, 200)
        self.assertContains(beds_response, 'Beds Management')
        self.assertContains(beds_response, 'Load bed overview')

    def test_add_and_edit_patient_pages_render(self):
        add_response = self.client.get('/add-patient/')
        edit_response = self.client.get('/edit-patient/')

        self.assertEqual(add_response.status_code, 200)
        self.assertContains(add_response, 'Register Patient')

        self.assertEqual(edit_response.status_code, 200)
        self.assertContains(edit_response, 'Edit Patient')

    def test_api_dashboard_returns_ward_availability_summary(self):
        surgical_ward = Wards.objects.create(name='Surgical Ward', total_beds=2)
        Beds.objects.create(
            ward=surgical_ward,
            bed_number='SW-01',
            bed_type='adult',
            status='available',
        )
        Beds.objects.create(
            ward=surgical_ward,
            bed_number='SW-02',
            bed_type='child',
            status='occupied',
        )

        response = self.client.get(
            '/api/dashboard/',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('ward_availability', response.json())
        ward_summary = next(
            ward for ward in response.json()['ward_availability'] if ward['ward_name'] == 'Surgical Ward'
        )
        self.assertEqual(ward_summary['total_beds'], 2)
        self.assertEqual(ward_summary['available_beds'], 1)
        self.assertEqual(ward_summary['occupied_beds'], 1)
        self.assertIn('adult', ward_summary['bed_types'])
        self.assertIn('child', ward_summary['bed_types'])

    def test_nurse_can_mark_bed_available_when_patient_dies(self):
        admission = Admissions.objects.create(
            patient=self.patient,
            ward=self.ward,
            bed=self.bed,
            admission_date='2026-05-02',
            reason='Chest pain',
            status='admitted',
        )

        response = self.client.post(
            '/api/deaths/',
            data={
                'patient': self.patient.id,
                'cause': 'Cardiac arrest',
                'death_date': '2026-05-03T10:00:00Z',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.nurse_token.key}',
        )

        self.assertEqual(response.status_code, 201)
        self.bed.refresh_from_db()
        self.assertEqual(self.bed.status, 'available')
        admission.refresh_from_db()
        self.assertEqual(admission.status, 'discharged')

    def test_admin_can_manage_users_and_view_activity(self):
        admin_user, admin_token = self.create_user_with_role('admin2', 'admin123', 'admin')

        create_response = self.client.post(
            '/api/admin/users/',
            data={
                'username': 'newstaff',
                'email': 'newstaff@example.com',
                'password': 'newstaff123',
                'first_name': 'New',
                'last_name': 'Staff',
                'role': 'nurse',
                'is_active': True,
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {admin_token.key}',
        )

        self.assertEqual(create_response.status_code, 201)
        created_id = create_response.json()['id']

        update_response = self.client.put(
            f'/api/admin/users/{created_id}/',
            data={
                'username': 'newstaff',
                'email': 'newstaff@example.com',
                'first_name': 'New',
                'last_name': 'Staff',
                'role': 'doctor',
                'is_active': True,
                'password': '',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {admin_token.key}',
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()['role'], 'doctor')

        delete_response = self.client.delete(
            f'/api/admin/users/{created_id}/',
            HTTP_AUTHORIZATION=f'Token {admin_token.key}',
        )

        self.assertEqual(delete_response.status_code, 204)

        activity_response = self.client.get(
            '/api/admin/activity/',
            HTTP_AUTHORIZATION=f'Token {admin_token.key}',
        )

        self.assertEqual(activity_response.status_code, 200)
        self.assertTrue(len(activity_response.json()) >= 1)
