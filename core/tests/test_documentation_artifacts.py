from __future__ import annotations

from pathlib import Path

from django.test import TestCase


class DocumentationArtifactsTests(TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[2]
        self.readme = self.repo_root / "README.md"
        self.requirements = self.repo_root / "requirements.txt"
        self.doc_md = self.repo_root / "docs" / "finalny-dokument-BL-25.md"
        self.doc_docx = self.repo_root / "docs" / "finalny-dokument-BL-25.docx"

    def test_required_documentation_files_exist_positive(self):
        for file_path in (self.readme, self.requirements, self.doc_md, self.doc_docx):
            self.assertTrue(file_path.exists(), msg=f"Brak pliku: {file_path}")

    def test_readme_contains_required_sections_and_demo_link_positive(self):
        content = self.readme.read_text(encoding="utf-8")

        required_fragments = [
            "# Diagnostix",
            "## Cel projektu",
            "## Architektura aplikacji",
            "## ERD (uproszczony)",
            "## Scenariusze uzytkownika (3 role)",
            "## Uruchomienie na czystym srodowisku",
            "## Demo video",
            "https://example.com/diagnostix-demo-video",
        ]

        for fragment in required_fragments:
            self.assertIn(fragment, content)

    def test_readme_has_no_todo_or_tbd_negative(self):
        content = self.readme.read_text(encoding="utf-8").lower()

        self.assertNotIn("todo", content)
        self.assertNotIn("tbd", content)

    def test_requirements_contains_runtime_dependencies_positive_and_no_placeholders_negative(self):
        content = self.requirements.read_text(encoding="utf-8").lower()

        self.assertIn("django==", content)
        self.assertIn("djangorestframework==", content)
        self.assertIn("celery==", content)
        self.assertNotIn("<version>", content)

