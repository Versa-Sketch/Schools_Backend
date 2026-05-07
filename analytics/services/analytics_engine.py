"""
Analytics engine — pure computation, zero DB calls.

Public API:
    compute_question_analytics(q_results, subject_marks) → list[QuestionAnalyticsResult]
    compute_student_risks(subject_results, total_questions) → list[StudentRiskResult]
    compute_section_analytics(section_students, risk_by_student) → list[SectionAnalyticsResult]

The storage layer is responsible for:
  - fetching input data from the DB (as plain dicts)
  - calling these functions
  - bulk-writing the returned dataclasses back to the DB

Input dicts expected by each function are documented on the function signatures.
"""

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

from analytics.constants import (
    DIFFICULTY_EASY,
    DIFFICULTY_EASY_THRESHOLD,
    DIFFICULTY_HARD,
    DIFFICULTY_MEDIUM,
    DIFFICULTY_MEDIUM_THRESHOLD,
    KEY_ERROR_DISCRIMINATION_THRESHOLD,
    KEY_ERROR_MAX_DIFFICULTY,
    PERFORMANCE_ABOVE_AVERAGE,
    PERFORMANCE_AVERAGE,
    PERFORMANCE_BELOW_AVERAGE,
    PERFORMANCE_EXCEPTIONAL,
    PERFORMANCE_NEEDS_ATTENTION,
    RISK_ALERT,
    RISK_SAFE,
    RISK_SCORE_MARKS_WEIGHT,
    RISK_SCORE_SKIP_WEIGHT,
    RISK_SCORE_WRONG_WEIGHT,
    RISK_WATCH,
)


# ------------------------------------------------------------------ output types

@dataclass
class QuestionAnalyticsResult:
    q_no: int
    correct_count: int
    wrong_count: int
    skip_count: int
    difficulty_index: float      # 0.0–100.0  e.g. 72.5 → 72.5% of students correct
    difficulty_tag: str          # EASY / MEDIUM / HARD
    discrimination_index: float  # -1.0 to 1.0
    has_key_error: bool


@dataclass
class StudentRiskResult:
    student_id: str        # UUID string — whatever the storage passed in
    risk_score: float      # 0.0–100.0
    risk_label: str        # SAFE / WATCH / ALERT
    z_score: float
    performance_label: str  # EXCEPTIONAL / ABOVE_AVERAGE / AVERAGE / BELOW_AVERAGE / NEEDS_ATTENTION


@dataclass
class SectionAnalyticsResult:
    section_id: str
    avg_marks: float
    median_marks: float
    std_dev: float
    top_scorer_id: str    # student_id with the highest marks in this section+subject
    at_risk_count: int    # number of students with risk_label == ALERT


# ------------------------------------------------------------------ public API

def compute_question_analytics(
    q_results: List[Dict],     # [{'student_id': str, 'q_no': int, 'status': 'C'|'W'|'U'}, ...]
    subject_marks: List[Dict], # [{'student_id': str, 'total_marks': int}, ...]
) -> List[QuestionAnalyticsResult]:
    """
    Compute per-question difficulty and discrimination for one subject in one exam.

    q_results    — every QuestionResult row for this exam+subject
    subject_marks — every ExamResult row for this exam+subject (used for top27/bottom27)
    """
    if not q_results or not subject_marks:
        return []

    total_students = len(subject_marks)
    top_ids, bottom_ids, n27 = _top_bottom_split(subject_marks)

    # Group question results by q_no, and build per-question student-status lookup
    q_counts: Dict[int, Dict[str, int]] = defaultdict(lambda: {'C': 0, 'W': 0, 'U': 0})
    q_status_lookup: Dict[int, Dict[str, str]] = defaultdict(dict)

    for row in q_results:
        q_no      = row['q_no']
        student   = str(row['student_id'])
        status    = row['status']
        q_counts[q_no][status] += 1
        q_status_lookup[q_no][student] = status

    results = []
    for q_no in sorted(q_counts):
        counts  = q_counts[q_no]
        correct = counts['C']
        wrong   = counts['W']
        skip    = counts['U']

        difficulty_index = (correct / total_students) * 100
        difficulty_tag   = _difficulty_tag(difficulty_index)

        # Discrimination: (correct rate in top27) - (correct rate in bottom27)
        statuses      = q_status_lookup[q_no]
        top_correct   = sum(1 for sid in top_ids   if statuses.get(sid) == 'C')
        bot_correct   = sum(1 for sid in bottom_ids if statuses.get(sid) == 'C')
        discrimination = (top_correct / n27) - (bot_correct / n27)

        # Flag as key error only when discrimination is meaningfully negative
        # AND the question is not EASY. EASY questions (>70% correct) lose
        # discrimination resolution because almost everyone answers correctly,
        # making slightly negative values expected rather than suspicious.
        has_key_error = (
            discrimination < KEY_ERROR_DISCRIMINATION_THRESHOLD
            and difficulty_tag != DIFFICULTY_EASY
        )

        results.append(QuestionAnalyticsResult(
            q_no=q_no,
            correct_count=correct,
            wrong_count=wrong,
            skip_count=skip,
            difficulty_index=round(difficulty_index, 2),
            difficulty_tag=difficulty_tag,
            discrimination_index=round(discrimination, 4),
            has_key_error=has_key_error,
        ))

    return results


