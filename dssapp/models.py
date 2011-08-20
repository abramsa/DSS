from django.db import models
from datetime import datetime
import os
import settings

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
            
        
class Talk(models.Model):
    student = models.ForeignKey(Student)

    order = models.IntegerField(default=None)
    minutes = models.IntegerField(null=False, default=0)
    title = models.CharField(max_length=200)
    abstract = models.TextField(null=True, default=None)
    
    def abstract_name(self):
        return self.abstract.replace(r'\n','<br/>').replace('\\\'','\'' )
        
    def video_link(self):
        if not settings.VIDEO_ROOT:
            return None
        hosted_root = 'http://www.cse.wustl.edu/video/dsstalks/'
        
        event = self.event_set.get()
        file_name =  event.timestamp.strftime('%Y-%m-%d') + '_' + self.student.name.replace(' ', '_')
        for extension in ['.mp4', '.avi', '.mov', '.m4v', '.wmv', '.mpg',]:
            if os.path.exists(settings.VIDEO_ROOT + file_name + extension):
                return hosted_root + file_name + extension
        else:
            return None
            
    def __str__(self):
        return self.student.name + "'s Talk on " + self.event_set.get().timestamp.strftime('%b %d, %Y')



class Event(models.Model):
    timestamp = models.DateTimeField(null=True)
    semester = models.ForeignKey(Semester)
    title = models.CharField(null=True, max_length=100, default='')
    event_type = models.CharField(null=False, max_length=100)
    
    talks = models.ManyToManyField(Talk)
    judges = models.ManyToManyField(Advisor)
    
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
