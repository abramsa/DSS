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
        
        print "ADDING EVENTS" + '-' * 60
        self.add_events(lines)
        
        print "ADDING TALKS" + '-' * 60
        self.add_talks(lines)
        
       
        
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
                    #advisor_email = match.groups()[3]
                    advisor_email = 'austin.abrams@gmail.com'
                    advisor_active = match.groups()[4] == '1'
                    
                    new_advisor = Advisor(id=advisor_id, name=advisor_name, email=advisor_email, active=advisor_active)
                    new_advisor.save()
                    print "Added advisor", advisor_name, ", id #", advisor_id
                    
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
                    #my_email = match.groups()[4]
                    my_email = 'austin.abrams@gmail.com'
                    my_advisor = int(match.groups()[5])
                    my_semester = match.groups()[6]
                    my_active = match.groups()[7] == '1'
                    my_web_key = random.randint(10**9,10**10)  # random 10-digit number
                    
                    advisor = Advisor.objects.get(id=my_advisor)
                    semester = string_to_semester(my_semester)
                    new_student = Student(id=my_id, name=my_name, nickname=my_nickname, email=my_email, start_semester=semester, active=my_active, web_key=my_web_key )
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
        
