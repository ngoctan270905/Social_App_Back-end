from enum import Enum

class ExamSortType(str, Enum):
    name = "name"
    grade = "grade"
    created_at = "created_at"
