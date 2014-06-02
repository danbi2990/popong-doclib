#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from functools import wraps

def polymorph(base, *signature):
    def decorator(f):
        if not hasattr(base, 'dict'):
            setattr(base, 'dict', {})
        base.dict[tuple(signature)] = f

        @wraps(f)
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)

        return decorated

    return decorator
