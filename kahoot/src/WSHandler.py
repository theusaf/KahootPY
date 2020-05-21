import asyncio
import websockets
import ssl
from . import consts

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
