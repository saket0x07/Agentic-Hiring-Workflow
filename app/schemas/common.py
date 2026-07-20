from enum import Enum

class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"

class WorkMode(str, Enum):
    ON_SITE = "on_site"
    REMOTE = "remote"
    HYBRID = "hybrid"