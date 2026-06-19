from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from core.views import (
    home,
    dashboard,
    patients_page,
    users_page,
    beds_page,
    add_patient_page,
    edit_patient_page,
    patient_details_page,
    visits_page,
    admissions_page,
    billing_page,
    wards_page,
    consents_page,
    admin_dashboard,
    doctor_page,
    nurse_page,
    heo_page,
    mrc_page,
    pharmacy_page,
    lab_page,
)
from django.shortcuts import render


def login_page(request):
    return render(request, 'login.html')


urlpatterns = [
    path('admin/', admin.site.urls),

    # Pages
    path('', home, name='home'),
    path('login/', login_page, name='login_page'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('patients/', patients_page),
    path('users/', users_page),
    path('beds/', beds_page),
    path('add-patient/', add_patient_page),
    path('edit-patient/', edit_patient_page),
    path('patient-details/', patient_details_page),
    path('visits/', visits_page),
    path('admissions/', admissions_page),
    path('billing/', billing_page),
    path('wards/', wards_page),
    path('consents/', consents_page),
    path('admin-dashboard/', admin_dashboard),
    path('doctor/', doctor_page),
    path('nurse/', nurse_page),
    path('heo/', heo_page),
    path('mrc/', mrc_page),
    path('pharmacy/', pharmacy_page),
    path('lab/', lab_page),

    # API routes
    path('api/', include('core.urls')),
]