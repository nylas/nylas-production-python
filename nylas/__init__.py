# NOTE: This is copied straight from the nylas python bindings' top-level
# __init__.py. Don't change it unless you want to introduce import bugs
# based on install ordering.
from pkgutil import extend_path
from .client.client import APIClient

# Allow out-of-tree submodules.
__path__ = extend_path(__path__, __name__)
__all__ = ['APIClient']
