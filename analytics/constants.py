SUBJECT_MATHS = 'MATHS'
SUBJECT_PHYSICS = 'PHYSICS'
SUBJECT_CHEMISTRY = 'CHEMISTRY'
SUBJECT_CHOICES = [
    (SUBJECT_MATHS, 'Maths'),
    (SUBJECT_PHYSICS, 'Physics'),
    (SUBJECT_CHEMISTRY, 'Chemistry'),
]

# CSV column prefix for question columns: m_q1, m_q2, ... / p_q1, ... / c_q1, ...
# total_questions is detected dynamically from CSV headers, not hardcoded here.
SUBJECT_PREFIX_MAP = {
    SUBJECT_MATHS:     'm_q',
    SUBJECT_PHYSICS:   'p_q',
    SUBJECT_CHEMISTRY: 'c_q',
}

# Maps each subject to its per-student summary columns in the CSV
SUBJECT_COLUMN_MAP = {
    SUBJECT_MATHS: {
        'total': 'maths_total', 'rank': 'maths_rank',
        'correct': 'maths_correct', 'wrong': 'maths_wrong', 'unattempted': 'maths_unattempted',
    },
    SUBJECT_PHYSICS: {
        'total': 'physics_total', 'rank': 'physics_rank',
        'correct': 'physics_correct', 'wrong': 'physics_wrong', 'unattempted': 'physics_unattempted',
    },
    SUBJECT_CHEMISTRY: {
        'total': 'chem_total', 'rank': 'chem_rank',
        'correct': 'chem_correct', 'wrong': 'chem_wrong', 'unattempted': 'chem_unattempted',
    },
}

ANALYTICS_STATUS_PENDING = 'PENDING'
ANALYTICS_STATUS_RUNNING = 'RUNNING'
ANALYTICS_STATUS_DONE = 'DONE'
ANALYTICS_STATUS_FAILED = 'FAILED'
ANALYTICS_STATUS_CHOICES = [
    (ANALYTICS_STATUS_PENDING, 'Pending'),
    (ANALYTICS_STATUS_RUNNING, 'Running'),
    (ANALYTICS_STATUS_DONE, 'Done'),
    (ANALYTICS_STATUS_FAILED, 'Failed'),
]

DIFFICULTY_EASY = 'EASY'
DIFFICULTY_MEDIUM = 'MEDIUM'
DIFFICULTY_HARD = 'HARD'
DIFFICULTY_CHOICES = [
    (DIFFICULTY_EASY, 'Easy'),
    (DIFFICULTY_MEDIUM, 'Medium'),
    (DIFFICULTY_HARD, 'Hard'),
]

# difficulty_index is expressed as 0–100 (percentage of students who got it right)
DIFFICULTY_EASY_THRESHOLD   = 70.0   # > 70  → EASY
DIFFICULTY_MEDIUM_THRESHOLD = 30.0   # 30–70 → MEDIUM, below 30 → HARD

# has_key_error = True only when discrimination is meaningfully negative
# AND the question is not easy. Easy questions (>70% correct) can have
# slightly negative discrimination just because the formula loses resolution
# when almost everyone answers correctly — that is not a real answer-key error.
KEY_ERROR_DISCRIMINATION_THRESHOLD = -0.15   # discrimination must be worse than this
KEY_ERROR_MAX_DIFFICULTY           = 70.0    # skip the flag if difficulty_index ≥ this

# Risk score component weights (must sum ≤ 100)
RISK_SCORE_MARKS_WEIGHT  = 40   # how far below batch average
RISK_SCORE_WRONG_WEIGHT  = 30   # wrong-answer rate among attempted questions
RISK_SCORE_SKIP_WEIGHT   = 20   # skip rate across all questions

RISK_SAFE = 'SAFE'
RISK_WATCH = 'WATCH'
RISK_ALERT = 'ALERT'
RISK_CHOICES = [
    (RISK_SAFE, 'Safe'),
    (RISK_WATCH, 'Watch'),
    (RISK_ALERT, 'Alert'),
]

PERFORMANCE_EXCEPTIONAL = 'EXCEPTIONAL'
PERFORMANCE_ABOVE_AVERAGE = 'ABOVE_AVERAGE'
PERFORMANCE_AVERAGE = 'AVERAGE'
PERFORMANCE_BELOW_AVERAGE = 'BELOW_AVERAGE'
PERFORMANCE_NEEDS_ATTENTION = 'NEEDS_ATTENTION'
PERFORMANCE_CHOICES = [
    (PERFORMANCE_EXCEPTIONAL, 'Exceptional'),
    (PERFORMANCE_ABOVE_AVERAGE, 'Above Average'),
    (PERFORMANCE_AVERAGE, 'Average'),
    (PERFORMANCE_BELOW_AVERAGE, 'Below Average'),
    (PERFORMANCE_NEEDS_ATTENTION, 'Needs Attention'),
]

QUESTION_STATUS_CORRECT = 'C'
QUESTION_STATUS_WRONG = 'W'
QUESTION_STATUS_UNATTEMPTED = 'U'
QUESTION_STATUS_CHOICES = [
    (QUESTION_STATUS_CORRECT, 'Correct'),
    (QUESTION_STATUS_WRONG, 'Wrong'),
    (QUESTION_STATUS_UNATTEMPTED, 'Unattempted'),
]

# Fixed columns every CSV must have
REQUIRED_INFO_COLUMNS = [
    'student_id', 'student_name', 'exam_name', 'exam_date', 'class', 'section',
]

REQUIRED_SUBJECT_COLUMNS = [
    'maths_total', 'maths_rank', 'maths_correct', 'maths_wrong', 'maths_unattempted',
    'physics_total', 'physics_rank', 'physics_correct', 'physics_wrong', 'physics_unattempted',
    'chem_total', 'chem_rank', 'chem_correct', 'chem_wrong', 'chem_unattempted',
]
