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
        print "CRON EMAIL TIME", datetime.now()
        if day == SUNDAY:
            self.send_abstract_email()
        elif day == TUESDAY:
            self.send_abstract_reminder()
        elif day == THURSDAY:
            self.send_weekly_notice()
        elif day == FRIDAY:
            self.send_weekly_notice()
            self.send_pizza_order()
        else:
            print "No emails to send today!"
            
    def send_abstract_email(self):
        print "sending abstract email..."
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
            email_content = Template(template.template).render(Context({'student': student, 'chairs': settings.DSS_CHAIRS, 'semester': most_recent_semester()}))
        
            #to = [student.email]
            to = ['austin.abrams@gmail.com']
        
            email = EmailMessage(template.subject, email_content, to=[student.email])
            email.send()
        
            email_sent = EmailSent(student=student, email=template)
            email_sent.save()
            print "sent to ", student.email
        
    def send_abstract_reminder(self):
        print "sending abstract reminder email..."
        
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
            
            email_content = Template(template.template).render(Context({'student': student, 'chairs': settings.DSS_CHAIRS, 'semester': most_recent_semester()}))
        
            #to = [student.email]
            to = ['austin.abrams@gmail.com']
        
            email = EmailMessage(template.subject, email_content, to=to)
            email.send()
        
            email_sent = EmailSent(student=student, email=template)
            email_sent.save()
            
            print "sent to ", student.email
            
        
    def send_weekly_notice(self):
        print "Sending weekly notice..."
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
        to = ['austin.abrams@gmail.com']
        
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
            print "Hot Topics...send it yourself!"
            return
        
        elif event.event_type == 'DSS':
            email_subject = "DSS Talks Friday"
            
            email_content = """
All,

The following DSS talks will be held starting at 12:30.
Food and refreshments will be provided.

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
        print "Sent to", to


    def send_pizza_order(self):
        print "Sending pizza order..."
        # send out the pizza order.

        today = datetime.now()
        next_week = today + timedelta(days=7)
        events = Event.objects.filter(timestamp__gt=today, timestamp__lt=next_week)
        if len(events) == 0:
            print "No events!"
            return

        event = events[0]
        if event.event_type == "Break":
            print "It's a break!"
            return

        # to = ["eckmank@seas.wustl.edu"]
        to = ['austin.abrams@gmail.com']

        try:
            template = EmailTemplate.objects.get(name='PizzaOrder')
        except EmailTemplate.DoesNotExist:
            template = EmailTemplate(name='PizzaOrder', subject="DSS Pizza Order", template="""
Hi Kelli -

Would you please place the order for Friday's Doctoral Student seminar?
Please order for 12 pm.

Our order is for 13 pizzas, all large original crust:

2 extra cheese
1 bacon
2 sausage
3 pepperoni
1 black olive
1 green peppers
1 mushrooms
1 onions
1 tomatoes

Thanks,
{{chairs}}
""")
            template.save()
        email_content = Template(template.template).render(Context({'student': None, 'chairs': settings.DSS_CHAIRS, 'semester': most_recent_semester()}))
        
        email = EmailMessage(template.subject, email_content, to=to)
        email.send()
