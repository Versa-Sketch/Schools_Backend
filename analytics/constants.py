SUBJECT_MATHS = 'MATHS'
SUBJECT_PHYSICS = 'PHYSICS'
SUBJECT_CHEMISTRY = 'CHEMISTRY'
SUBJECT_CHOICES = [
    (SUBJECT_MATHS, 'Maths'),
    (SUBJECT_PHYSICS, 'Physics'),
    (SUBJECT_CHEMISTRY, 'Chemistry'),
]

SUBJECT_CONFIG = {
    SUBJECT_MATHS:     {'total_questions': 80, 'max_marks': 80, 'prefix': 'm_q'},
    SUBJECT_PHYSICS:   {'total_questions': 40, 'max_marks': 40, 'prefix': 'p_q'},
    SUBJECT_CHEMISTRY: {'total_questions': 40, 'max_marks': 40, 'prefix': 'c_q'},
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

REQUIRED_INFO_COLUMNS = [
    'student_id', 'student_name', 'exam_name', 'exam_date', 'class', 'section',
]

REQUIRED_SUBJECT_COLUMNS = [
    'maths_total', 'maths_rank', 'maths_correct', 'maths_wrong', 'maths_unattempted',
    'physics_total', 'physics_rank', 'physics_correct', 'physics_wrong', 'physics_unattempted',
    'chem_total', 'chem_rank', 'chem_correct', 'chem_wrong', 'chem_unattempted',
]

MATHS_Q_COLUMNS = [f'm_q{i}' for i in range(1, 81)]
PHYSICS_Q_COLUMNS = [f'p_q{i}' for i in range(1, 41)]
CHEM_Q_COLUMNS = [f'c_q{i}' for i in range(1, 41)]
QUESTION_COLUMNS = MATHS_Q_COLUMNS + PHYSICS_Q_COLUMNS + CHEM_Q_COLUMNS

ALL_REQUIRED_COLUMNS = REQUIRED_INFO_COLUMNS + REQUIRED_SUBJECT_COLUMNS + QUESTION_COLUMNS
