from functools import wraps
from contextlib import contextmanager


def proxy_factory(type, underlying_getter):
    """
    Create a callable that creates proxies.  This function (#1) will return
    another function (#2) that can be called with a name.  The return value
    will be a proxy function (#3) that simply delegates to the underlying
    object.  The underlying object itself is found through calling
    underlying_getter, and the type of this object must be given (which is
    used to look up whether it's a function or property.
    """
    def proxy_function(name):
        proxy_to = getattr(type, name)

        if isinstance(proxy_to, property):
            def fget(self, *args, **kwargs):
                underlying = underlying_getter(self)
                return proxy_to.fget(underlying, *args, **kwargs)
            the_proxy = property(fget, doc=proxy_to.__doc__)

            if proxy_to.fset is not None:
                def fset(self, *args, **kwargs):
                    underlying = underlying_getter(self)
                    return proxy_to.fset(underlying, *args, **kwargs)
                the_proxy.fset = fset

            if proxy_to.fdel is not None:
                def fdel(self, *args, **kwargs):
                    underlying = underlying_getter(self)
                    return proxy_to.fdel(underlying, *args, **kwargs)
                the_proxy.fdel = fdel
        else:
            @wraps(proxy_to)
            def the_proxy(self, *args, **kwargs):
                underlying = underlying_getter(self)
                return proxy_to(underlying, *args, **kwargs)

        return the_proxy

    return proxy_function


@contextmanager
def patch(obj, attr, value):
    hasOld = False
    old = None
    if hasattr(obj, attr):
        old = getattr(obj, attr)
        hasOld = True

    setattr(obj, attr, value)
    yield

    if hasOld:
        setattr(obj, attr, old)
