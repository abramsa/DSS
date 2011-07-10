from django.conf.urls.defaults import *
import settings
import dssapp.views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^dss/', include('dss.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    (r'^$', dssapp.views.schedule),
    (r'^schedule$', dssapp.views.schedule),
    (r'^schedule_preference$', dssapp.views.schedule_preference),
    
    
    (r'^admin_schedule$', dssapp.views.admin_schedule),
    (r'^student_dashboard$', dssapp.views.student_dashboard),
        
    (r'^create_schedule$', dssapp.views.create_schedule),
    (r'^create_event$', dssapp.views.create_event),
    (r'^delete_event$', dssapp.views.delete_event),
    
    (r'^email_students$', dssapp.views.email_students),
    (r'^render_email_template$', dssapp.views.render_email_template),
    (r'^send_email$', dssapp.views.send_email),

    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
                'document_root': settings.MEDIA_ROOT,
            }),
)
