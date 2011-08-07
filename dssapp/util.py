from dssapp.models import *
from munkres import Munkres, print_matrix

SPRING_MONTH = 1;
SUMMER_MONTH = 6;
FALL_MONTH = 9;


TALKS_PER_EVENT = 2;
PREFERENCE_TO_COST = {None: 5, 'prefer': 1, 'available': 5, 'cannot': 1000000}

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
    
    
# schedule the following students into the DSS schedule.
def schedule_semester(semester, students):
    events = Event.objects.filter(event_type='DSS', semester=semester)
    
    schedulable = []
    for e in events:
        # make an entry for every available slot.
        for copy in range(len(e.talks.all()), TALKS_PER_EVENT):
            schedulable.append(e)
            
    
    # build up a preference matrix.
    cost_matrix = []
    
    # the first index is for students
    for s in students:
        costs = []
        for e in schedulable:
            try:
                pref = TalkPreference.objects.get(student=s, event=e)
                pref = pref.preference
            except TalkPreference.DoesNotExist:
                pref = None
            
            costs.append(PREFERENCE_TO_COST[pref])
        cost_matrix.append(costs)

    m = Munkres()
    indexes = m.compute(cost_matrix)
    print_matrix(cost_matrix)

    for row, column in indexes:
        print "Scheduling student", students[row], "for talk on", schedulable[column].timestamp
        talk = Talk(student=students[row], order=1)
        talk.save()
        schedulable[column].talks.add(talk)
        schedulable[column].save()

    
                
                
def most_recent_semester():
    return Semester.objects.order_by('-year','-month')[0]
    
            
            
    
    