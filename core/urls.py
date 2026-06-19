from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    home, login_view, logout_view, api_dashboard,
    admin_users_list, admin_user_detail, admin_activity_list,
    PatientsViewSet, VisitsViewSet, AdmissionsViewSet, BedsViewSet,
    BillingViewSet, ComplaintsViewSet, ConsentsViewSet, DeathsViewSet,
    DiagnosisViewSet, LabResultsViewSet, RolesViewSet, TreatmentsViewSet,
    UsersViewSet, WardsViewSet, ProfileViewSet
)

router = DefaultRouter()
router.register(r'patients', PatientsViewSet)
router.register(r'visits', VisitsViewSet)
router.register(r'admissions', AdmissionsViewSet)
router.register(r'beds', BedsViewSet)
router.register(r'billing', BillingViewSet)
router.register(r'complaints', ComplaintsViewSet)
router.register(r'consents', ConsentsViewSet)
router.register(r'deaths', DeathsViewSet)
router.register(r'diagnosis', DiagnosisViewSet)
router.register(r'lab-results', LabResultsViewSet)
router.register(r'roles', RolesViewSet)
router.register(r'treatments', TreatmentsViewSet)
router.register(r'users', UsersViewSet)
router.register(r'wards', WardsViewSet)
router.register(r'profiles', ProfileViewSet)

urlpatterns = [
    path('', home),
    path('login/', login_view),
    path('logout/', logout_view),
    path('dashboard/', api_dashboard),
    path('admin/users/', admin_users_list),
    path('admin/users/<int:user_id>/', admin_user_detail),
    path('admin/activity/', admin_activity_list),
    path('', include(router.urls)),
]

# API endpoint note: This is included under 'api/' prefix in main urls.py,
# so the full path is /api/dashboard/









