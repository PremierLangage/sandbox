from django.shortcuts import render

from rest_framework import viewsets

from .serializers import FrozenSerializer


class FrozenViewSet(viewsets.ModelViewSet):
    serializer_class = FrozenSerializer

    def post_pla(self, request, *args, **kwargs):
        pass;

    def post_pl(self, request, *args, **kwargs):
        pass