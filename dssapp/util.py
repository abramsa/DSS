from dssapp.models import *

SPRING_MONTH = 1;
SUMMER_MONTH = 6;
FALL_MONTH = 9;


def string_to_semester(datestring):
    # datestring is of the form yyyy.m or yyyy.mm.
    
    year = int(datestring[0:4])
    month = int(datestring[5:])
    semester, created = Semester.objects.get_or_create(year=year, month=month)
    return semester
    
def timestamp_to_semester(timestamp):
    # returns spring, summer,  or fall semester of that year.
    year = timestamp.year
    month = timestamp.month
    if SPRING_MONTH <= month < SUMMER_MONTH:
        semester, created = Semester.objects.get_or_create(year=year, month=SPRING_MONTH)
    elif SUMMER_MONTH <= month < FALL_MONTH:
        semester, created = Semester.objects.get_or_create(year=year, month=SUMMER_MONTH)
    else:
        semester, created = Semester.objects.get_or_create(year=year, month=FALL_MONTH)
    return semester
    