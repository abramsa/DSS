from django.template import Template, Context, RequestContext, TemplateSyntaxError
from dss.dssapp import *
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from util import *
from datetime import *
from django.core.mail import EmailMessage

import settings


# Front-facing views ------------------------------------------------
def schedule(request):
    
    semester_string = request.GET.get('semester', None)
    semester = None
    error = ''
    events = []
    
    if semester_string:
        semester = string_to_semester(semester_string)
        
        # get all the events this semester.
        events = Event.objects.filter(semester=semester).order_by('timestamp')
        
    else:
        # what's the most recent semester.
        semester = Semester.objects.order_by('-year')[0]
        return HttpResponseRedirect('schedule?semester=' + str(semester.year) + '.' + str(semester.month))
       
    
    all_semesters = []
    for sem in Semester.objects.all().order_by('year', 'month'):
        # make sure the semester has at least some events.
        if Event.objects.filter(semester=sem).exists():
            all_semesters.append(sem)
    
    

    return render_to_response('dssapp/schedule.html', {'events': events,
                                                       'semester': semester,
                                                       'all_semesters': all_semesters},
                               context_instance=RequestContext(request))
                               
                               
def admin_schedule(request):
    # make sure the person is logged in.
    if not request.user.is_authenticated():
        return HttpResponseRedirect('admin/')
        
    semester_string = request.GET.get('semester', None)
    semester = None
    events = []

    if semester_string:
        semester = string_to_semester(semester_string)
    
        # get all the events this semester.
        events = Event.objects.filter(semester=semester).order_by('timestamp')
        for ev in events:
            if ev.event_type == 'DSS' and len(ev.talks.all()) > 0:
                ev.deletable = False
            else:
                ev.deletable = True
    else:
        # what's the most recent semester.
        semester = Semester.objects.order_by('-year')[0]
        return HttpResponseRedirect('admin_schedule?semester=' + str(semester.year) + '.' + str(semester.month))


    all_semesters = []
    for sem in Semester.objects.all().order_by('year', 'month'):
        # make sure the semester has at least some events.
        if Event.objects.filter(semester=sem).exists():
            all_semesters.append(sem)

    return render_to_response('dssapp/admin_schedule.html', {'events': events,
                                                       'semester': semester,
                                                       'all_semesters': all_semesters},
                               context_instance=RequestContext(request))
                               
          
def student_dashboard(request):
    # make sure the person is logged in.
    if not request.user.is_authenticated():
        return HttpResponseRedirect('admin/')
        
    students = Student.objects.filter(active=True)[:]
    students = sorted(students, key=lambda x: x.name.split()[-1])  # sort by last name.
    for s in students:
        emails = EmailSent.objects.filter(student=s).order_by('-timestamp')
        if len(emails) > 0:
            s.most_recent_email = emails[0]
        else:
            s.most_recent_email = None
        s.responded = None
            
    return render_to_response('dssapp/student_dashboard.html', {'students': students},
                                context_instance=RequestContext(request))
    
def email_students(request):
    students = []
    for param in request.POST:
        if param.endswith('box'):
            student_id = int(param.replace('box', ''))
            students.append(Student.objects.get(id=student_id))
            
    templates = EmailTemplate.objects.all()
    for t in templates:
        t.template = t.template.replace('\n','@NEWLINE@').replace('\r','@CARRAIGE@').replace('{','\{').replace('}','\}').replace("'","\\'").replace('"','\\"')
    return render_to_response('dssapp/email_students.html', {'students': students, 'templates': templates},
                              context_instance=RequestContext(request))
                              
def schedule_students(request):
    students = []
    for param in request.POST:
        if param.endswith('box'):
            student_id = int(param.replace('box', ''))
            students.append(Student.objects.get(id=student_id))
            
    semester_str = '2011.09'
    semester = string_to_semester(semester_str)
    
    schedule_semester(semester, students)
    
def send_email(request):
    template = request.POST['template']
    subject = request.POST['subject_line']
    
    # save the template.
    template_kind = request.POST['template_kind']
    template_name = request.POST['template_name']
    
    template_obj = None
    if template_kind == 'custom':
        template_obj = EmailTemplate(template=template, subject=subject, name=template_name)
        template_obj.save()
    else:
        template_obj = EmailTemplate.objects.get(id=int(template_kind))
        template_obj.template = template
        template_obj.subject = subject
        template_obj.save()
    
    for param in request.POST:
        if param.startswith('student'):
            student_id = int(param.replace('student', ''))
            student = Student.objects.get(id=student_id)
            
            email_content = Template(template).render(Context({'student': student}))
            assert student.email == 'austin.abrams@gmail.com'
            
            email = EmailMessage(subject, email_content, to=[student.email])
            email.send()
            
    return HttpResponseRedirect('student_dashboard')
            
def schedule_preference(request):
    semester_str = request.GET['semester']
    semester = string_to_semester(semester_str)
    
    student_key = request.GET['student_key']
    student = get_object_or_404(Student, web_key=student_key)
    
    events = Event.objects.filter(semester=semester, event_type="DSS").order_by('timestamp')
    
    
    return render_to_response('dssapp/schedule_preference.html', {'semester': semester, 'student': student, 'events': events},
                              context_instance=RequestContext(request))
    
    
    
