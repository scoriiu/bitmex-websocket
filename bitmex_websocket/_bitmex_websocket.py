import asyncio
import json
import logging
import ssl
from urllib.parse import urlparse

import alog
import websockets

from bitmex_websocket.auth.api_key_auth import generate_nonce, \
    generate_signature
from bitmex_websocket.settings import settings

__all__ = ['BitMEXWebsocket']


class BitMEXWebsocketConnectionError(Exception):
    pass


class BitMEXWebsocket:
    def __init__(self, should_auth=False, heartbeat=True, ping_interval=10,
                 ping_timeout=9, **kwargs):
        self.ping_timeout = ping_timeout
        self.ping_interval = ping_interval
        self.should_auth = should_auth
        self.heartbeat = heartbeat
        self.channels = []
        self.reconnect_count = 0
        self.url = self.gen_url()
        self.ws = None

    def gen_url(self):
        base_url = settings.BASE_URL
        url_parts = list(urlparse(base_url))
        query_string = '?heartbeat=true' if self.heartbeat else ''
        return f"wss://{url_parts[1]}/realtime{query_string}"

    async def connect(self):
        async with websockets.connect(self.url,
                                      ssl=ssl.SSLContext()) as websocket:
            self.ws = websocket
            await self.on_open()

            try:
                async for message in websocket:
                    await self.on_message(message)
            except websockets.ConnectionClosed as e:
                await self.on_close()
                raise BitMEXWebsocketConnectionError(
                    f"WebSocket connection closed: {e}")

    async def start(self):
        while True:
            try:
                await self.connect()
            except BitMEXWebsocketConnectionError as e:
                alog.error(f"Connection error: {e}")
                await asyncio.sleep(5)  # Reconnect after 5 seconds

    async def on_open(self):
        alog.debug("WebSocket opened.")
        await self.subscribe_channels()

    async def on_close(self):
        alog.info("WebSocket closed")

    async def on_error(self, error):
        alog.error(f"WebSocket error: {error}")
        raise BitMEXWebsocketConnectionError(error)

    async def on_message(self, message):
        """Handler for parsing WS messages."""
        message = json.loads(message)

        if 'error' in message:
            await self.on_error(message['error'])

        action = message.get('action')

        if action:
            await self.on_action(message)
        elif 'subscribe' in message:
            await self.on_subscribe(message)
        elif 'status' in message:
            await self.on_status(message)

    async def on_pong(self, message):
        timestamp = float(time.time() * 1000)
        latency = timestamp - (self.last_ping_tm * 1000)

    async def subscribe(self, channel: str):
        subscription_msg = {"op": "subscribe", "args": [channel]}
        await self._send_message(subscription_msg)

    async def _send_message(self, message):
        await self.ws.send(json.dumps(message))

    def is_connected(self):
        return self.ws is not None and self.ws.open

    async def header(self):
        """Return auth headers. Will use API Keys if present in settings."""
        auth_header = []
        alog.info(f'### should auth {self.should_auth} ###')

        if self.should_auth:
            alog.info("Authenticating with API Key.")
            alog.info((settings.BITMEX_API_KEY, settings.BITMEX_API_SECRET))

            nonce = generate_nonce()
            api_signature = generate_signature(
                settings.BITMEX_API_SECRET, 'GET', '/realtime', nonce, '')

            auth_header = [
                "api-nonce: " + str(nonce),
                "api-signature: " + api_signature,
                "api-key:" + settings.BITMEX_API_KEY
            ]

            alog.info(alog.pformat(auth_header))

        return auth_header

    async def on_subscribe(self, message):
        if message['success']:
            alog.debug("Subscribed to %s." % message['subscribe'])
        else:
            raise Exception('Unable to subscribe.')

    async def on_action(self, message):
        # Handle action message
        pass

    async def on_status(self, message):
        # Handle status message
        pass

    async def subscribe_channels(self):
        # Placeholder for subscribe_channels logic
        pass


async def main():
    ticker = BitMEXWebsocket()
    await ticker.start()


if __name__ == '__main__':
    alog.set_level(logging.DEBUG)
    asyncio.run(main())
