"""
Puts TAP interfaces wrapped by netlib to use

Designed to work with the Corundum testing framework, hence the name:
it's a play on topaz, another mineral, like Corundum
"""

#ruff: noqa F401

from tapaz.client import TAPClient
from tapaz.server import TAPServer
