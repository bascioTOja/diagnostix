"""
URL configuration for diagnostix project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path

from core.admin_site import diagnostix_admin_site
import appointments.admin  # noqa: F401
import inspections.admin  # noqa: F401
import notifications.admin  # noqa: F401
import users.admin  # noqa: F401
import vehicles.admin  # noqa: F401

urlpatterns = [
    path('', include('core.web.urls')),
    path('admin/', diagnostix_admin_site.urls),
    path('api/', include(('api.urls', 'api'), namespace='v1')),
    path('api/v1/', include('api.urls')),
]
