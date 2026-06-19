import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms.settings')
import django

django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from core.models import Patients, Wards, Beds, Profile

user = User.objects.create_user(username='admissiondebug', password='adm123')
Profile.objects.update_or_create(user=user, defaults={'role': 'mrc'})
token = Token.objects.create(user=user)
patient = Patients.objects.create(first_name='Ada', last_name='Lovelace', gender='Female', dob='1815-12-10')
ward = Wards.objects.create(name='General Ward', total_beds=2)
bed = Beds.objects.create(ward=ward, bed_number='GW-01', bed_type='Standard', status='available')

client = APIClient()
client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
payload = {
    'patient': patient.id,
    'ward': ward.id,
    'bed': bed.id,
    'status': 'admitted',
    'admission_date': '2026-05-26T12:00:00',
    'reason': 'Checkup',
}
response = client.post('/api/admissions/', payload, format='json')
print('status', response.status_code)
print(response.content.decode())
