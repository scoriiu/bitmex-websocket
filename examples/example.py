import asyncio
import logging
import signal

import alog

from bitmex_websocket import Instrument
from bitmex_websocket.constants import InstrumentChannels


class Ticker(Instrument):
    def __init__(self, symbol='XBTUSD', **kwargs):
        channels = [
            InstrumentChannels.trade,
        ]
        super().__init__(symbol=symbol, channels=channels, **kwargs)

    async def on_action(self, message):
        alog.info(alog.pformat(message['data']))

    async def on_open(self):
        alog.debug("WebSocket opened.")
        await self.subscribe_channels()

    async def subscribe_channels(self):
        for channel in self.channels:
            channel_key = f'{channel.name}:{self.symbol}'
            await self.subscribe(channel_key)

    async def run_forever(self):
        await super().start()


async def main():
    emitter = Ticker('XBTUSD')
    await emitter.run_forever()


def handle_signal(loop, signal):
    loop.stop()


if __name__ == '__main__':
    alog.set_level(logging.DEBUG)
    loop = asyncio.get_event_loop()

    # Handle SIGINT and SIGTERM to gracefully shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal, loop, sig)

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
