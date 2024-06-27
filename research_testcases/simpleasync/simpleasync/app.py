# Testcase motivation from: https://testdriven.io/blog/django-async-views/
import html
import os
import sys

import asyncio
from time import sleep
import requests

from django.utils.decorators import classonlymethod

from django.conf import settings
from django.core.asgi import get_asgi_application
from asgiref.sync import sync_to_async, async_to_sync
from django.http import HttpResponse
from django.urls import path
from django.utils.crypto import get_random_string

from django.views.generic import View

settings.configure(
    DEBUG=(os.environ.get("DEBUG", "") == "1"), # CWEID 215
    # Disable host header validation
    ALLOWED_HOSTS=["*"], # CWEID 183
    # Make this module the urlconf
    ROOT_URLCONF=__name__,
    # We aren't using any security features but Django requires this setting
    SECRET_KEY=get_random_string(50),
)

class AsyncView(View):


    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine
        return view


    # Attack Payload: curl 'http://localhost:8000/async/?name=Mansi<script>alert(1)</script>'
    async def get(self, request, *args, **kwargs):
        await asyncio.sleep(2)
        return HttpResponse('This was run asynchronously, man thats a long word :|' + request.GET.get("name")) # CWEID 80



# Attack Payload: curl 'http://localhost:8000/?name=<script>alert(1)</script>' 
async def index(request):
    name = request.GET.get("name", "World")
    return HttpResponse(f"Hello, " + name + " !!" ) # CWEID 80
    #return HttpResponse(f"Hello, {html.escape(name)}!") # FP

# Attack Payload: curl 'http://localhost:8000/template_index/?name=<script>alert(1)</script>'
async def template_index(request):
    name = request.GET.get("name")
    return HttpResponse(f"Hello, {name}!") # CWEID 80

# Attack Payload: curl 'http://localhost:8000/template_index_fp/?name=<script>alert(1)</script>'
async def template_index_fp(request):
    name = request.GET.get("name")
    return HttpResponse(f"Hello, {html.escape(name)}!") # FP CWEID 80

@sync_to_async
def _get_request_decorator(r):
    return r # tainted propogated

# Attack Payload : curl 'http://localhost:8000/sync_to_async_decorator/?name=<script>alert(1)</script>'
async def sync_to_async_decorator(request):
    r = await _get_request_decorator(request.GET.get("name")) # tainted value passed to decorator
    return HttpResponse(f"Sync to Async via decorator " + r) # CWEID 80


def _get_request_func(r):
    return r # tainted propogated

# Attack Payload: curl 'http://localhost:8000/sync_to_async_func/?name=<script>alert(1)</script>'
async def sync_to_async_func(request):
    r = await sync_to_async(_get_request_func)(request.GET.get("name")) # tainted value passed to function
    return HttpResponse(f"Sync to Async via function " + r) # CWEID 80


# Attack Payload: curl 'http://localhost:8000/async_to_sync_func/?name=<script>alert(1)</script>'
def async_to_sync_func(request):
    sync_data = async_to_sync(_get_async_to_sync_func)(request.GET.get("name")) # Tainted data being propogated to async function
    return HttpResponse("Async to Sync function" + sync_data) # CWEID 80


async def _get_async_to_sync_func(r):
    return r

# Attack Payload: curl 'http://localhost:8000/async_to_syc_decorator/?name=<script>alert(1)</script>'
def async_to_syc_decorator(request):
    sync_data = _get_async_to_sync_decorator(request.GET.get("name")) # tainted data being propogated to decorator
    return HttpResponse("Async to Sync Decorator " + sync_data) # CWEID 80

@async_to_sync
async def _get_async_to_sync_decorator(r):
    return r

urlpatterns = [path("", index),
               path("template_index/",template_index),
               path("template_index_fp/",template_index_fp),
               path("sync_to_async_decorator/",sync_to_async_decorator),
               path("sync_to_async_func/",sync_to_async_func),
               path('async/', AsyncView.as_view(), name='async'),
               path("async_to_sync_func/",async_to_sync_func),
               path("async_to_syc_decorator/",async_to_syc_decorator)
               ]

application = get_asgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
