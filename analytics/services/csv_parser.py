"""
CSV parser for analytics exam uploads.

Public API:
    validate_structure(headers)  → question_cols dict, raises CSVStructureError
    parse_row(row, row_number, question_cols) → (ParsedRow | None, RowError | None)
    parse_file(file_obj)         → ParseResult
    generate_template_csv()      → str  (ready to serve as file download)

This module is pure — no DB calls, no imports from other analytics modules
except constants and exceptions.
"""

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple

from analytics.constants import (
    REQUIRED_INFO_COLUMNS,
    REQUIRED_SUBJECT_COLUMNS,
    SUBJECT_CHOICES,
    SUBJECT_COLUMN_MAP,
    SUBJECT_PREFIX_MAP,
)
from analytics.exceptions import AnalyticsValidationError, CSVStructureError


# ------------------------------------------------------------------ data classes

@dataclass
class ParsedExamMeta:
    exam_name: str
    exam_date: date


@dataclass
class ParsedStudent:
    student_ref_id: str
    name: str
    class_name: str
    section_name: str


@dataclass
class ParsedSubjectResult:
    total_marks: int
    rank: int
    correct: int
    wrong: int
    unattempted: int


@dataclass
class ParsedRow:
    student: ParsedStudent
    results: Dict[str, ParsedSubjectResult]        
    question_statuses: Dict[str, Dict[int, str]]   


@dataclass
class RowError:
    row_number: int
    student_id: str   
    reason: str


@dataclass
class ParseResult:
    exam_meta: ParsedExamMeta
    question_cols: Dict[str, List[str]]   
    rows: List[ParsedRow] = field(default_factory=list)
    skipped: List[RowError] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return len(self.rows)



def validate_structure(headers: List[str]) -> Dict[str, List[str]]:
    """
    Validate that all required fixed columns are present, then detect
    question columns dynamically from headers using prefix patterns.

    Returns question_cols dict on success.
    Raises CSVStructureError immediately on any missing column or subject
    with zero question columns.
    """
    header_set = set(headers)

    missing = [
        col for col in REQUIRED_INFO_COLUMNS + REQUIRED_SUBJECT_COLUMNS
        if col not in header_set
    ]
    if missing:
        raise CSVStructureError(missing)

    question_cols: Dict[str, List[str]] = {}
    missing_subjects = []

    for subject_name, prefix in SUBJECT_PREFIX_MAP.items():
        pattern = re.compile(rf'^{re.escape(prefix)}\d+$')
        cols = sorted(
            [h for h in headers if pattern.fullmatch(h)],
            key=lambda x: int(x[len(prefix):]),
        )
        if not cols:
            missing_subjects.append(f'{subject_name} (expected columns like {prefix}1, {prefix}2, ...)')
        question_cols[subject_name] = cols

    if missing_subjects:
        raise CSVStructureError(missing_subjects)

    return question_cols


def parse_row(
    row: dict,
    row_number: int,
    question_cols: Dict[str, List[str]],
) -> Tuple[Optional[ParsedRow], Optional[RowError]]:
    """
    Validate and parse one CSV row.

    Returns (ParsedRow, None) on success or (None, RowError) on validation
    failure. Never raises — all errors are returned as RowError.

    Question status values that are not C/W/U are silently defaulted to 'U'
    (blank = unattempted is a valid exam state, not a data error).
    """
    student_id = row.get('student_id', '').strip()

    def error(reason: str) -> Tuple[None, RowError]:
        return None, RowError(row_number=row_number, student_id=student_id, reason=reason)

    # --- student info ---
    if not student_id:
        return error('student_id is blank')

    student_name = row.get('student_name', '').strip()
    if not student_name:
        return error('student_name is blank')

    class_name = row.get('class', '').strip()
    if not class_name:
        return error('class is blank')

    section_name = row.get('section', '').strip()
    if not section_name:
        return error('section is blank')

    exam_name = row.get('exam_name', '').strip()
    if not exam_name:
        return error('exam_name is blank')

    exam_date_str = row.get('exam_date', '').strip()
    try:
        exam_date = date.fromisoformat(exam_date_str)
    except (ValueError, TypeError):
        return error(f'exam_date "{exam_date_str}" is not a valid YYYY-MM-DD date')

    # --- per-subject integer columns ---
    results: Dict[str, ParsedSubjectResult] = {}
    for subject_name, col_map in SUBJECT_COLUMN_MAP.items():
        try:
            results[subject_name] = ParsedSubjectResult(
                total_marks=_int(row.get(col_map['total'], '')),
                rank=_int(row.get(col_map['rank'], '')),
                correct=_int(row.get(col_map['correct'], '')),
                wrong=_int(row.get(col_map['wrong'], '')),
                unattempted=_int(row.get(col_map['unattempted'], '')),
            )
        except ValueError as exc:
            subject_display = dict(SUBJECT_CHOICES).get(subject_name, subject_name)
            return error(f'{subject_display}: {exc}')

    # --- question statuses (soft — bad value → 'U', never skip the row) ---
    question_statuses: Dict[str, Dict[int, str]] = {}
    for subject_name, cols in question_cols.items():
        prefix = SUBJECT_PREFIX_MAP[subject_name]
        statuses: Dict[int, str] = {}
        for col in cols:
            q_no = int(col[len(prefix):])
            val = row.get(col, '').strip().upper()
            statuses[q_no] = val if val in ('C', 'W', 'U') else 'U'
        question_statuses[subject_name] = statuses

    parsed = ParsedRow(
        student=ParsedStudent(
            student_ref_id=student_id,
            name=student_name,
            class_name=class_name,
            section_name=section_name,
        ),
        results=results,
        question_statuses=question_statuses,
    )
    return parsed, None


