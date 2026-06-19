from rest_framework.decorators import permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS, AllowAny
from rest_framework.authentication import TokenAuthentication
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    Patients, Visits, Admissions, Beds, Profile, Billing, Complaints,
    Consents, Deaths, Diagnosis, LabResults, Roles, Treatments, Users, Wards,
    UserActivity
)
from .serializers import (
    PatientsSerializer, VisitsSerializer, AdmissionsSerializer, BedsSerializer,
    BillingSerializer, ComplaintsSerializer, ConsentsSerializer, DeathsSerializer,
    DiagnosisSerializer, LabResultsSerializer, RolesSerializer, TreatmentsSerializer,
    UsersSerializer, WardsSerializer, ProfileSerializer
)


# =======================
# PERMISSION CLASSES
# =======================
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            profile = Profile.objects.get(user=request.user)
            return profile.role == 'admin'
        except Profile.DoesNotExist:
            return False


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            profile = Profile.objects.get(user=request.user)
            return profile.role in ['doctor', 'admin']
        except Profile.DoesNotExist:
            return False


class IsNurse(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            profile = Profile.objects.get(user=request.user)
            return profile.role in ['nurse', 'admin']
        except Profile.DoesNotExist:
            return False


class IsPharmacy(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            profile = Profile.objects.get(user=request.user)
            return profile.role in ['pharmacy', 'admin']
        except Profile.DoesNotExist:
            return False


class IsLab(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            profile = Profile.objects.get(user=request.user)
            return profile.role in ['lab', 'admin']
        except Profile.DoesNotExist:
            return False


class RoleBasedWritePermission(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        try:
            profile = Profile.objects.get(user=request.user)
            return profile.role in self.allowed_roles
        except Profile.DoesNotExist:
            return False


class IsMRCOrAdminForWrites(RoleBasedWritePermission):
    allowed_roles = ['mrc', 'admin']


class IsClinicalRecordEditor(RoleBasedWritePermission):
    allowed_roles = ['mrc', 'nurse', 'heo', 'doctor', 'admin']


class IsLabRecordEditor(RoleBasedWritePermission):
    allowed_roles = ['lab', 'admin']


class IsAdmissionEditor(RoleBasedWritePermission):
    allowed_roles = ['mrc', 'nurse', 'admin']


class IsBillingEditor(RoleBasedWritePermission):
    allowed_roles = ['mrc', 'nurse', 'admin']


class IsConsentEditor(RoleBasedWritePermission):
    allowed_roles = ['mrc', 'nurse', 'heo', 'doctor', 'admin']


class IsWardBedEditor(RoleBasedWritePermission):
    allowed_roles = ['mrc', 'nurse', 'doctor', 'admin']


# =======================
# PATIENTS
# =======================
class PatientsViewSet(viewsets.ModelViewSet):
    queryset = Patients.objects.all()
    serializer_class = PatientsSerializer
    permission_classes = [IsMRCOrAdminForWrites]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'phone', 'mrn']
    ordering_fields = ['created_at', 'first_name']

    def get_queryset(self):
        queryset = Patients.objects.all().order_by('-created_at', '-id')
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
                | Q(mrn__icontains=search)
            )
        return queryset

    def destroy(self, request, *args, **kwargs):
        patient = self.get_object()
        patient_visits = Visits.objects.filter(patient=patient)

        with transaction.atomic():
            Complaints.objects.filter(visit__in=patient_visits).delete()
            Diagnosis.objects.filter(visit__in=patient_visits).delete()
            LabResults.objects.filter(visit__in=patient_visits).delete()
            Treatments.objects.filter(visit__in=patient_visits).delete()

            Billing.objects.filter(Q(patient=patient) | Q(visit__in=patient_visits)).delete()
            Admissions.objects.filter(Q(patient=patient) | Q(visit__in=patient_visits)).delete()
            Consents.objects.filter(patient=patient).delete()
            Deaths.objects.filter(patient=patient).delete()

            patient_visits.delete()
            patient.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# =======================
# VISITS
# =======================
class VisitsViewSet(viewsets.ModelViewSet):
    queryset = Visits.objects.all()
    serializer_class = VisitsSerializer
    permission_classes = [IsMRCOrAdminForWrites]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['patient', 'visit_type', 'department', 'status', 'visit_date']
    search_fields = ['patient__first_name', 'patient__last_name', 'department', 'reason']
    ordering_fields = ['visit_date', 'visit_time']


# =======================
# ADMISSIONS
# =======================
class AdmissionsViewSet(viewsets.ModelViewSet):
    queryset = Admissions.objects.all()
    serializer_class = AdmissionsSerializer
    permission_classes = [IsAdmissionEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['patient', 'ward', 'status']
    search_fields = ['patient__first_name', 'patient__last_name', 'reason']

    def _assign_bed(self, data):
        bed_id = data.get('bed')
        ward_id = data.get('ward')

        if bed_id:
            bed = Beds.objects.filter(id=bed_id).first()
            if not bed:
                raise ValueError('Bed not found')
            if bed.status == 'occupied':
                raise ValueError('Selected bed is unavailable')
            if ward_id and int(ward_id) != bed.ward_id:
                raise ValueError('Selected bed does not belong to the selected ward')
            return bed

        if ward_id:
            bed = Beds.objects.filter(ward_id=ward_id, status='available').first()
            if bed:
                return bed

        bed = Beds.objects.filter(status='available').first()
        if not bed:
            raise ValueError('No available beds')
        return bed

    def _mark_bed(self, bed, status):
        if bed:
            bed.status = status
            bed.save(update_fields=['status'])

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        try:
            bed = self._assign_bed(data)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        data['bed'] = bed.id
        if not data.get('ward'):
            data['ward'] = bed.ward_id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self._mark_bed(bed, 'occupied')
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_bed = instance.bed
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        new_bed = serializer.validated_data.get('bed')
        new_bed_id = getattr(new_bed, 'id', None)
        if serializer.validated_data.get('status') == 'discharged':
            if old_bed:
                self._mark_bed(old_bed, 'available')
            return Response(serializer.data)

        if old_bed and new_bed_id and old_bed.id != new_bed_id:
            self._mark_bed(old_bed, 'available')
        if new_bed_id:
            new_bed = Beds.objects.filter(id=new_bed_id).first()
            if new_bed:
                self._mark_bed(new_bed, 'occupied')
        elif old_bed:
            self._mark_bed(old_bed, 'occupied')

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        admission = self.get_object()
        bed = admission.bed
        if bed:
            self._mark_bed(bed, 'available')
        return super().destroy(request, *args, **kwargs)


# =======================
# BEDS
# =======================
class BedsViewSet(viewsets.ModelViewSet):
    queryset = Beds.objects.all()
    serializer_class = BedsSerializer
    permission_classes = [IsWardBedEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['ward', 'status', 'bed_type']
    search_fields = ['bed_number']


# =======================
# BILLING
# =======================
class BillingViewSet(viewsets.ModelViewSet):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    permission_classes = [IsBillingEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['patient', 'payment_type', 'billing_date']
    search_fields = ['patient__first_name', 'patient__last_name', 'service', 'payment_type']
    ordering_fields = ['billing_date', 'amount']


# =======================
# COMPLAINTS
# =======================
class ComplaintsViewSet(viewsets.ModelViewSet):
    queryset = Complaints.objects.all()
    serializer_class = ComplaintsSerializer
    permission_classes = [IsClinicalRecordEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['visit']
    search_fields = ['complaint', 'symptom_duration']


# =======================
# CONSENTS
# =======================
class ConsentsViewSet(viewsets.ModelViewSet):
    queryset = Consents.objects.all()
    serializer_class = ConsentsSerializer
    permission_classes = [IsConsentEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['patient', 'signed']
    search_fields = ['patient__first_name', 'patient__last_name', 'consent_text']


# =======================
# DEATHS
# =======================
class DeathsViewSet(viewsets.ModelViewSet):
    queryset = Deaths.objects.all()
    serializer_class = DeathsSerializer
    permission_classes = [IsWardBedEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['patient']
    search_fields = ['patient__first_name', 'patient__last_name', 'cause']
    ordering_fields = ['death_date']

    def _release_bed_for_patient(self, patient):
        if patient is None:
            return

        active_admission = Admissions.objects.filter(
            patient=patient,
            status='admitted',
        ).select_related('bed').first()

        if not active_admission or not active_admission.bed:
            return

        bed = active_admission.bed
        bed.status = 'available'
        bed.save(update_fields=['status'])

        active_admission.status = 'discharged'
        if not active_admission.discharge_date:
            active_admission.discharge_date = timezone.now()
        active_admission.save(update_fields=['status', 'discharge_date'])

    def perform_create(self, serializer):
        death = serializer.save()
        self._release_bed_for_patient(death.patient)

    def perform_update(self, serializer):
        death = serializer.save()
        self._release_bed_for_patient(death.patient)


# =======================
# DIAGNOSIS
# =======================
class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    permission_classes = [IsClinicalRecordEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['visit']
    search_fields = ['diagnosis', 'findings']


# =======================
# LAB RESULTS
# =======================
class LabResultsViewSet(viewsets.ModelViewSet):
    queryset = LabResults.objects.all()
    serializer_class = LabResultsSerializer
    permission_classes = [IsLabRecordEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['visit', 'test_type']
    search_fields = ['test_type', 'result']
    ordering_fields = ['result_date']


# =======================
# ROLES
# =======================
class RolesViewSet(viewsets.ModelViewSet):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer


# =======================
# TREATMENTS
# =======================
class TreatmentsViewSet(viewsets.ModelViewSet):
    queryset = Treatments.objects.all()
    serializer_class = TreatmentsSerializer
    permission_classes = [IsClinicalRecordEditor]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['visit']
    search_fields = ['medication', 'dosage', 'instructions']


# =======================
# USERS
# =======================
class UsersViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UsersSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['full_name', 'email', 'phone', 'department']
    ordering_fields = ['created_at', 'full_name']

    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get('role')
        status_value = self.request.query_params.get('status')
        if role:
            queryset = queryset.filter(role__name=role)
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset


# =======================
# WARDS
# =======================
class WardsViewSet(viewsets.ModelViewSet):
    queryset = Wards.objects.all()
    serializer_class = WardsSerializer
    permission_classes = [IsWardBedEditor]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['created_at', 'name']


# =======================
# PROFILE
# =======================
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role']


# =======================
# LOGIN API
# =======================
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        token, _ = Token.objects.get_or_create(user=user)
        try:
            profile = Profile.objects.get(user=user)
            UserActivity.objects.create(
                actor=user,
                action='login',
                details=f'{user.username} signed in'
            )
            return Response({
                'token': token.key,
                'role': profile.role,
                'user_id': user.id,
                'username': user.username
            })
        except Profile.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


# =======================
# LOGOUT API
# =======================
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout_view(request):
    UserActivity.objects.create(
        actor=request.user,
        action='logout',
        details=f'{request.user.username} signed out'
    )
    request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


# =======================
# ADMIN MANAGEMENT
# =======================
def _admin_user_payload(user):
    profile = Profile.objects.filter(user=user).first()
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': profile.role if profile else 'unknown',
        'is_active': user.is_active,
    }


def _log_admin_activity(actor, action, details, target_user=None):
    UserActivity.objects.create(
        actor=actor,
        target_user=target_user,
        action=action,
        details=details,
    )


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def admin_users_list(request):
    if request.method == 'GET':
        users = User.objects.all().order_by('username')
        return Response([_admin_user_payload(user) for user in users])

    username = (request.data.get('username') or '').strip()
    email = (request.data.get('email') or '').strip()
    password = request.data.get('password') or ''
    role = (request.data.get('role') or '').strip()
    first_name = (request.data.get('first_name') or '').strip()
    last_name = (request.data.get('last_name') or '').strip()
    is_active = request.data.get('is_active', True)

    valid_roles = {choice[0] for choice in Profile.ROLE_CHOICES}

    if not username or not password or role not in valid_roles:
        return Response({'error': 'Username, password, and a valid role are required'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username__iexact=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    if email and User.objects.filter(email__iexact=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    user.is_active = bool(is_active)
    user.save(update_fields=['is_active'])
    Profile.objects.update_or_create(user=user, defaults={'role': role})

    _log_admin_activity(
        request.user,
        'user_created',
        f'Created user {username}',
        target_user=user,
    )

    return Response(_admin_user_payload(user), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def admin_user_detail(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(_admin_user_payload(user))

    if request.method == 'PUT':
        username = (request.data.get('username') or user.username).strip()
        email = (request.data.get('email') or user.email or '').strip()
        password = request.data.get('password') or ''
        role = (request.data.get('role') or '').strip()
        first_name = (request.data.get('first_name') or user.first_name or '').strip()
        last_name = (request.data.get('last_name') or user.last_name or '').strip()
        is_active = request.data.get('is_active', user.is_active)

        valid_roles = {choice[0] for choice in Profile.ROLE_CHOICES}
        if role and role not in valid_roles:
            return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)

        if username != user.username and User.objects.filter(username__iexact=username).exclude(id=user.id).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        if email and email != user.email and User.objects.filter(email__iexact=email).exclude(id=user.id).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = bool(is_active)
        if password:
            user.set_password(password)
        user.save()

        if role:
            Profile.objects.update_or_create(user=user, defaults={'role': role})

        _log_admin_activity(
            request.user,
            'user_updated',
            f'Updated user {user.username}',
            target_user=user,
        )

        return Response(_admin_user_payload(user))

    username = user.username
    Token.objects.filter(user=user).delete()
    user.delete()
    _log_admin_activity(
        request.user,
        'user_deleted',
        f'Deleted user {username}',
    )
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def admin_activity_list(request):
    activities = UserActivity.objects.select_related('actor', 'target_user').order_by('-created_at')[:50]
    payload = []
    for activity in activities:
        payload.append({
            'id': activity.id,
            'action': activity.action,
            'details': activity.details,
            'created_at': activity.created_at.isoformat(),
            'actor': activity.actor.username if activity.actor else None,
            'target_user': activity.target_user.username if activity.target_user else None,
        })
    return Response(payload)


# =======================
# DASHBOARD API
# =======================
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_dashboard(request):
    total_patients = Patients.objects.count()
    total_beds = Beds.objects.count()
    occupied_beds = Beds.objects.filter(status='occupied').count()
    available_beds = Beds.objects.filter(status='available').count()
    total_admissions = Admissions.objects.count()
    total_visits = Visits.objects.count()
    pending_billing = Billing.objects.count()
    today = timezone.localdate()
    daily_patients = Patients.objects.filter(created_at__date=today).count()
    daily_admissions = Admissions.objects.filter(admission_date__date=today).count()
    daily_visits = Visits.objects.filter(visit_date=today).count()
    daily_billing = Billing.objects.filter(billing_date__date=today).count()

    ward_availability = []
    for ward in Wards.objects.all().order_by('name'):
        ward_beds = Beds.objects.filter(ward=ward)
        bed_types = {
            'adult': ward_beds.filter(bed_type='adult').count(),
            'child': ward_beds.filter(bed_type='child').count(),
            'general': ward_beds.filter(bed_type='general').count(),
            'icu': ward_beds.filter(bed_type='icu').count(),
            'private': ward_beds.filter(bed_type='private').count(),
        }
        ward_availability.append({
            'ward_id': ward.id,
            'ward_name': ward.name,
            'total_beds': ward_beds.count(),
            'available_beds': ward_beds.filter(status='available').count(),
            'occupied_beds': ward_beds.filter(status='occupied').count(),
            'maintenance_beds': ward_beds.filter(status='maintenance').count(),
            'bed_types': bed_types,
        })

    return Response({
        "total_patients": total_patients,
        "total_beds": total_beds,
        "occupied_beds": occupied_beds,
        "available_beds": available_beds,
        "total_admissions": total_admissions,
        "total_visits": total_visits,
        "pending_billing": pending_billing,
        "daily_patients": daily_patients,
        "daily_admissions": daily_admissions,
        "daily_visits": daily_visits,
        "daily_billing": daily_billing,
        "ward_availability": ward_availability,
    })


# =======================
# HOME PAGE
# =======================
def home(request):
    """Render the landing page for the application root."""
    return render(request, 'index.html')


# =======================
# SECURED PAGES - ROLE BASED
# =======================

def _get_user_from_token_param(request):
    # Try query string first (?token=xxx)
    token_key = request.GET.get('token')
    if not token_key:
        # Fallback: try Authorization header (Token xxx)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token '):
            token_key = auth_header[6:]
    if not token_key:
        # Fallback: try cookie
        token_key = request.COOKIES.get('auth_token')

    if not token_key:
        return None

    try:
        token = Token.objects.select_related('user').get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None


def _authorize_role_page(request, allowed_roles):
    user = _get_user_from_token_param(request)
    if user is None:
        return redirect('login_page')

    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return redirect('login_page')

    if profile.role not in allowed_roles:
        return redirect('login_page')

    return None


def dashboard(request):
    """Universal dashboard page for authenticated users or valid token users."""
    if request.user.is_authenticated:
        user = request.user
    else:
        user = _get_user_from_token_param(request)
        if user is None:
            return redirect('login_page')

    profile = Profile.objects.filter(user=user).first()

    context = {
        'user': user,
        'dashboard_username': user.username,
        'dashboard_display_name': user.get_full_name().strip() or user.username,
        'dashboard_user_role': profile.role if profile else 'staff',
    }
    return render(request, 'dashboard.html', context)

def patients_page(request):
    return render(request, 'patients.html')


def users_page(request):
    return render(request, 'users.html')


def beds_page(request):
    return render(request, 'beds.html')


def add_patient_page(request):
    return render(request, 'add_patient.html')


def edit_patient_page(request):
    return render(request, 'edit_patient.html')


def patient_details_page(request):
    return render(request, 'patient_details.html')


def visits_page(request):
    return render(request, 'visits.html')


def admissions_page(request):
    return render(request, 'admissions_management.html')


def billing_page(request):
    return render(request, 'billing_management.html')


def wards_page(request):
    return render(request, 'wards_management.html')


def consents_page(request):
    return render(request, 'consents.html')


def admin_dashboard(request):
    auth_response = _authorize_role_page(request, ['admin'])
    if auth_response is not None:
        return auth_response
    return render(request, 'admin-dashboard.html')


def doctor_page(request):
    auth_response = _authorize_role_page(request, ['doctor', 'admin'])
    if auth_response is not None:
        return auth_response
    return render(request, 'doctor.html')


def nurse_page(request):
    auth_response = _authorize_role_page(request, ['nurse', 'admin'])
    if auth_response is not None:
        return auth_response
    return render(request, 'nurse.html')


def heo_page(request):
    auth_response = _authorize_role_page(request, ['heo', 'admin'])
    if auth_response is not None:
        return auth_response
    return render(request, 'heo.html')


def mrc_page(request):
    auth_response = _authorize_role_page(request, ['mrc', 'admin'])
    if auth_response is not None:
        return auth_response
    return render(request, 'mrc.html')


def pharmacy_page(request):
    auth_response = _authorize_role_page(request, ['pharmacy', 'admin'])
    if auth_response is not None:
        return auth_response
    return render(request, 'pharmacy.html')


def lab_page(request):
    auth_response = _authorize_role_page(request, ['lab', 'admin'])
    if auth_response is not None:
        return auth_response
    return render(request, 'lab.html')