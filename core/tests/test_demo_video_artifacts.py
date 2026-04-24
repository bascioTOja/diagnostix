from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from appointments.models import Appointment
from notifications.models import Notification


class DemoVideoArtifactsTests(TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[2]
        self.readme = self.repo_root / "README.md"
        self.final_doc = self.repo_root / "docs" / "finalny-dokument-BL-25.md"
        self.scenario_doc = self.repo_root / "docs" / "demo-video-scenariusz.md"
        self.demo_fixture = self.repo_root / "core" / "fixtures" / "demo_video_seed.json"
        self.plan_stage = self.repo_root / "plan" / "10-demo-video.md"
        self.demo_link = "https://example.com/diagnostix-demo-video"

    def test_demo_artifacts_files_exist_positive(self):
        for file_path in (self.scenario_doc, self.demo_fixture, self.plan_stage):
            self.assertTrue(file_path.exists(), msg=f"Brak pliku: {file_path}")

    def test_demo_fixture_loads_and_contains_required_entities_positive(self):
        call_command("loaddata", "demo_video_seed", verbosity=0)

        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(email="admin.demo@diagnostix.local").exists())
        self.assertTrue(user_model.objects.filter(email="diagnosta.demo@diagnostix.local").exists())
        self.assertTrue(user_model.objects.filter(email="client.demo@diagnostix.local").exists())
        self.assertGreaterEqual(Appointment.objects.count(), 2)
        self.assertGreaterEqual(Notification.objects.count(), 1)

    def test_demo_scenario_contains_required_scenes_and_has_no_placeholders_negative(self):
        content = self.scenario_doc.read_text(encoding="utf-8").lower()

        required_keywords = [
            "rejestracja/logowanie",
            "dodanie pojazdu",
            "rezerwacja badania",
            "sciezka diagnosty",
            "panel admin",
            "powiadomien",
        ]
        for keyword in required_keywords:
            self.assertIn(keyword, content)

        self.assertNotIn("todo", content)
        self.assertNotIn("tbd", content)
        self.assertNotIn("<link>", content)

    def test_demo_link_is_consistent_across_readme_docs_and_plan_positive(self):
        readme_content = self.readme.read_text(encoding="utf-8")
        final_doc_content = self.final_doc.read_text(encoding="utf-8")
        scenario_content = self.scenario_doc.read_text(encoding="utf-8")
        plan_content = self.plan_stage.read_text(encoding="utf-8")

        self.assertIn(self.demo_link, readme_content)
        self.assertIn(self.demo_link, final_doc_content)
        self.assertIn(self.demo_link, scenario_content)
        self.assertIn(self.demo_link, plan_content)