def parse_file(file_obj) -> ParseResult:
    """
    Read, validate, and parse a CSV file object.

    Raises CSVStructureError if required columns are missing.
    Raises AnalyticsValidationError if the file is empty or has no valid rows.
    Bad individual rows are collected in ParseResult.skipped, not raised.
    """
    raw = file_obj.read()
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8-sig')

    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)

    if not rows:
        raise AnalyticsValidationError('CSV file is empty.')

    headers = [h.strip().lower() for h in (reader.fieldnames or [])]
    question_cols = validate_structure(headers)

    exam_meta: Optional[ParsedExamMeta] = None
    parsed_rows: List[ParsedRow] = []
    skipped: List[RowError] = []

    for i, raw_row in enumerate(rows, start=1):
        row = {k.strip().lower(): v for k, v in raw_row.items()}
        parsed_row, row_error = parse_row(row, i, question_cols)

        if row_error:
            skipped.append(row_error)
            continue

        if exam_meta is None:
            exam_meta = ParsedExamMeta(
                exam_name=row['exam_name'].strip(),
                exam_date=date.fromisoformat(row['exam_date'].strip()),
            )

        parsed_rows.append(parsed_row)

    if exam_meta is None:
        raise AnalyticsValidationError('No valid rows found in CSV.')

    return ParseResult(
        exam_meta=exam_meta,
        question_cols=question_cols,
        rows=parsed_rows,
        skipped=skipped,
    )


def generate_template_csv() -> str:
    """
    Generate a downloadable CSV template string.

    Contains all fixed columns (21) + default question columns
    (m_q1…m_q80, p_q1…p_q40, c_q1…c_q40) and 3 example rows.
    Users may add or remove question columns — the parser detects them
    dynamically at upload time.
    """
    maths_q_cols   = [f'm_q{i}' for i in range(1, 81)]
    physics_q_cols = [f'p_q{i}' for i in range(1, 41)]
    chem_q_cols    = [f'c_q{i}' for i in range(1, 41)]

    all_headers = (
        REQUIRED_INFO_COLUMNS
        + REQUIRED_SUBJECT_COLUMNS
        + maths_q_cols
        + physics_q_cols
        + chem_q_cols
    )

    example_rows = [
        _make_example_row(
            student_id='STU001', name='Rahul Sharma', class_name='Class 11',
            section='11-A', rank_offset=1,
            maths=(62, 1, 55, 18, 7), physics=(28, 2, 22, 12, 6), chem=(30, 1, 26, 9, 5),
            maths_q_cols=maths_q_cols, physics_q_cols=physics_q_cols, chem_q_cols=chem_q_cols,
            pattern='high',
        ),
        _make_example_row(
            student_id='STU002', name='Priya Nair', class_name='Class 11',
            section='11-A', rank_offset=2,
            maths=(44, 3, 38, 20, 22), physics=(19, 5, 16, 14, 10), chem=(21, 4, 18, 12, 10),
            maths_q_cols=maths_q_cols, physics_q_cols=physics_q_cols, chem_q_cols=chem_q_cols,
            pattern='mid',
        ),
        _make_example_row(
            student_id='STU003', name='Arjun Reddy', class_name='Class 11',
            section='11-B', rank_offset=6,
            maths=(22, 8, 20, 22, 38), physics=(10, 9, 9, 16, 15), chem=(12, 7, 11, 15, 14),
            maths_q_cols=maths_q_cols, physics_q_cols=physics_q_cols, chem_q_cols=chem_q_cols,
            pattern='low',
        ),
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_headers, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(example_rows)
    return output.getvalue()


# ------------------------------------------------------------------ helpers

def _int(value: str) -> int:
    """Parse a CSV string to int, raising ValueError with a readable message."""
    val = str(value).strip()
    if not val:
        raise ValueError(f'expected an integer but got an empty value')
    try:
        result = int(val)
    except ValueError:
        raise ValueError(f'expected an integer but got "{val}"')
    if result < 0:
        raise ValueError(f'value must be ≥ 0, got {result}')
    return result


def _make_example_row(
    student_id, name, class_name, section, rank_offset,
    maths, physics, chem,
    maths_q_cols, physics_q_cols, chem_q_cols,
    pattern,
):
    """Build one example CSV row dict with realistic question statuses."""
    m_total, m_rank, m_c, m_w, m_u = maths
    p_total, p_rank, p_c, p_w, p_u = physics
    c_total, c_rank, c_c, c_w, c_u = chem

    row = {
        'student_id': student_id,
        'student_name': name,
        'exam_name': 'JEE Mock Test 1',
        'exam_date': '2026-05-01',
        'class': class_name,
        'section': section,
        'maths_total': m_total, 'maths_rank': m_rank,
        'maths_correct': m_c, 'maths_wrong': m_w, 'maths_unattempted': m_u,
        'physics_total': p_total, 'physics_rank': p_rank,
        'physics_correct': p_c, 'physics_wrong': p_w, 'physics_unattempted': p_u,
        'chem_total': c_total, 'chem_rank': c_rank,
        'chem_correct': c_c, 'chem_wrong': c_w, 'chem_unattempted': c_u,
    }

    # Fill question statuses based on pattern (high/mid/low performance)
    for cols, correct_count, wrong_count in [
        (maths_q_cols, m_c, m_w),
        (physics_q_cols, p_c, p_w),
        (chem_q_cols, c_c, c_w),
    ]:
        for idx, col in enumerate(cols):
            if idx < correct_count:
                row[col] = 'C'
            elif idx < correct_count + wrong_count:
                row[col] = 'W'
            else:
                row[col] = 'U'

    return row
