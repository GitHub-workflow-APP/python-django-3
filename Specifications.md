# Introduction

This research spec updates our current support to [Django 3.1](https://docs.djangoproject.com/en/3.1/). It assumes complete support of [Django 2.x specs](https://veracode.atlassian.net/wiki/spaces/RES/pages/10918665/Django+2.x+Research), [Django 1.x specs](https://veracode.atlassian.net/wiki/spaces/RES/pages/10917825/Django+1.x+Research),[Django Normalizer support](https://veracode.atlassian.net/wiki/spaces/RES/pages/10917822/Django+1.x+Normalizer+Additions) and also [python 3.8 spec](https://veracode.atlassian.net/wiki/spaces/RES/pages/10917854/Python3+Refresh+v3.5+-+v3.8). 

# Modeling Information

## Asynchronous Support

Asynchronous support of Django framework is not yet available for all layers. So, far its mainly for identifying views and for rest just using `sync_to_async` adapters. So, for the time being our main objective would be to make sure we identify all entry points and propogate taint accordingly.

Asynchronous functionality of Django is entirely based on python's co-routine support. Please refer: [Python 3.8 Support](https://veracode.atlassian.net/wiki/spaces/RES/pages/10917854/Python3+Refresh+v3.5+-+v3.8#Python3Refreshv3.5-v3.8-AsynchronousI/O:).  

### Identifying Views:

- Function based views tagged as `async` should still be considered valid entry points

```
# Entry Point
async def index(request):
    name = request.GET.get("name", "World")
    return HttpResponse(f"Hello, " + name + " !!" ) # CWEID 80
```
- Class based views with entry point classes tagged as `async`, should still be considered a valid entry points

```
class AsyncView(View):
    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine
        return view

	# Class Based View, should be considered a valid entry point
    async def get(self, request, *args, **kwargs):
        await asyncio.sleep(2)
        return HttpResponse('This was run asynchronously ' + request.GET.get("name")) # CWEID 80


```

### Taint Analysis (Propogation):

- All functions called by [`sync_to_async`](https://docs.djangoproject.com/en/3.1/topics/async/#sync-to-async) and [`async_to_sync`](https://docs.djangoproject.com/en/3.1/topics/async/#async-to-sync) adapters should be treated as propogators

```
async def sync_to_async_func(request):
    r = await sync_to_async(_get_request_func)(request.GET.get("name")) # tainted value passed to function
    return HttpResponse(f"Sync to Async via function " + r) # CWEID 80

# Should be considered propogator
def _get_request_func(r):
    return r # tainted propogated
```
- All functions decorated with [`sync_to_async`](https://docs.djangoproject.com/en/3.1/topics/async/#sync-to-async) and [`async_to_sync`](https://docs.djangoproject.com/en/3.1/topics/async/#async-to-sync) should be treated as propogators

```
# Should be considered propogators
async def sync_to_async_decorator(request):
    r = await _get_request_decorator(request.GET.get("name")) # tainted value passed to decorator
    return HttpResponse(f"Sync to Async via decorator " + r) # CWEID 80
    
@sync_to_async
def _get_request_decorator(r):
    return r # tainted propogated
```


## Settings Configurations

In Django 3, [django.conf.settings](https://docs.djangoproject.com/en/3.1/topics/settings/#custom-default-settings) is also used as an object with setting individual properties directly in python code. 

**Note:** This doesn't negate using settings as a module as specc'ed in [Django 2.x Specs](https://veracode.atlassian.net/wiki/spaces/RES/pages/10918665/Django+2.x+Research#Django2.xResearch-Miscellaneousfindings)

```
settings.configure(
    DEBUG=(os.environ.get("DEBUG", "") == "1"), # CWEID 215
    ALLOWED_HOSTS=["*"], # CWEID 183
)
```

# References

1. [Django 3.x Asynchronous Support](https://docs.djangoproject.com/en/3.1/topics/async/#sync-to-async)
2. [Django 3.0 release notes](https://docs.djangoproject.com/en/3.1/releases/3.0/)
3. [Django 3.1 release notes](https://docs.djangoproject.com/en/3.1/releases/3.1/)
4. [All releases](https://docs.djangoproject.com/en/3.1/releases/)

# ToDo

