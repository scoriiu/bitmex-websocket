#!/usr/bin/env python

import asyncio
import logging
import signal

import alog

from bitmex_websocket import Instrument
from bitmex_websocket.constants import InstrumentChannels


class Ticker(Instrument):
    def __init__(self, symbol='XBTUSD', **kwargs):
        channels = [
            InstrumentChannels.quote,
        ]
        super().__init__(symbol=symbol, channels=channels, **kwargs)

    async def on_action(self, message):
        pass
        # alog.info(alog.pformat(message['data']))

    async def run_forever(self):
        self.on('action', self.on_action)
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
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(
            loop.shutdown_asyncgens()))

    try:
        loop.run_until_complete(main())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