def admin_preferences(request):
    semester_str = request.GET['semester']
    semester = string_to_semester(semester_str)
    
    students = Student.objects.filter(active=True)[:]
    students = sorted(students, key=lambda x: x.name.split()[-1])  # sort by last name.
    
    events = Event.objects.filter(event_type='DSS', semester=semester)
    for s in students:
        s.preferences = []
        for e in events:
            try:
                pref = TalkPreference.objects.get(student=s, event=e)
            except TalkPreference.DoesNotExist:
                pref = None
            s.preferences.append(pref)
            
    return render_to_response('dssapp/admin_preferences.html', {'students': students, 'events': events})
    


def render_email_template(request):
    try:
        template = Template(request.GET['template'])
        student_id = request.GET['student_id']
        student = Student.objects.get(id=int(student_id))
        result = template.render(Context({'student': student}))
    except TemplateSyntaxError as e:
        result = 'Template syntax error: ' + str(e)
    
    return HttpResponse(result)
    
def message(request):
    msg_type = request.GET['msg']
    messages = {'prefsubmit': 'Thank you for submitting your preferences.'}
    return render_to_response('dssapp/message.html', {'message': messages[msg_type]})
    

          
# Database modification views ---------------------------------------
def create_event(request):
    # make sure the person is logged in.
    if not request.user.is_authenticated():
        return HttpResponseRedirect('admin/')
    
    event_type = request.POST.get('event_type', None)
    date_string = request.POST.get('date', None)
    time_string = request.POST.get('time', None)
    event_title = request.POST.get('event_title', None)

    timestamp = datetime.strptime(date_string + ' ' + time_string, r'%m/%d/%Y %I:%M%p')
    semester = timestamp_to_semester(timestamp)
    
    ev = Event(timestamp=timestamp, semester=semester, title=event_title, event_type=event_type);
    ev.save()
    
    return HttpResponseRedirect('admin_schedule?semester=' + str(semester.year) + '.' + str(semester.month))

def delete_event(request):
    # make sure the person is logged in.
    if not request.user.is_authenticated():
        return HttpResponseRedirect('admin/')
        
    event_id = request.POST.get('event_id', None)
    
    event = Event.objects.get(id=int(event_id))
    semester = event.semester
    
    # verify that the event has no scheduled talks.
    if (len(event.talks.all()) == 0):
        event.delete()
        
    return HttpResponseRedirect('admin_schedule?semester=' + str(semester.year) + '.' + str(semester.month))
      
          
                               
def create_schedule(request):
    # make sure the person is logged in.
    if not request.user.is_authenticated():
        return HttpResponseRedirect('admin/')
        
    season = request.POST.get('season', None)
    year = int(request.POST.get('year', -1))
    
    # some defaults.
    SPRING_START_DATE = datetime(month=1, day=23, year=year, hour=12, minute=30)
    SPRING_END_DATE   = datetime(month=4, day=30, year=year, hour=12, minute=30)

    FALL_START_DATE   = datetime(month=9, day=15, year=year, hour=12, minute=30)
    FALL_END_DATE     = datetime(month=12, day=5, year=year, hour=12, minute=30)
    
    SUMMER_START_DATE = datetime(month=6, day=1, year=year, hour=12, minute=30)
    SUMMER_END_DATE   = datetime(month=8, day=31, year=year, hour=12, minute=30)
    
    
    if season == 'spring':
        semester_string = str(year) + '.1'
    elif season == 'fall':
        semester_string = str(year) + '.9'
    else:
        semester_string = str(year) + '.6'
        
    # grab the semester.
    semester = string_to_semester(semester_string)
    
    # if there are no events...
    if not Event.objects.filter(semester=semester).exists():
        # create a DSS event every Friday during the season.
        if season == 'spring':
            start_date = SPRING_START_DATE
            end_date = SPRING_END_DATE
        elif season == 'fall':
            start_date = FALL_START_DATE
            end_date = FALL_END_DATE
        else:
            start_date = SUMMER_START_DATE
            end_date = SUMMER_END_DATE
        
        day = start_date
        while day <= end_date:
            if day.weekday() == 4: # Friday
                event = Event(timestamp=day, semester=semester, event_type="DSS")
                event.save()
            
            day = day + timedelta(days=1)
    
    return HttpResponseRedirect("/admin_schedule?semester=" + semester_string)
            
def submit_preferences(request):
    student_id = int(request.POST['student_id'])
    student = Student.objects.get(pk=student_id)
    
    preferences = [x for x in request.POST if x.endswith('preference') ]
    
    for pref in preferences:
        event_id = int(pref[0:-len("preference")])
        event = Event.objects.get(pk=event_id)

        talk_preference, created = TalkPreference.objects.get_or_create(student=student, event=event,
                          defaults={'preference': request.POST[pref]})
        if not created:
            talk_preference.preference = request.POST[pref]
        
        talk_preference.save()
        
    return HttpResponseRedirect("/message?msg=prefsubmit")

    
    
    
    
    
    
    
    
    
    