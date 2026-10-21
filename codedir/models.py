from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class CourseCatalogItem:
    course_number: str
    course_name: str
    assignment_spec: str
    available_semesters: list[str] = field(default_factory=list)
    assignment_names: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        if self.course_number:
            return f"{self.course_number} - {self.course_name}"
        return self.course_name


@dataclass(slots=True)
class AssignmentMeta:
    sheet_name: str
    match_title: str = ""
    prompt: str = ""
    prompt_summary: str = ""
    existing_semesters: list[str] = field(default_factory=list)
    response_count: int = 0

    @property
    def display_name(self) -> str:
        if self.prompt_summary:
            return f"{self.sheet_name} - {self.prompt_summary}"
        return self.sheet_name


@dataclass(slots=True)
class WorkbookProfile:
    path: Path
    course_name: str
    assignments: list[AssignmentMeta] = field(default_factory=list)
    semester_suggestions: list[str] = field(default_factory=list)

    def assignment_names(self) -> list[str]:
        return [assignment.sheet_name for assignment in self.assignments]

    def assignment_by_name(self, sheet_name: str) -> AssignmentMeta | None:
        for assignment in self.assignments:
            if assignment.sheet_name == sheet_name:
                return assignment
        return None


@dataclass(slots=True)
class ZipImportPreview:
    path: Path
    response_count: int
    detected_assignment: str | None
    detected_semester: str | None
    submission_date: datetime | None
    note: str


@dataclass(slots=True)
class ArchiveImportRequest:
    zip_path: Path
    target_sheet: str
    semester: str


@dataclass(slots=True)
class ImportResult:
    zip_path: Path
    target_sheet: str
    imported_count: int
    created_sheet: bool
    batch_id: str
