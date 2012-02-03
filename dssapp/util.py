from dssapp.models import *
from munkres import Munkres, print_matrix

SPRING_MONTH = 1;
SUMMER_MONTH = 6;
FALL_MONTH = 9;


TALKS_PER_EVENT = 2;
JUDGES_PER_EVENT = 3;

PREFERENCE_TO_COST = {None: 5, 'prefer': 1, 'available': 5, 'cannot': 1000000}
JUDGE_COST = {True: 1, False: 1000000}



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
def schedule_semester_students(semester, students):
    # make sure none of the students are already giving a talk.
    dss_students = []
    for s in students:
        if Talk.objects.filter(event__semester=semester, student=s).exists():
            continue
        dss_students.append(s)
    
    events = Event.objects.filter(event_type='DSS', semester=semester)
    
    schedulable = []
    for e in events:
        # make an entry for every available slot.
        for copy in range(len(e.talks.all()), TALKS_PER_EVENT):
            schedulable.append(e)
            
    if len(dss_students) == 0 or len(schedulable) == 0:
        return
    
    # build up a preference matrix.
    cost_matrix = []
    
    # the first index is for students
    for s in dss_students:
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
        if cost_matrix[row][column] == PREFERENCE_TO_COST['cannot']:
            continue
        print "Scheduling student", dss_students[row], "for talk on", schedulable[column].timestamp
        talk = Talk(student=dss_students[row], order=1)
        talk.save()
        schedulable[column].talks.add(talk)
        schedulable[column].save()
        
# schedule judges into the DSS schedule.  Works on the assumption that students
# are free the same day that their advisors are, WHICH SHOULD BE FUGGIN TRUE.
def schedule_semester_judges(semester):
    # get all the events this semester.
    all_events = Event.objects.filter(event_type='DSS', semester=semester)
    
    schedulable = []
    for e in all_events:
        for copy in range(len(e.judges.all()), JUDGES_PER_EVENT):
            schedulable.append(e)
    
    # get all the faculty.
    all_faculty = Advisor.objects.filter(active=True)
    
    if len(all_faculty) == 0 or len(schedulable) == 0:
        return
    
    # the goal is to schedule 3 judges per event, such that:
    # 1.  if a judge is scheduled for an event, at least one of their students 
    #     said that they were available that day.
    # 2.  none of that judge's students are presenting that day.
    # this function will assign one faculty member to one event, if possible.  So,
    # hopefully the judges will be spread out as we call this function a few times.
    
    # find out which faculty are available for which events.
    for a in all_faculty:
        students = a.student_set.all()
        a.available = {}
        
        for e in all_events:
            if a in e.judges.all():
                # the judge is already going to this event.
                a.available[e] = False
                continue
            
            a.available[e] = False
            for s in students:
                # if the student is inactive or exempt, don't worry about them.
                if not s.active or exemption_status(s).reason != "Not Exempted":
                    continue
                
                # if one of the faculty's students are presenting, the judge is ineligible.
                student_talking = e.talks.all().filter(student=s).exists()
                if student_talking:
                    a.available[e] = False
                    break
                
                try:
                    pref = TalkPreference.objects.get(student=s, event=e)
                    pref = pref.preference
                except TalkPreference.DoesNotExist:
                    pref = None
                
                # if any of the faculty's students are available, then they have
                # checked that their advisor is available as well.
                if pref != 'cannot':
                    a.available[e] = True
    
    # build up a preference matrix.
    cost_matrix = []

    # the first index is for faculty.
    for a in all_faculty:
        costs = []
        for e in schedulable:
            available = a.available[e]
            costs.append(JUDGE_COST[available])
        cost_matrix.append(costs)

    m = Munkres()
    indexes = m.compute(cost_matrix)
    print_matrix(cost_matrix)

    for row, column in indexes:
        print "Scheduling judge", all_faculty[row], "for talk on", schedulable[column].timestamp
        event = schedulable[column]
        event.judges.add(all_faculty[row])
        event.save()



def sort_by_last_name(students):
    return sorted(students, key=lambda x: x.name.split()[-1])  # sort by last name.
                
def most_recent_semester():
    return Semester.objects.order_by('-year','-month')[0]  
        
def most_recent_occupied_semester():
    semesters = Semester.objects.order_by('-year', '-month')
    occupied = [s for s in semesters if s.event_set.count() > 0]
    return occupied[0]
    
        
def exemption_status(student):
    my_exemptions = Exemption.objects.filter(student=student)
    if not my_exemptions:
        new_exemption = Exemption(student=student, 
                                  semester=most_recent_semester())
        new_exemption.save()
        return new_exemption
    
    # choose the most recent.
    return my_exemptions.order_by('-semester__year', '-semester__month')[0]       

