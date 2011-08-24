from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage
from dss.dssapp.models import *
from dss.dssapp.util import *
from datetime import datetime, timedelta
from django.template import Template, Context


MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6

class Command(BaseCommand):
    help = 'Sends out daily emails, if we need to.'

    def handle(self, *args, **options):
        day = datetime.now().weekday()
        print "CRON EMAIL TIME"
        if day == SUNDAY:
            self.send_abstract_email()
        elif day == TUESDAY:
            self.send_abstract_reminder()
        elif day == THURSDAY or day == FRIDAY:
            self.send_weekly_notice()
        else:
            print "No emails to send today!"
            
    def send_abstract_email(self):
        # send out an email to all students giving a talk later this week about filling in their abstract info.
        today = datetime.now()
        next_week = today + timedelta(days=7)
        events = Event.objects.filter(timestamp__gt=today, timestamp__lt=next_week)
        if len(events) == 0:
            print "No events!"
            return
        
        event = events[0]
        if event.event_type != 'DSS':
            print "Event is", event.event_type, "no need to send out abstract email."
            return
        
        students = [talk.student for talk in event.talks.all()]
        print students
        
        template = EmailTemplate.objects.get(name='SubmitAbstract')
        
        for student in students:
            email_content = Template(template.template).render(Context({'student': student}))
            assert student.email == 'austin.abrams@gmail.com'
        
            email = EmailMessage(template.subject, email_content, to=[student.email])
            email.send()
        
            email_sent = EmailSent(student=student, email=template)
            email_sent.save()
        
    def send_abstract_reminder(self):
        # send out an email to all students giving a talk later this week about filling in their abstract info.
        today = datetime.now()
        next_week = today + timedelta(days=7)
        events = Event.objects.filter(timestamp__gt=today, timestamp__lt=next_week)
        if len(events) == 0:
            print "No events!"
            return
        
        event = events[0]
        if event.event_type != 'DSS':
            print "Event is", event.event_type, "no need to send out abstract email."
            return
        
        students = [talk.student for talk in event.talks.all() if not talk.abstract ]
        print students
        
        template = EmailTemplate.objects.get(name='SubmitAbstractReminder')
        
        for student in students:
            
            email_content = Template(template.template).render(Context({'student': student}))
            assert student.email == 'austin.abrams@gmail.com'
        
            email = EmailMessage(template.subject, email_content, to=[student.email])
            email.send()
        
            email_sent = EmailSent(student=student, email=template)
            email_sent.save()
        
    def send_weekly_notice(self):
        # send out an email to all active, nonexempt, and in-STL students, and all active faculty
        # that DSS is happening this week.
        
        today = datetime.now()
        next_week = today + timedelta(days=7)
        events = Event.objects.filter(timestamp__gt=today, timestamp__lt=next_week)
        if len(events) == 0:
            print "No events!"
            return
        
        event = events[0]
        
        # to = [grads@cse.wustl.edu, csf@cse.wustl.edu]
        to = ["austin.abrams@gmail.com"]
        
        if event.event_type == 'Break':
            email_content = """
Dear students and faculty,

There will be no DSS event this week due to """ + event.break_name + """.

Thanks!
Your friendly DSS chairs"""
            email_subject = "No DSS this week"

        elif event.event_type == 'Hot Topics':
            # If this is a Hot Topics event, you should probably email them yourself.
            # There's just too much variability in one of these events that we can't
            # really boilerplate it.
            return
        
        elif event.event_type == 'DSS':
            email_subject = "DSS Talks Friday"
            
            email_content = """
All,

The following DSS talks will be held starting at 12:30.
Food and refreshments will be provided.

IF ANYBODY RECEIVES THIS EMAIL, PLEASE IGNORE IT.  AUSTIN IS NOT A VERY GOOD PROGRAMMER AND IS VERY SORRY FOR ANY CONFUSION.

Thanks,
Your friendly DSS chairs


"""
            for talk in event.talks.all():
                email_content = email_content + '-' * 40 + "\n\n"
                
                
                if talk.title:
                    email_content = email_content + talk.title
                else:
                    email_content = email_content + "No title provided"
                    
                email_content = email_content + "\n\n"
                email_content = email_content + talk.student.name + "\n"
                email_content = email_content + "Advisor(s):" + talk.student.all_advisors() + "\n\n"

                if talk.abstract:
                    email_content = email_content + talk.abstract
                else:
                    email_content = email_content + "No abstract provided"
            
                email_content = email_content + '\n\n'
                
        email = EmailMessage(email_subject, email_content, to=to)
        email.send()
