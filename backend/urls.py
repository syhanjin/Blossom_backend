"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_nested import routers

import account.views.user
import account.views.class_
import apps.views

router = routers.DefaultRouter()
router.register("users", account.views.user.UserViewSet)
router.register("classes", account.views.class_.ClassViewSet)
router.register("apps", apps.views.AppViewSet)

class_router = routers.NestedDefaultRouter(router, "classes", lookup="class")
class_router.register("students", account.views.class_.ClassStudentViewSet)
class_router.register("teachers", account.views.class_.ClassTeacherViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include('djoser.urls.authtoken')),
]
urlpatterns += [
    path(settings.BASE_URL, include(router.urls)),
    path(settings.BASE_URL, include(class_router.urls)),
]

if settings.DEBUG:
    # TODO: 静态资源访问权限限制！
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
