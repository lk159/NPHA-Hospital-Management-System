from rest_framework import serializers
from .models import *


class PatientsSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = data.copy()
            if 'province' in data and 'village' not in data:
                data['village'] = data.pop('province')
            if 'residence' in data and 'address' not in data:
                data['address'] = data.pop('residence')
        return super().to_internal_value(data)

    class Meta:
        model = Patients
        fields = '__all__'


class VisitsSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Visits
        fields = '__all__'

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name or ''} {obj.patient.last_name or ''}".strip()
        return None

    def get_doctor_name(self, obj):
        if obj.doctor:
            return obj.doctor.full_name or obj.doctor.email
        return None


class AdmissionsSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    ward_name = serializers.SerializerMethodField()
    bed_number = serializers.SerializerMethodField()

    class Meta:
        model = Admissions
        fields = '__all__'

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name or ''} {obj.patient.last_name or ''}".strip()
        return None

    def get_ward_name(self, obj):
        if obj.ward:
            return obj.ward.name
        return None

    def get_bed_number(self, obj):
        if obj.bed:
            return obj.bed.bed_number
        return None

    def validate(self, data):
        if not data.get('patient'):
            raise serializers.ValidationError("Patient is required")
        if not data.get('admission_date'):
            raise serializers.ValidationError("Admission date is required")
        return data


class BedsSerializer(serializers.ModelSerializer):
    ward_name = serializers.SerializerMethodField()
    is_occupied = serializers.SerializerMethodField()

    class Meta:
        model = Beds
        fields = '__all__'

    def get_ward_name(self, obj):
        if obj.ward:
            return obj.ward.name
        return None

    def get_is_occupied(self, obj):
        return obj.status == 'occupied'


class BillingSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = Billing
        fields = '__all__'

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name or ''} {obj.patient.last_name or ''}".strip()
        return None


class ComplaintsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaints
        fields = '__all__'


class ConsentsSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = Consents
        fields = '__all__'

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name or ''} {obj.patient.last_name or ''}".strip()
        return None


class DeathsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deaths
        fields = '__all__'


class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = '__all__'


class LabResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResults
        fields = '__all__'


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'


class TreatmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatments
        fields = '__all__'


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}


class WardsSerializer(serializers.ModelSerializer):
    available_beds = serializers.SerializerMethodField()

    class Meta:
        model = Wards
        fields = '__all__'

    def get_available_beds(self, obj):
        return Beds.objects.filter(ward=obj, status='available').count()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'