from django.db import models
from datetime import datetime
import os
import settings
import util

class Semester(models.Model):
    year = models.IntegerField(default=1970)
    month = models.IntegerField(default=1)
    
    def __str__(self):
        return str(self.year) + '.' + str(self.month)
        
    def season(self):
        seasons = {1: "Spring", 6: "Summer", 9: "Fall", 12: "Winter"}
        if self.month in seasons:
            return seasons[self.month]
        else:
            d = datetime(month=self.month, year=self.year, day=1)
            return d.strftime('%B')
    def __str__(self):
        return self.season() + " " + str(self.year)

class Advisor(models.Model):
    name = models.CharField(null=False, max_length=100)
    email = models.CharField(max_length=150)
    active = models.BooleanField(null=False, default=False)
    
    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(null=False, max_length=200)
    nickname = models.CharField(max_length=100)
    email = models.CharField(max_length=150)
    advisors = models.ManyToManyField(Advisor)
    start_semester = models.ForeignKey(Semester)
    active = models.BooleanField()
    web_key = models.IntegerField()
    
    def __str__(self):
        return self.name
        
    def all_advisors(self):
        s = ""
        advisors = self.advisors.all()
        for i in range(len(advisors)):
            s += advisors[i].name
            if (len(advisors) == 2 and i == 0):
                s += " and "
            elif (i < len(advisors) - 2):
                s += ", "
            elif (i == len(advisors) - 2):
                s += ", and "
        return s
        
    def next_talk(self):
        all_my_talks = Talk.objects.filter(student=self)
        for talk in all_my_talks:
            if talk.event_set.get().timestamp > datetime.now():
                return talk
        return None
       
    def last_talk(self):
        all_my_talks = Talk.objects.filter(student=self)
        latest_talk = None
        for talk in all_my_talks:
            timestamp = talk.event_set.get().timestamp
            if timestamp < datetime.now():
                if latest_talk == None or latest_talk.event_set.get().timestamp < timestamp:
                    latest_talk = talk
        return latest_talk
            
        
class Talk(models.Model):
    student = models.ForeignKey(Student)

    order = models.IntegerField(default=None)
    minutes = models.IntegerField(null=False, default=0)
    title = models.CharField(max_length=200)
    abstract = models.TextField(null=True, default=None)
    
    def abstract_name(self):
        return self.abstract.replace(r'\n','<br/>').replace('\\\'','\'' )
        
    def file_name(self):
        event = self.event_set.get()
        return event.timestamp.strftime('%Y-%m-%d') + '_' + self.student.name.replace(' ', '_')
        
    def video_link(self):
        if not settings.VIDEO_ROOT:
            return None
        hosted_root = 'http://www.cse.wustl.edu/video/dsstalks/'
        
        file_name =  self.file_name()
        for extension in ['.mp4', '.avi', '.mov', '.m4v', '.wmv', '.mpg',]:
            if os.path.exists(settings.VIDEO_ROOT + file_name + extension):
                return hosted_root + file_name + extension
        return None
            
    def __str__(self):
        try:
            event = self.event_set.get()
            return self.student.name + "'s Talk on " + event.timestamp.strftime('%b %d, %Y')
        except Event.DoesNotExist:
            return self.student.name + "'s Talk"

class Exemption(models.Model):
    student = models.ForeignKey(Student)
    semester = models.ForeignKey(Semester)
    reason = models.CharField(max_length=1024, default='Not Exempted')

class Event(models.Model):
    timestamp = models.DateTimeField(null=True)
    semester = models.ForeignKey(Semester)
    title = models.CharField(null=True, max_length=100, default='', blank=True)
    event_type = models.CharField(null=False, max_length=100)
    
    talks = models.ManyToManyField(Talk, blank=True)
    judges = models.ManyToManyField(Advisor, blank=True)
    
    def __str__(self):
        return self.event_type + " on " + self.timestamp.strftime('%b %d %Y ')
        
    def current(self):
        now = datetime.now()
        return (now < self.timestamp) and (self.timestamp - now) > 7
    
class TalkPreference(models.Model):
    student = models.ForeignKey(Student)
    event = models.ForeignKey(Event)
    preference = models.CharField(null = False, max_length = 25)
    
    def __str__(self):
        return str(self.student) + "'s preference for event " + str(self.event) + ": " + self.preference
        
    def color(self):
        colors = {'prefer': 'green', 'available': white, 'cannot': red}

class EmailTemplate(models.Model):
    template = models.TextField()
    subject = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    
class EmailSent(models.Model):
    student = models.ForeignKey(Student)
    email = models.ForeignKey(EmailTemplate)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.timestamp.strftime('%b %d %H:%M:%S') + "," + self.email.subject + ""
