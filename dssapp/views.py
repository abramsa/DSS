from django.template import Template, Context, RequestContext, TemplateSyntaxError
from dss.dssapp import *
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from util import *
from datetime import *
from django.core.mail import EmailMessage
from django import forms


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
		semester = most_recent_semester()
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
						 
def view_student(request, student_id):
	student = Student.objects.get(id=student_id)
	now = datetime.now()
	return render_to_response('dssapp/view_student.html', {'student': student,
														   'now' : now})

def exemptions(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect("/message?msg=permissions")
	
	# gather all the exemptions for all students.
	nonexempt = []
	graduates = []
	not_present = []
	students = sort_by_last_name(Student.objects.all())
	
	for student in students:
		exemption = exemption_status(student)
		if exemption.reason == 'PhD Dissertation':
			graduates.append(exemption)
		elif exemption.reason == 'Not present':
			not_present.append(exemption)
		else:
			nonexempt.append(exemption)
	return render_to_response('dssapp/exemptions.html', {'nonexempt' : nonexempt,
														 'graduates' : graduates,
														 'not_present' : not_present},
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
		semester = most_recent_semester()
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
	students = sort_by_last_name(students)
	
	graduates = []
	not_present = []
	nonexempt = []
	exempt = []
	for s in students:
		emails = EmailSent.objects.filter(student=s).order_by('-timestamp')
		if len(emails) > 0:
			s.most_recent_email = emails[0]
		else:
			s.most_recent_email = None
		
		if s.most_recent_email and s.most_recent_email.email.name == 'SubmitPrefs':
			prefs = TalkPreference.objects.filter(student=s, event__semester=most_recent_semester())
			s.responded = TalkPreference.objects.filter(student=s, event__semester=most_recent_semester()).exists()
		elif s.most_recent_email and s.most_recent_email.email.name == 'SubmitAbstract' and s.next_talk():
			s.responded = s.next_talk().abstract != None
		else:
			s.responded = None
			
		exemption = exemption_status(s)
		if exemption.reason == 'PhD Dissertation':
			graduates.append(s)
		elif exemption.reason == 'Not present':
			not_present.append(s)
		elif exemption.reason == 'Not Exempted':
			nonexempt.append(s)
		else:
			s.reason = exemption.reason
			exempt.append(s)
	students = nonexempt + exempt + not_present + graduates
				
	return render_to_response('dssapp/student_dashboard.html', {'nonexempt': nonexempt, 'exempt': exempt, 'graduates': graduates, 'not_present': not_present, 'students': students},
								context_instance=RequestContext(request))
	
def email_students(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('message?msg=permissions')
	
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
	if not request.user.is_authenticated():
		return HttpResponseRedirect('message?msg=permissions')
	
	students = []
	for param in request.POST:
		if param.endswith('box'):
			student_id = int(param.replace('box', ''))
			students.append(Student.objects.get(id=student_id))
			
	semester = most_recent_semester()
	
	schedule_semester_students(semester, students)
	
	return HttpResponseRedirect('schedule')
	
def schedule_judges(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('message?msg=permissions')
	
	schedule_semester_judges(most_recent_semester())
	schedule_semester_judges(most_recent_semester())
	schedule_semester_judges(most_recent_semester())
	
	return HttpResponseRedirect('schedule')
	
	
def send_email(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('message?msg=permissions')
	
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
			
			email_content = Template(template).render(Context({'student': student, 'chairs': settings.DSS_CHAIRS, 'semester': most_recent_semester()}))
			
			email = EmailMessage(subject, email_content, to=[student.email])
			email.send()
			
			email_sent = EmailSent(student=student, email=template_obj)
			email_sent.save()	   
				  
	return HttpResponseRedirect('student_dashboard')
			
def schedule_preference(request):
	semester_str = request.GET['semester']
	semester = string_to_semester(semester_str)
	
	student_key = request.GET['student_key']
	student = get_object_or_404(Student, web_key=student_key)
	
	events = Event.objects.filter(semester=semester, event_type="DSS").order_by('timestamp')
	for e in events:
		try:
			preference = TalkPreference.objects.get(student=student, event=e)
			e.pref = preference.preference
		except TalkPreference.DoesNotExist:
			e.pref = 'available'
	
	return render_to_response('dssapp/schedule_preference.html', {'semester': semester, 'student': student, 'events': events},
							  context_instance=RequestContext(request))
	
def abstract(request):
	talk_id = request.GET.get('talk_id', None)
	student_key = request.GET.get('student_key', None)
	if not student_key or not talk_id:
		return HttpResponseRedirect('schedule')
		
	student = get_object_or_404(Student, web_key=student_key)
	talk = get_object_or_404(Talk, id=int(talk_id))
	if student != talk.student:
		return HttpResponseRedirect('schedule')
	
	deadline = talk.event_set.get().timestamp - timedelta(days=3)
	
	return render_to_response('dssapp/abstract.html', {'talk' : talk, 'student' : student, 'deadline' : deadline},
							  context_instance=RequestContext(request))
	
	
def admin_preferences(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('message?msg=permissions')
	
	if 'semester' in request.GET:
		semester_str = request.GET['semester']
		semester = string_to_semester(semester_str)
	else:
		# what's the most recent semester.
		semester = most_recent_semester()
		return HttpResponseRedirect('admin_preferences?semester=' + str(semester.year) + '.' + str(semester.month))
	
	students = Student.objects.filter(active=True)[:]
	students = sorted(students, key=lambda x: x.name.split()[-1])  # sort by last name.
	students = [student for student in students if exemption_status(student).reason == 'Not Exempted']
	
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
	if not request.user.is_authenticated():
		return HttpResponseRedirect('message?msg=permissions')
	
	try:
		template = Template(request.GET['template'])
		student_id = request.GET['student_id']
		student = Student.objects.get(id=int(student_id))
		result = template.render(Context({'student': student, 'chairs': settings.DSS_CHAIRS, 'semester': most_recent_semester()}))
	except TemplateSyntaxError as e:
		result = 'Template syntax error: ' + str(e)
	
	return HttpResponse(result)
	
def message(request):
	msg_type = request.GET['msg']
	messages = {'prefsubmit': 'Thank you for submitting your preferences.',
				'abstractsubmit': 'Thank you for sumitting your abstract.',
				'permissions': 'You do not have the necessary permissions to view this page.'}
	return render_to_response('dssapp/message.html', {'message': messages[msg_type]})
   
class DSSVideoForm(forms.Form):
	video = forms.Field(widget=forms.FileInput, required=True)	 
 
def upload(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('message?msg=permissions')
	
	talks = Talk.objects.all().order_by('-id')[0:25]
	form = DSSVideoForm()
	
	return render_to_response('dssapp/upload.html', {'talks': talks, 'form': form},
								context_instance=RequestContext(request))
	
def upload_video(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('message?msg=permissions')
	video = request.FILES['video']
	talk_id = int(request.POST['talk_id'])
	talk = Talk.objects.get(id=talk_id)
	
	extension = video.name[video.name.find('.'):]
	file_name = settings.VIDEO_ROOT + talk.file_name() + extension
	
	destination = open(file_name, 'wb+')
	for chunk in video.chunks():
		destination.write(chunk)
	destination.close()
	
	return HttpResponseRedirect('schedule')


def admin(request):
	if request.user.is_authenticated():
		return render_to_response('dssapp/admin.html', {'admin': True})
	else:
		return render_to_response('dssapp/admin.html', {'admin': False})
		
	  
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
	SPRING_END_DATE	  = datetime(month=4, day=30, year=year, hour=12, minute=30)

	FALL_START_DATE	  = datetime(month=9, day=15, year=year, hour=12, minute=30)
	FALL_END_DATE	  = datetime(month=12, day=5, year=year, hour=12, minute=30)
	
	SUMMER_START_DATE = datetime(month=6, day=1, year=year, hour=12, minute=30)
	SUMMER_END_DATE	  = datetime(month=8, day=31, year=year, hour=12, minute=30)
	
	
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
	
	exemption = exemption_status(student)
	exemption.reason = 'Not Exempted'
	exemption.save()
	
	for pref in preferences:
		event_id = int(pref[0:-len("preference")])
		event = Event.objects.get(pk=event_id)
		try:
			talk_preference, created = TalkPreference.objects.get_or_create(student=student, event=event,
							defaults={'preference': request.POST[pref]})
			if not created:
				talk_preference.preference = request.POST[pref]
			
		except TalkPreference.MultipleObjectsReturned:
			TalkPreference.objects.filter(student=student, event=event).delete()
			talk_preference = TalkPreference(student=student, event=event)
		
		talk_preference.save()
		
	return HttpResponseRedirect("/message?msg=prefsubmit")
	
def submit_abstract(request):
	talk_id = request.POST.get('talk_id', None)
	if talk_id == None:
		return HttpResponseRedirect("schedule")
	
	talk = get_object_or_404(Talk, id=int(talk_id))
	abstract = request.POST.get('abstract', None)
	title = request.POST.get('title', None)
	
	talk.abstract = abstract
	talk.title = title
	talk.save()

	return HttpResponseRedirect("/message?msg=abstractsubmit")
	
	
def add_exemption(request):
	student_id = request.POST.get('student')
	reason = request.POST.get('reason')
	semester = most_recent_semester()
	student = Student.objects.get(id=int(student_id))
	
	exemption, created = Exemption.objects.get_or_create(student=student, semester=semester)
	exemption.reason = reason
	exemption.save()
	
	if 'redirect' in request.POST:
		# this came from the preference submission page, so we should make sure that this student
		# is not available for any DSS talks.
		events = Event.objects.filter(semester=semester)
		for e in events:
			talk_preference, created = TalkPreference.objects.get_or_create(student=student, event=e,  defaults={'preference': 'cannot'})
			if not created:
				talk_preference.preference = 'cannot'
				
			talk_preference.save()
		
		
		return HttpResponseRedirect('/message?msg=prefsubmit')
	else:
		return HttpResponseRedirect("exemptions")
