from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    #path('admin/', admin.site.urls),

    #  Custom logout before anything else
   # path('site-logout/', auth_views.LogoutView.as_view(), name='site_logout'),
    #  path('logout/', auth_views.LogoutView.as_view(), name='logout'),
   #h('site-logout/', auth_views.LogoutView.as_view(), name='site_logout'),

    # Homepage app URLs
    path('', include('homepage.urls')),
path('adminpanel/', include('adminpanel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)