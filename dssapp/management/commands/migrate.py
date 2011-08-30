from django.core.management.base import BaseCommand, CommandError
from dss.dssapp.models import *
from dss.dssapp.util import *
import re
from datetime import *
import random

def displaymatch(match):
    if match is None:
        return None
    return '<Match: %r, groups=%r>' % (match.group(), match.groups())


    

class Command(BaseCommand):
    args = '<dumpfile>'
    help = 'Migrates an old database into a new database schema.'

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError('Supply a MySQL dump file as an argument.')
    
        dumpfile_name = args[0]
        try:
            f = file(dumpfile_name, 'r')
            lines = f.readlines()
            f.close()
        except IOError as e:
            raise CommandError('Couldn''t read file ' + dumpfile_name)
               
        print "ADDING ADVISORS" + '-' * 60
        self.add_advisors(lines)
        
        print "ADDING STUDENTS" + '-' * 60
        self.add_students(lines)
        
        print "ADDING EXEMPTIONS" + '-' * 60
        self.add_exemptions(lines)
        
        print "ADDING EVENTS" + '-' * 60
        self.add_events(lines)
        
        print "ADDING TALKS" + '-' * 60
        self.add_talks(lines)
        

        
        print "ADDING SOME DEFAULT TEMPLATES"
        submit_prefs = EmailTemplate(subject="DSS Scheduling", name="SubmitPrefs", template="""
{{student.name}},

It is time once again to schedule DSS talks. Our records indicate that you are eligible to give a talk in {{semester}}. This is a great opportunity to practice giving a talk and to share your ideas with the department. It is also required if you have taken any doctoral research credits in the last academic year and you do not meet any of the exemption conditions.

IF YOU ARE EXEMPT FROM GIVING A TALK THIS SEMESTER, PLEASE INDICATE IT ON THE LINK BELOW.

WHAT YOU NEED TO DO:

Access the following web page to record any exemptions and/or scheduling preferences. All the necessary instructions are there:

http://dss.cse.wustl.edu/schedule_preference?semester={{semester.year}}.{{semester.month}}&student_key={{student.web_key}}

IF WE DO NOT HEAR FROM YOU BY 11:59pm WEDNESDAY, SEPTEMBER 7th, WE WILL ASSUME WE CAN SCHEDULE YOU ANY TIME THIS UPCOMING SEMESTER.

Note also that ties in scheduling preferences will be broken in favor of whoever filled out the above web page first. You will thus be more likely to be scheduled when you want if you submit your preferences early.

Please let us know if you have any questions or problems.

Thanks,
{{chairs}}
DSS co-chairs""")
        submit_prefs.save()
        
        submit_abstract = EmailTemplate(subject="Your DSS Abstract", name="SubmitAbstract", template="""
{{student.name}},

This is to remind you that you are scheduled to give a DSS talk on {{student.next_talk.event_set.all.0.timestamp}}.  Please POST A TITLE AND ABSTRACT BY 11:59 PM ON TUESDAY, using the following link:

http://dss.cse.wustl.edu/abstract?talk_id={{student.next_talk.id}}&student_key={{student.web_key}}

so that we can advertise the talk. Also, please remember to NUMBER YOUR SLIDES.

If you are not familiar with the format, DSS talks are 25 minutes, with 5 minutes at the end for questions. This is a strict time limit. Talks should be on original research that you are participating in as a student.  Since the faculty and doctoral students of the department at large will be attending your talk, it is important to write your talk for a general CS audience: do not assume the listeners know or understand the important terms/algorithms/problems/etc in your field. Each talk is judged by three faculty members to help decide the best talk of the semester. The student with this best talk is rewarded with a certificate and a cash-valued prize.

As a final point, we strongly encourage you to practice your talk with an audience, especially with students outside your field, so that you can give the best talk possible.

Thanks,
{{chairs}}
DSS co-chairs""")
        submit_abstract.save()
       
        submit_abstract_reminder = EmailTemplate(subject="Submit your abstract for DSS", name="SubmitAbstractReminder", template="""
{{student.name}},

We still have not received a title and/or abstract from you for your talk this Friday. Please POST A TITLE AND ABSTRACT BY 11:59 PM ON TUESDAY, using the following link:

http://dss.cse.wustl.edu/abstract?talk_id={{student.next_talk.id}}&student_key={{student.web_key}}

Thanks,
{{chairs}}
DSS co-chairs""")
        submit_abstract_reminder.save()
        
        
    def add_advisors(self, lines):
        alert_string = r"INSERT INTO `advisors` VALUES";
        search_string = r"\(((\d+),'(.*?)','(.*?)',(\d)\))"
        my_regex = re.compile(search_string)      
        for line in lines:
            if line.startswith(alert_string):
                match = my_regex.search(line)
                while match:
                    advisor_id = int(match.groups()[1])
                    advisor_name = match.groups()[2]
                    advisor_email = match.groups()[3]
                    advisor_active = match.groups()[4] == '1'
                    
                    new_advisor = Advisor(id=advisor_id, name=advisor_name, email=advisor_email, active=advisor_active)
                    new_advisor.save()
                    print "Added advisor", advisor_name, ", id #", advisor_id
                    
                    line = line.replace(match.groups()[0], '')
                    match = my_regex.search(line)
                    
    def add_exemptions(self, lines):
        alert_string = r"INSERT INTO `exemptions` VALUES";
        
        (1,'2009.7','PhD Dissertation')
        
        search_string = r"\(((\d+),'(.*?)','(.*?)'\))"
        my_regex = re.compile(search_string)      
        for line in lines:
            if line.startswith(alert_string):
                match = my_regex.search(line)
                while match:
                    exemption_id = int(match.groups()[1])
                    exemption_semester = match.groups()[2]
                    exemption_reason = match.groups()[3]
                    conversion = {'exempted': 'Exempted for other reasons', 'not present': 'Not present'}
                    if exemption_reason in conversion:
                        exemption_reason = conversion[exemption_reason]
                    student = Student.objects.get(id=exemption_id)
                    new_exemption = Exemption(student=student, semester=string_to_semester(exemption_semester), reason=exemption_reason)
                    new_exemption.save()
                    print "Added exemption for", student, "during", exemption_semester

                    line = line.replace(match.groups()[0], '')
                    match = my_regex.search(line)
        
        
        
    def add_students(self, lines):
        alert_string = r"INSERT INTO `students` VALUES";
        search_string = r"\(((\d+),'(.*?)',(NULL|'.*?'),'(.*?)',(\d+),'(.*?)',(\d+?),(\d+?)\))"
        my_regex = re.compile(search_string)      
        for line in lines:
            if line.startswith(alert_string):
                match = my_regex.search(line)
                while match:
                    my_id = int(match.groups()[1])
                    my_name = match.groups()[2]
                    if my_name == 'NULL':
                        my_name = None
                    my_nickname = match.groups()[3]
                    my_email = match.groups()[4]
                    #my_email = 'austin.abrams@gmail.com'
                    my_advisor = int(match.groups()[5])
                    my_semester = match.groups()[6]
                    my_active = match.groups()[7] == '1'
                    my_web_key = random.randint(10**8,10**9)  # random 9-digit number
                    
                    semester = string_to_semester(my_semester)
                    new_student, created = Student.objects.get_or_create(id=my_id, name=my_name, nickname=my_nickname, email=my_email, start_semester=semester, active=my_active, web_key=my_web_key )
                    new_student.save()
                    
                    advisor = Advisor.objects.get(id=my_advisor)
                    new_student.advisors.add(advisor)
                    new_student.save()
                    
                    print "Added student", new_student.name , ", advised by", advisor.name

                    line = line.replace(match.groups()[0], '')
                    match = my_regex.search(line)       


    def add_events(self, lines):
        alert_string = r"INSERT INTO `events` VALUES";
        search_string = r"\(((\d+),'(.*?)','(.*?)',('.*?'|NULL),(\d+|NULL),(\d+|NULL),(\d+|NULL)\))"
        my_regex = re.compile(search_string)      
        for line in lines:
            if line.startswith(alert_string):
                match = my_regex.search(line)
                while match:
                    my_id = int(match.groups()[1])
                    my_datetime = match.groups()[2]
                    my_type = match.groups()[3]
                    my_break_title = match.groups()[4]
                    my_judge1_id = match.groups()[5]
                    my_judge2_id = match.groups()[6]
                    my_judge3_id = match.groups()[7]
                    try:
                        timestamp = datetime.strptime(my_datetime, '%Y-%m-%d %H:%M:%S')  
                        semester = timestamp_to_semester(timestamp)
                    
                        print "Adding event for" , semester , "semester...",
                    
                        if my_type == 'dss':
                            new_event = Event(id=my_id, timestamp=timestamp, semester=semester, event_type='DSS')
                            new_event.save()
                            print "DSS talk on", new_event.timestamp, "judged by",
                        
                            for jid in [my_judge1_id, my_judge2_id, my_judge3_id]:
                                if jid == 'NULL':
                                    continue
                                judge = Advisor.objects.get(id=int(jid))
                                new_event.judges.add(judge)
                                print judge,
                            new_event.save()
                            print

                        elif my_type == "break":
                            my_break_title = my_break_title[1:-1]
                            new_event = Event(id=my_id, timestamp=timestamp, semester=semester, title=my_break_title, event_type='Break')
                            new_event.save()
                            print "break for", new_event.title
                    
                        elif my_type == "hot topics":
                            new_event = Event(id=my_id, semester=semester, timestamp=timestamp, event_type='Hot Topics')
                            new_event.save()
                            print "Hot Topics event on", new_event.timestamp
                        
                        else:
                            print "unknown event type."
                        
                    except ValueError:
                        pass
                    
                    
                    line = line.replace(match.groups()[0], '')
                    match = my_regex.search(line)



    def add_talks(self, lines):
        alert_string = r"INSERT INTO `talks` VALUES";
        search_string = r"\(((\d+),(NULL|\d+),(\d+),(\d+),(\d+),'(.*?)','(.*?)',(NULL|'.*?')\))"
        my_regex = re.compile(search_string)      
        for line in lines:
            if line.startswith(alert_string):
                match = my_regex.search(line)
                while match:
                    my_id = int(match.groups()[1])
                    my_event_id = match.groups()[2]
                    my_order_num = match.groups()[3]
                    my_minutes = int(match.groups()[4])
                    my_student_id = match.groups()[5]
                    my_type = match.groups()[6]
                    my_title = match.groups()[7]
                    my_abstract = match.groups()[8]
                    if my_event_id == 'NULL' or my_type != 'dss':
                        event = None
                    else:
                        try:
                            event = Event.objects.get(id=int(my_event_id))
                        except:
                            event = None
                        
                    
                    if my_order_num == 'NULL':
                        my_order_num = None
                    else:
                        my_order_num = int(my_order_num)
                    
                    if my_title == 'NULL':
                        my_title = None                    
                        
                    if my_student_id != 'NULL' and event:
                        student = Student.objects.get(id=my_student_id)
                        my_abstract = my_abstract[1:-1]
                        talk = Talk(id=my_id, student=student, order=my_order_num, minutes=my_minutes, title=my_title, abstract=my_abstract)
                        talk.save()
                        
                        event.save()
                        event.talks.add(talk)
                        event.save()

                        print "Added talk by student", talk.student, ", titled", talk.title
                        

                        
                    line = line.replace(match.groups()[0], '')
                    match = my_regex.search(line)
        
