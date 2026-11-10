"""Build mode: 'pen' = single sprite drawing with pen stamps (eOS.pmp), 'sprite' = apps + UI elements are sprites."""
import contextlib
import os

MODE = os.environ.get('EOS_MODE', 'pen')


def app_unit(name):
    """sprite build: everything inside belongs to the app's own sprite; pen build: no-op"""
    if MODE == 'sprite':
        import sb3
        return sb3.unit(name)
    return contextlib.nullcontext()
