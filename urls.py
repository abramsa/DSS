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
    (r'^admin$', dssapp.views.admin),
    (r'^manage/', include(admin.site.urls)),
    
    (r'^student/(?P<student_id>\d+)$', dssapp.views.view_student),
    
    (r'^$', dssapp.views.schedule),
    (r'^schedule$', dssapp.views.schedule),
    (r'^schedule_preference$', dssapp.views.schedule_preference),
    (r'^message$', dssapp.views.message),
    (r'^abstract$', dssapp.views.abstract),
    (r'^exemptions$', dssapp.views.exemptions),
    
    (r'^admin_schedule$', dssapp.views.admin_schedule),
    (r'^student_dashboard$', dssapp.views.student_dashboard),
    (r'^admin_preferences$', dssapp.views.admin_preferences),
    (r'^schedule_students$', dssapp.views.schedule_students),
        
    (r'^create_schedule$', dssapp.views.create_schedule),
    (r'^create_event$', dssapp.views.create_event),
    (r'^delete_event$', dssapp.views.delete_event),
    (r'^submit_preferences$', dssapp.views.submit_preferences),
    (r'^submit_abstract$', dssapp.views.submit_abstract),
    (r'^add_exemption$', dssapp.views.add_exemption),
    
    
    (r'^email_students$', dssapp.views.email_students),
    (r'^render_email_template$', dssapp.views.render_email_template),
    (r'^send_email$', dssapp.views.send_email),

    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
                'document_root': settings.MEDIA_ROOT,
            }),
)
