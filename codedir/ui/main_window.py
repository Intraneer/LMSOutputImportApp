from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from PySide6.QtCore import Property, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QDragEnterEvent, QDropEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from codedir.models import ArchiveImportRequest, CourseCatalogItem, WorkbookProfile
from codedir.services.catalog import find_catalog_path, load_course_catalog
from codedir.services.importer import ImportService
from codedir.ui.styles import get_stylesheet


class DropZone(QFrame):
    files_dropped = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._dragging = False
        self._icon_color = QColor("#F8FAFC")

        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(220)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(176)

        self.title_label = QLabel("Drop Brightspace ZIP files")
        self.title_label.setObjectName("DropTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("or browse and queue them below")
        self.subtitle_label.setObjectName("DropSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addStretch()

    def is_dragging(self) -> bool:
        return self._dragging

    def set_dragging(self, value: bool) -> None:
        if self._dragging == value:
            return

        self._dragging = value
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    dragging = Property(bool, is_dragging, set_dragging)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._event_has_files(event):
            self.dragging = True
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.dragging = False
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self.dragging = False

        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
            and Path(url.toLocalFile()).suffix.lower() == ".zip"
        ]

        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() // 2
        center_y = 70

        pen = QPen(
            self._icon_color,
            5,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )

        painter.setPen(pen)
        painter.drawLine(center_x, center_y + 18, center_x, center_y - 34)
        painter.drawLine(center_x, center_y - 34, center_x - 17, center_y - 16)
        painter.drawLine(center_x, center_y - 34, center_x + 17, center_y - 16)
        painter.drawRoundedRect(center_x - 45, center_y + 18, 90, 54, 10, 10)

    def _event_has_files(
        self,
        event: QDragEnterEvent | QDropEvent,
    ) -> bool:
        if not event.mimeData().hasUrls():
            return False

        return any(url.isLocalFile() for url in event.mimeData().urls())

    def set_theme(self, theme: str) -> None:
        self._icon_color = QColor("#F8FAFC" if theme == "dark" else "#0F1722")
        self.update()


class MainWindow(QMainWindow):
    PATH_ROLE = Qt.ItemDataRole.UserRole

    def __init__(self) -> None:
        super().__init__()
        self.import_service = ImportService()
        self.catalog_path = find_catalog_path()
        self.catalog_items: list[CourseCatalogItem] = []
        self.workbook_profile: WorkbookProfile | None = None
        self._known_zip_paths: set[Path] = set()
        self.workbooks_dir = self._default_workbooks_root()
        self.theme = "dark"

        self.setWindowTitle("Course Journal")
        self.resize(1180, 820)
        self.setMinimumSize(980, 680)

        self._build_ui()
        self._connect_signals()
        self.drop_zone.set_theme(self.theme)
        self._load_catalog()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 18, 22, 16)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        header_text = QVBoxLayout()
        title = QLabel("Course Journal ")
        title.setObjectName("Title")
        subtitle = QLabel("Automatic Importing and Grading from D2L ZIPs")
        subtitle.setObjectName("Subtitle")
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header_row.addLayout(header_text, 1)

        self.queue_count = QLabel("0 ZIPs queued")
        self.queue_count.setObjectName("Subtitle")
        self.queue_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(self.queue_count)
        layout.addLayout(header_row)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs, 1)

        self.importer_tab = QWidget()
        self.grading_tab = QWidget()
        self.settings_tab = QWidget()
        self.tabs.addTab(self.importer_tab, "Importer")
        self.tabs.addTab(self.grading_tab, "Grading")
        self.tabs.addTab(self.settings_tab, "Settings")

        self._build_importer_tab()
        self._build_grading_tab()
        self._build_settings_tab()
        self.statusBar().showMessage("Ready")

    def _build_importer_tab(self) -> None:
        layout = QVBoxLayout(self.importer_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        selectors = QFrame()
        selectors.setObjectName("Panel")
        selector_layout = QGridLayout(selectors)
        selector_layout.setContentsMargins(16, 14, 16, 14)
        selector_layout.setHorizontalSpacing(12)
        selector_layout.setVerticalSpacing(10)

        self.course_combo = QComboBox()
        self.semester_combo = QComboBox()
        self.semester_combo.setEditable(True)
        self.semester_combo.setToolTip("Fallback semester used only when a ZIP does not include a readable submission date.")
        self.workbook_edit = QLineEdit()
        self.workbook_edit.setPlaceholderText("Stored in selected workbooks folder as <class>workbook.xlsx")
        self.assignment_combo = QComboBox()
        self.assignment_combo.setEditable(True)

        self.browse_workbook_button = QPushButton("Workbook")
        self.browse_workbook_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.open_workbook_button = QPushButton("Open Workbook")
        self.open_workbook_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        self.refresh_workbook_button = QPushButton("Refresh")
        self.refresh_workbook_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.create_sheets_check = QCheckBox("Create missing sheets")
        self.create_sheets_check.setChecked(True)

        self._add_labeled_widget(selector_layout, 0, 0, "Class", self.course_combo)
        self._add_labeled_widget(selector_layout, 0, 1, "Semester Fallback", self.semester_combo)
        self._add_labeled_widget(selector_layout, 1, 0, "Workbook", self.workbook_edit)
        self._add_labeled_widget(selector_layout, 1, 1, "Assignment", self.assignment_combo)
        selector_layout.addWidget(self.browse_workbook_button, 1, 2)
        selector_layout.addWidget(self.open_workbook_button, 1, 3)
        selector_layout.addWidget(self.refresh_workbook_button, 1, 4)
        selector_layout.addWidget(self.create_sheets_check, 2, 0)
        selector_layout.setColumnStretch(0, 2)
        selector_layout.setColumnStretch(1, 2)
        selector_layout.setColumnStretch(2, 0)
        selector_layout.setColumnStretch(3, 0)
        selector_layout.setColumnStretch(4, 0)
        layout.addWidget(selectors)

        self.drop_zone = DropZone()
        layout.addWidget(self.drop_zone, 2)

        table_panel = QFrame()
        table_panel.setObjectName("Panel")
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(10)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ZIP", "Responses", "Assignment", "Semester", "Status"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        table_layout.addWidget(self.table)

        action_row = QHBoxLayout()
        self.browse_zip_button = QPushButton("Add ZIPs")
        self.browse_zip_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.remove_button = QPushButton("Remove")
        self.remove_button.setObjectName("DangerButton")
        self.clear_button = QPushButton("Clear")
        self.import_button = QPushButton("Import")
        self.import_button.setObjectName("PrimaryButton")
        action_row.addWidget(self.browse_zip_button)
        action_row.addWidget(self.remove_button)
        action_row.addWidget(self.clear_button)
        action_row.addStretch(1)
        action_row.addWidget(self.import_button)
        table_layout.addLayout(action_row)

        layout.addWidget(table_panel, 3)

    def _build_grading_tab(self) -> None:
        layout = QVBoxLayout(self.grading_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 18, 20, 18)
        panel_layout.setSpacing(8)

        title = QLabel("Grading")
        title.setObjectName("Title")
        subtitle = QLabel("Reserved for the later grading workflow.")
        subtitle.setObjectName("Subtitle")
        panel_layout.addWidget(title)
        panel_layout.addWidget(subtitle)
        panel_layout.addStretch(1)
        layout.addWidget(panel)

    def _build_settings_tab(self) -> None:
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        folder_panel = QFrame()
        folder_panel.setObjectName("Panel")
        folder_layout = QGridLayout(folder_panel)
        folder_layout.setContentsMargins(16, 14, 16, 14)
        folder_layout.setHorizontalSpacing(12)
        folder_layout.setVerticalSpacing(10)

        self.workbooks_dir_edit = QLineEdit(str(self.workbooks_dir))
        self.workbooks_dir_edit.setPlaceholderText("Folder for generated and selected course workbooks")
        self.browse_workbooks_dir_button = QPushButton("Browse")
        self.browse_workbooks_dir_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.open_workbooks_dir_button = QPushButton("Open Workbooks Folder")
        self.open_workbooks_dir_button.setObjectName("PrimaryButton")
        self.generate_all_workbooks_button = QPushButton("Generate All Workbooks")
        self.advanced_metadata_check = QCheckBox("Advanced metadata")
        self.advanced_metadata_check.setChecked(True)
        self.dark_mode_check = QCheckBox("Dark mode")
        self.dark_mode_check.setChecked(True)

        self._add_labeled_widget(folder_layout, 0, 0, "Workbooks Folder", self.workbooks_dir_edit)
        folder_layout.addWidget(self.browse_workbooks_dir_button, 0, 1)
        folder_layout.addWidget(self.open_workbooks_dir_button, 0, 2)
        folder_layout.addWidget(self.generate_all_workbooks_button, 1, 2)
        folder_layout.addWidget(self.advanced_metadata_check, 1, 0)
        folder_layout.addWidget(self.dark_mode_check, 1, 1)
        folder_layout.setColumnStretch(0, 1)
        layout.addWidget(folder_panel)
        layout.addStretch(1)

    def _add_labeled_widget(self, layout: QGridLayout, row: int, column: int, label: str, widget: QWidget) -> None:
        wrapper = QVBoxLayout()
        wrapper.setSpacing(5)
        field_label = QLabel(label)
        field_label.setObjectName("FieldLabel")
        wrapper.addWidget(field_label)
        wrapper.addWidget(widget)
        layout.addLayout(wrapper, row, column)

    def _connect_signals(self) -> None:
        self.course_combo.currentIndexChanged.connect(self._course_changed)
        self.browse_workbook_button.clicked.connect(self._browse_workbook)
        self.open_workbook_button.clicked.connect(self._open_workbook)
        self.refresh_workbook_button.clicked.connect(self._inspect_workbook)
        self.workbook_edit.editingFinished.connect(self._inspect_workbook)
        self.drop_zone.files_dropped.connect(self._add_zip_paths)
        self.browse_zip_button.clicked.connect(self._browse_zips)
        self.remove_button.clicked.connect(self._remove_selected_rows)
        self.clear_button.clicked.connect(self._clear_queue)
        self.import_button.clicked.connect(self._import_queue)
        self.browse_workbooks_dir_button.clicked.connect(self._browse_workbooks_dir)
        self.open_workbooks_dir_button.clicked.connect(self._open_workbooks_dir)
        self.generate_all_workbooks_button.clicked.connect(self._generate_all_workbooks)
        self.workbooks_dir_edit.editingFinished.connect(self._apply_workbooks_dir_from_edit)
        self.dark_mode_check.toggled.connect(self._toggle_theme)

    def _load_catalog(self) -> None:
        self.catalog_items = []
        if self.catalog_path and self.catalog_path.exists():
            try:
                self.catalog_items = load_course_catalog(self.catalog_path)
                self.statusBar().showMessage(f"Loaded catalog: {self.catalog_path.name}")
            except Exception as exc:
                self.statusBar().showMessage("Catalog could not be loaded")
                QMessageBox.warning(self, "Catalog Error", str(exc))

        self.course_combo.blockSignals(True)
        self.course_combo.clear()
        for item in self.catalog_items:
            self.course_combo.addItem(item.display_name, item)
        self.course_combo.blockSignals(False)

        if self.catalog_items:
            self.course_combo.setCurrentIndex(0)
            self._course_changed()
        else:
            self.assignment_combo.addItems(["Assignment 1"])

    def _course_changed(self) -> None:
        self._clear_queue(silent=True)
        course = self._current_course()
        self._populate_semesters(course)

        guessed = self._guess_workbook_path(course)
        if guessed:
            self.workbook_edit.setText(str(guessed))
            if guessed.exists():
                self._inspect_workbook(show_errors=False)
            else:
                self.workbook_profile = None
                self.statusBar().showMessage("Workbook will be created in the selected workbooks folder on first import")
                self._populate_assignment_choices()
        else:
            self.workbook_profile = None
            self._populate_assignment_choices()

    def _populate_semesters(self, course: CourseCatalogItem | None) -> None:
        current = self.semester_combo.currentText().strip()
        values: list[str] = []
        if course:
            values.extend(course.available_semesters)
        if self.workbook_profile:
            values.extend(self.workbook_profile.semester_suggestions)
        values.extend(self.import_service._default_semester_suggestions([]))

        self.semester_combo.blockSignals(True)
        self.semester_combo.clear()
        for value in dict.fromkeys(v for v in values if v):
            self.semester_combo.addItem(value)
        if current:
            self.semester_combo.setCurrentText(current)
        elif self.semester_combo.count():
            self.semester_combo.setCurrentIndex(self.semester_combo.count() - 1)
        self.semester_combo.blockSignals(False)

    def _populate_assignment_choices(self) -> None:
        current = self.assignment_combo.currentText().strip()
        values: list[str] = []
        if self.workbook_profile and self.workbook_profile.assignments:
            values.extend(self.workbook_profile.assignment_names())
        else:
            course = self._current_course()
            if course:
                values.extend(course.assignment_names)
        if not values:
            course = self._current_course()
            if course:
                values.extend(course.assignment_names)
        if not values:
            values = ["Assignment 1"]

        self.assignment_combo.blockSignals(True)
        self.assignment_combo.clear()
        for value in dict.fromkeys(v for v in values if v):
            self.assignment_combo.addItem(value)
        if current and current in values:
            self.assignment_combo.setCurrentText(current)
        self.assignment_combo.blockSignals(False)

    def _browse_workbook(self) -> None:
        start_dir = str(self._workbooks_root())
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Course Workbook",
            start_dir,
            "Excel Workbooks (*.xlsx)",
        )
        if path:
            self.workbook_edit.setText(path)
            self._inspect_workbook()

    def _browse_zips(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Brightspace ZIP Exports",
            str(self._work_root()),
            "ZIP Archives (*.zip)",
        )
        self._add_zip_paths([Path(path) for path in paths])

    def _inspect_workbook(self, show_errors: bool = True) -> None:
        raw_path = self.workbook_edit.text().strip()
        if not raw_path:
            self.workbook_profile = None
            self._populate_assignment_choices()
            return

        path = Path(raw_path)
        try:
            self.workbook_profile = self.import_service.inspect_workbook(path)
            count = len(self.workbook_profile.assignments)
            if path.exists():
                self.statusBar().showMessage(f"Workbook ready: {count} assignment sheets")
            else:
                self.statusBar().showMessage("Workbook will be created on first import")
        except Exception as exc:
            self.workbook_profile = None
            self.statusBar().showMessage("Workbook could not be inspected")
            if show_errors:
                QMessageBox.warning(self, "Workbook Error", str(exc))
        self._populate_semesters(self._current_course())
        self._populate_assignment_choices()

    def _open_workbook(self) -> None:
        raw_path = self.workbook_edit.text().strip()
        if not raw_path:
            QMessageBox.information(self, "No Workbook Selected", "Choose a workbook before opening it.")
            return

        workbook_path = Path(raw_path)
        if not workbook_path.exists():
            QMessageBox.warning(self, "Workbook Not Found", f"The workbook does not exist yet:\n{workbook_path}")
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(str(workbook_path))
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(workbook_path)))
        except Exception as exc:
            QMessageBox.warning(self, "Open Workbook Failed", str(exc))

    def _browse_workbooks_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Select Workbooks Folder",
            str(self._workbooks_root()),
        )
        if selected:
            self.workbooks_dir_edit.setText(selected)
            self._apply_workbooks_dir(Path(selected))

    def _apply_workbooks_dir_from_edit(self) -> None:
        raw = self.workbooks_dir_edit.text().strip()
        if not raw:
            self.workbooks_dir_edit.setText(str(self.workbooks_dir))
            return
        self._apply_workbooks_dir(Path(raw))

    def _apply_workbooks_dir(self, path: Path) -> None:
        self.workbooks_dir = path.expanduser()
        self.workbooks_dir_edit.setText(str(self.workbooks_dir))
        self._course_changed()

    def _open_workbooks_dir(self) -> None:
        folder = self._workbooks_root()
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _generate_all_workbooks(self) -> None:
        if not self.catalog_items:
            QMessageBox.information(self, "No Catalog Loaded", "Load a course catalog before generating workbooks.")
            return

        folder = self._workbooks_root()
        folder.mkdir(parents=True, exist_ok=True)

        created = 0
        skipped = 0
        for course in self.catalog_items:
            workbook_path = self._guess_workbook_path(course)
            if not workbook_path:
                continue
            if workbook_path.exists():
                skipped += 1
                continue
            self.import_service.create_course_workbook(workbook_path, course)
            created += 1

        self.statusBar().showMessage(
            f"Generated {created} workbook(s); skipped {skipped} existing workbook(s)"
        )
        QMessageBox.information(
            self,
            "Workbook Generation Complete",
            f"Created {created} workbook(s) in {folder}.\nSkipped {skipped} existing workbook(s).",
        )
        self._course_changed()

    def _toggle_theme(self, checked: bool) -> None:
        self.theme = "dark" if checked else "light"
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(get_stylesheet(self.theme))
        self.drop_zone.set_theme(self.theme)

    def _add_zip_paths(self, paths: list[Path]) -> None:
        added = 0
        for path in paths:
            path = path.resolve()
            if path in self._known_zip_paths:
                continue
            self._known_zip_paths.add(path)
            self._add_preview_row(path)
            added += 1
        self._update_queue_count()
        if added:
            self.statusBar().showMessage(f"Queued {added} ZIP file(s)")

    def _add_preview_row(self, path: Path) -> None:
        default_assignment = self.assignment_combo.currentText().strip()
        default_semester = self.semester_combo.currentText().strip()
        preview = self.import_service.preview_archive(
            path,
            self.workbook_profile,
            default_assignment,
            default_semester,
        )
        row = self.table.rowCount()
        self.table.insertRow(row)

        zip_item = QTableWidgetItem(path.name)
        zip_item.setToolTip(str(path))
        zip_item.setData(self.PATH_ROLE, str(path))
        self.table.setItem(row, 0, zip_item)

        count_item = QTableWidgetItem(str(preview.response_count))
        count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 1, count_item)

        detected_assignment = preview.detected_assignment
        used_fallback = False
        if self._should_use_incremental_assignment_fallback(detected_assignment):
            detected_assignment = self._next_incremental_assignment()
            used_fallback = bool(detected_assignment)

        assignment_combo = QComboBox()
        for value in self._assignment_choice_values(detected_assignment):
            assignment_combo.addItem(value)
        if detected_assignment:
            assignment_combo.setCurrentText(detected_assignment)
        self.table.setCellWidget(row, 2, assignment_combo)

        semester_combo = QComboBox()
        semester_combo.setEditable(True)
        for value in self._semester_choice_values(preview.detected_semester):
            semester_combo.addItem(value)
        if preview.detected_semester:
            semester_combo.setCurrentText(preview.detected_semester)
        self.table.setCellWidget(row, 3, semester_combo)

        status_item = QTableWidgetItem(preview.note)
        if preview.submission_date:
            status_item.setToolTip(
                f"Submission date: {preview.submission_date.strftime('%Y-%m-%d %I:%M %p')}"
            )
        status_text = self._assignment_status_text(preview.note, detected_assignment, used_fallback)
        status_item.setText(status_text)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 4, status_item)
        self.table.resizeRowToContents(row)

    def _assignment_choice_values(self, extra: str | None = None) -> list[str]:
        values = [self.assignment_combo.itemText(index) for index in range(self.assignment_combo.count())]
        if extra and extra not in values:
            values.insert(0, extra)
        if not values:
            values.append("Assignment 1")
        return values

    def _should_use_incremental_assignment_fallback(self, detected_assignment: str | None) -> bool:
        if not self.workbook_profile or not self.workbook_profile.assignments:
            return not bool(detected_assignment)
        if not detected_assignment:
            return True
        return not any(assignment.match_title.strip() for assignment in self.workbook_profile.assignments)

    def _next_incremental_assignment(self) -> str | None:
        assignment_names = self._ordered_assignment_names()
        if not assignment_names:
            return None

        used_assignments: set[str] = set()
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 2)
            if isinstance(widget, QComboBox):
                value = widget.currentText().strip()
                if value:
                    used_assignments.add(value)

        for name in assignment_names:
            if name not in used_assignments:
                return name
        return assignment_names[min(self.table.rowCount(), len(assignment_names) - 1)]

    def _ordered_assignment_names(self) -> list[str]:
        if self.workbook_profile and self.workbook_profile.assignments:
            return [assignment.sheet_name for assignment in self.workbook_profile.assignments if assignment.sheet_name]
        values = [self.assignment_combo.itemText(index).strip() for index in range(self.assignment_combo.count())]
        return [value for value in values if value]

    def _assignment_status_text(
        self,
        preview_note: str,
        detected_assignment: str | None,
        used_fallback: bool,
    ) -> str:
        if preview_note != "Ready":
            return preview_note
        if used_fallback:
            return "Fallback (Verify)"
        if detected_assignment:
            return "Match"
        return "Fallback (Verify)"

    def _semester_choice_values(self, extra: str | None = None) -> list[str]:
        values = [self.semester_combo.itemText(index) for index in range(self.semester_combo.count())]
        if extra and extra not in values:
            values.insert(0, extra)
        return [value for value in values if value]

    def _remove_selected_rows(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            item = self.table.item(row, 0)
            if item:
                self._known_zip_paths.discard(Path(item.data(self.PATH_ROLE)))
            self.table.removeRow(row)
        self._update_queue_count()

    def _clear_queue(self, silent: bool = False) -> None:
        self.table.setRowCount(0)
        self._known_zip_paths.clear()
        self._update_queue_count()
        if not silent:
            self.statusBar().showMessage("Queue cleared")

    def _import_queue(self) -> None:
        workbook_path = Path(self.workbook_edit.text().strip())
        if not self.workbook_edit.text().strip():
            QMessageBox.warning(self, "Workbook Required", "Choose a workbook before importing.")
            return
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "No ZIPs Queued", "Add at least one Brightspace ZIP first.")
            return

        requests: list[ArchiveImportRequest] = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            assignment_widget = self.table.cellWidget(row, 2)
            semester_widget = self.table.cellWidget(row, 3)
            if (
                not item
                or not isinstance(assignment_widget, QComboBox)
                or not isinstance(semester_widget, QComboBox)
            ):
                continue
            semester = semester_widget.currentText().strip()
            if not semester:
                QMessageBox.warning(
                    self,
                    "Semester Required",
                    f"Enter a semester for {item.text()} before importing.",
                )
                return
            requests.append(
                ArchiveImportRequest(
                    zip_path=Path(item.data(self.PATH_ROLE)),
                    target_sheet=assignment_widget.currentText().strip(),
                    semester=semester,
                )
            )

        try:
            results = self.import_service.import_archives(
                workbook_path=workbook_path,
                requests=requests,
                workbook_profile=self.workbook_profile,
                course=self._current_course(),
                create_missing_sheets=self.create_sheets_check.isChecked(),
                record_advanced_metadata=self.advanced_metadata_check.isChecked(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Import Failed", str(exc))
            self.statusBar().showMessage("Import failed")
            return

        total = sum(result.imported_count for result in results)
        for row in range(self.table.rowCount()):
            self.table.item(row, 4).setText("Imported")
        self.statusBar().showMessage(f"Imported {total} responses into {workbook_path.name}")
        QMessageBox.information(
            self,
            "Import Complete",
            f"Imported {total} responses from {len(results)} ZIP file(s).",
        )
        self._inspect_workbook(show_errors=False)

    def _current_course(self) -> CourseCatalogItem | None:
        data = self.course_combo.currentData()
        if isinstance(data, CourseCatalogItem):
            return data
        return None

    def _guess_workbook_path(self, course: CourseCatalogItem | None) -> Path | None:
        if not course:
            return None
        return self._workbooks_root() / f"{self._class_filename_stem(course.course_name)}workbook.xlsx"

    def _work_root(self) -> Path:
        return Path(sys.argv[0]).resolve().parent

    def _default_workbooks_root(self) -> Path:
        return self._work_root() / "workbooks"

    def _workbooks_root(self) -> Path:
        return self.workbooks_dir

    def _class_filename_stem(self, value: str) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", "", value.casefold())
        return cleaned or "course"

    def _update_queue_count(self) -> None:
        count = self.table.rowCount()
        noun = "ZIP" if count == 1 else "ZIPs"
        self.queue_count.setText(f"{count} {noun} queued")


def show_main_window(app: QApplication) -> MainWindow:
    window = MainWindow()
    window.show()
    app.setActiveWindow(window)
    return window
