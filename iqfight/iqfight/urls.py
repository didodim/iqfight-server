from django.conf.urls import patterns, include, url

from django.contrib import admin
from iqfight_app.views import *
from django.conf.urls.static import static
import settings
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', index),
    # url(r'^blog/', include('blog.urls')),
    url(r'^login/*',login_func),
    url(r'^register/*',register),
    url(r'^is_logged/*',is_logged),
    url(r'^get_games/*',get_games),
    url(r'^open_game/*',open_game),
    url(r'^refresh_game/*',refresh_game),
    url(r'^play/*',play),
    url(r'^new_game/*',new_game),
    url(r'^answer/*',answer),
    url(r'^quit/*',quit),
    url(r'^logout/*',logout_custom),
    url(r'^admin/', include(admin.site.urls)),
    
)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
