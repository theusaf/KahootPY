import asyncio
import websocket
import ssl
from . import consts

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
