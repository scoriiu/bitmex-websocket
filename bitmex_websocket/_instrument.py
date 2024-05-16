import asyncio
import logging

from bitmex_websocket._bitmex_websocket import BitMEXWebsocket
from bitmex_websocket.constants import Channels, SecureChannels, \
    SecureInstrumentChannels, InstrumentChannels
import alog
import click

__all__ = ['Instrument']


class SubscribeToAtLeastOneChannelException(Exception):
    pass


class SubscribeToSecureChannelException(Exception):
    pass


class Instrument(BitMEXWebsocket):
    def __init__(self, symbol: str = 'XBTUSD',
                 channels: [Channels] or [str] = None, should_auth=False,
                 **kwargs):
        super().__init__(should_auth=should_auth, **kwargs)

        if channels is None:
            raise SubscribeToAtLeastOneChannelException()

        self.channels = channels

        if should_auth is False and self._channels_contains_secure():
            raise SubscribeToSecureChannelException()

        self.symbol = symbol

    async def run_forever(self):
        await super().start()

    async def subscribe_channels(self):
        for channel in self.channels:
            channel_key = f'{channel.name}:{self.symbol}'
            await self.subscribe(channel_key)

    async def on_action(self, message):
        alog.debug(alog.pformat(message))

    def _channels_contains_secure(self):
        secure_channels = list(SecureChannels) + list(SecureInstrumentChannels)
        return not set(secure_channels).isdisjoint(self.channels)


@click.command()
@click.argument('symbol', type=str, default='XBTUSD')
def main(symbol: str, **kwargs):
    alog.set_level(logging.DEBUG)

    channels = [
        InstrumentChannels.trade,
        InstrumentChannels.orderBookL2
    ]
    instrument = Instrument(
        symbol=symbol,
        channels=channels,
        **kwargs
    )

    asyncio.run(instrument.run_forever())


if __name__ == '__main__':
    main()
