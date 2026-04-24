from __future__ import annotations

from django.db import connection
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class SmokeCleanSetupTests(TestCase):
    def test_clean_setup_schema_and_login_flow(self):
        table_names = set(connection.introspection.table_names())

        expected_tables = {
            "users_customuser",
            "vehicles_vehicle",
            "appointments_appointment",
            "inspections_inspection",
            "notifications_notification",
        }
        self.assertTrue(expected_tables.issubset(table_names))

        client_api = APIClient()
        register_response = client_api.post(
            "/api/auth/register/",
            {
                "email": "smoke-user@test.com",
                "first_name": "Smoke",
                "last_name": "Tester",
                "password": "secret123",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        login_response = client_api.post(
            "/api/auth/login/",
            {"email": "smoke-user@test.com", "password": "secret123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

