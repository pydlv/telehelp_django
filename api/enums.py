from enum import IntEnum


class DayOfWeek(IntEnum):
    sunday = 1
    monday = 1 << 1
    tuesday = 1 << 2
    wednesday = 1 << 3
    thursday = 1 << 4
    friday = 1 << 5
    saturday = 1 << 6
    all = sunday | monday | tuesday | wednesday | thursday | friday | saturday
