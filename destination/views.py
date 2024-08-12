from rest_framework import mixins, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from destination.models import City, School
from destination.serializers import CitySimpleSerializer, SchoolSimpleSerializer


class Pagination(PageNumberPagination):
    page_size = 20
    max_page_size = 50


class SchoolViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = School.objects.all()
    permission_classes = [AllowAny]
    serializer_class = SchoolSimpleSerializer
    lookup_field = 'id'
    filter_backends = [SearchFilter]
    search_fields = ["name"]
    pagination_class = Pagination


class CityViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = City.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CitySimpleSerializer
    lookup_field = 'id'
    filter_backends = [SearchFilter]
    search_fields = ["name"]
    pagination_class = Pagination
