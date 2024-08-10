# Create your views here.
import os

from django.http import HttpResponseRedirect
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from account.permissions import AdminSuper
from apps.models import App, AppVersion
from apps.serializers import AppCreateSerializer, AppSerializer, AppVersionCreateSerializer, AppVersionSerializer


class AppViewSet(viewsets.ModelViewSet):
    serializer_class = AppSerializer
    queryset = App.objects.all()
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'create':
            return AppCreateSerializer
        elif self.action == 'version_create':
            return AppVersionCreateSerializer
        elif self.action == 'latest':
            return AppVersionSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'version_create']:
            self.permission_classes = [AdminSuper]
        return super().get_permissions()

    @action(methods=['post'], detail=False)
    def version_create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        app = App.objects.get(id=data.pop('app_id'))
        ext = os.path.splitext(data['installer'].name)[1]
        data['installer'].name = f"{app.name}-{data['version_name']}{ext}"
        data['author'] = request.user
        data['app'] = app
        version = AppVersion.objects.create(**data)
        url = request.build_absolute_uri(version.installer.url)
        return Response(
            status=status.HTTP_201_CREATED, data={'installer': url}
        )

    @action(methods=['get'], detail=True)
    def latest(self, request, *args, **kwargs):
        app = self.get_object()
        latest = self.get_serializer(instance=app.versions.all().first())
        data = latest.data
        version_code = request.query_params.get('version_code')
        if version_code:
            # 如果客户端携带了版本号，则返回其距离最新版本的全部更新
            data["updates"] = []
            data["mode"] = set()
            for version in app.versions.filter(version_code__gt=version_code):
                data["updates"].append({
                    "version_code": version.version_code,
                    "version_name": version.version_name,
                    "updates": version.updates
                })
                data["mode"].add(version.mode)
        return Response(data=data)

    @action(methods=['get'], detail=True)
    def get_latest_installer(self, request, *args, **kwargs):
        app = self.get_object()
        latest = app.versions.all().first()
        url = request.build_absolute_uri(latest.installer.url)
        return HttpResponseRedirect(url)
