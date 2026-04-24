from django.urls import path

from core.tests.views import AdminOnlyView, ClientResourceView, DiagnostaAssignmentView


urlpatterns = [
    path("rbac/admin-only/", AdminOnlyView.as_view(), name="rbac-admin-only"),
    path("rbac/client-resource/<int:owner_id>/", ClientResourceView.as_view(), name="rbac-client-resource"),
    path("rbac/diagnosta-assignment/<int:diagnosta_id>/", DiagnostaAssignmentView.as_view(), name="rbac-diagnosta-assignment"),
]

