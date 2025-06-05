"""What kind of application do you want running on your host?"""

#ruff: noqa F401

# whitelisted module exporting, I prefer this over glob-reexport
from host.application.simple_server import SimpleServer