def compute_student_risks(
    subject_results: List[Dict],  # [{'student_id': str, 'total_marks': int,
                                  #   'correct': int, 'wrong': int, 'unattempted': int}, ...]
    total_questions: int,          # ExamSubject.total_questions for this subject
) -> List[StudentRiskResult]:
    """
    Compute risk score, risk label, z-score, and performance label
    for every student in one subject in one exam.
    """
    if not subject_results:
        return []

    marks_list = [r['total_marks'] for r in subject_results]
    batch_avg  = statistics.mean(marks_list)
    std        = statistics.stdev(marks_list) if len(marks_list) > 1 else 0.0

    results = []
    for r in subject_results:
        marks       = r['total_marks']
        correct     = r['correct']
        wrong       = r['wrong']
        unattempted = r['unattempted']

        # --- risk score (three independent components, each capped by its weight) ---

        # Component 1: how far below batch average (normalised, 0–40 pts)
        if batch_avg > 0:
            score_component = RISK_SCORE_MARKS_WEIGHT * max(0.0, (batch_avg - marks) / batch_avg)
        else:
            score_component = 0.0

        # Component 2: wrong-answer rate among questions actually attempted (0–30 pts)
        attempts = correct + wrong
        if attempts > 0:
            wrong_component = RISK_SCORE_WRONG_WEIGHT * (wrong / attempts)
        else:
            wrong_component = 0.0

        # Component 3: skip rate across all questions in the paper (0–20 pts)
        if total_questions > 0:
            skip_component = RISK_SCORE_SKIP_WEIGHT * (unattempted / total_questions)
        else:
            skip_component = 0.0

        risk_score = min(100.0, score_component + wrong_component + skip_component)
        risk_label = _risk_label(risk_score)

        # --- z-score and performance label ---
        z_score = (marks - batch_avg) / std if std > 0 else 0.0
        performance_label = _performance_label(z_score)

        results.append(StudentRiskResult(
            student_id=str(r['student_id']),
            risk_score=round(risk_score, 2),
            risk_label=risk_label,
            z_score=round(z_score, 4),
            performance_label=performance_label,
        ))

    return results


def compute_section_analytics(
    section_students: List[Dict],  # [{'student_id': str, 'total_marks': int, 'section_id': str}, ...]
    risk_by_student: Dict[str, str],  # {student_id: risk_label}  ← from compute_student_risks
) -> List[SectionAnalyticsResult]:
    """
    Compute per-section summary statistics for one subject in one exam.

    section_students — only students who have a matched section FK (nulls excluded by storage)
    risk_by_student  — result of compute_student_risks, keyed by student_id string
    """
    if not section_students:
        return []

    # Group students by section
    by_section: Dict[str, List[Dict]] = defaultdict(list)
    for s in section_students:
        by_section[str(s['section_id'])].append(s)

    results = []
    for section_id, group in by_section.items():
        marks = [s['total_marks'] for s in group]

        avg    = statistics.mean(marks)
        median = statistics.median(marks)
        std    = statistics.stdev(marks) if len(marks) > 1 else 0.0

        top_scorer = max(group, key=lambda s: s['total_marks'])
        at_risk    = sum(
            1 for s in group
            if risk_by_student.get(str(s['student_id'])) == RISK_ALERT
        )

        results.append(SectionAnalyticsResult(
            section_id=section_id,
            avg_marks=round(avg, 2),
            median_marks=round(median, 2),
            std_dev=round(std, 2),
            top_scorer_id=str(top_scorer['student_id']),
            at_risk_count=at_risk,
        ))

    return results


# ------------------------------------------------------------------ private helpers

def _top_bottom_split(
    subject_marks: List[Dict],
) -> tuple:
    """
    Return (top_ids, bottom_ids, n27) for discrimination index calculation.

    Sorted ascending by total_marks.
    n27 = max(1, floor(N × 0.27)) — the validated optimal split for discrimination.
    top_ids    = last  n27 students (highest marks)
    bottom_ids = first n27 students (lowest marks)
    """
    sorted_marks = sorted(subject_marks, key=lambda r: r['total_marks'])
    n27          = max(1, math.floor(len(sorted_marks) * 0.27))
    bottom_ids   = {str(r['student_id']) for r in sorted_marks[:n27]}
    top_ids      = {str(r['student_id']) for r in sorted_marks[-n27:]}
    return top_ids, bottom_ids, n27


def _difficulty_tag(difficulty_index: float) -> str:
    if difficulty_index > DIFFICULTY_EASY_THRESHOLD:
        return DIFFICULTY_EASY
    if difficulty_index >= DIFFICULTY_MEDIUM_THRESHOLD:
        return DIFFICULTY_MEDIUM
    return DIFFICULTY_HARD


def _risk_label(risk_score: float) -> str:
    if risk_score < 30:
        return RISK_SAFE
    if risk_score < 60:
        return RISK_WATCH
    return RISK_ALERT


def _performance_label(z: float) -> str:
    if z > 1.5:
        return PERFORMANCE_EXCEPTIONAL
    if z > 0.5:
        return PERFORMANCE_ABOVE_AVERAGE
    if z > -0.5:
        return PERFORMANCE_AVERAGE
    if z > -1.5:
        return PERFORMANCE_BELOW_AVERAGE
    return PERFORMANCE_NEEDS_ATTENTION
