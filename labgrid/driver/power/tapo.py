""" Tested with TAPO P300, and should be compatible with any TAPO strip supported by kasa """

import asyncio
import os

from kasa import Credentials, Device, DeviceConfig, DeviceConnectionParameters, DeviceEncryptionType, DeviceFamily


def _get_credentials() -> Credentials:
    username = os.environ.get("KASA_USERNAME")
    password = os.environ.get("KASA_PASSWORD")
    if username is None or password is None:
        raise ValueError("Set KASA_USERNAME and KASA_PASSWORD environment variables")
    return Credentials(username=username, password=password)


def _get_connection_type() -> DeviceConnectionParameters:
    return DeviceConnectionParameters(
        device_family=DeviceFamily.SmartTapoPlug,
        encryption_type=DeviceEncryptionType.Klap,
        https=False,
        login_version=2,
    )


async def _power_set(host: str, port: str, index, value):
    """We embed the coroutines in an `async` function to minimise calls to `asyncio.run`"""
    assert port is None
    index = int(index)
    strip = await Device.connect(
        config=DeviceConfig(
            host=host, credentials=_get_credentials(), connection_type=_get_connection_type(), uses_http=True
        )
    )
    await strip.update()
    assert len(strip.children) > index, "Trying to access non-existant plug socket on strip"
    if value is True:
        await strip.children[index].turn_on()
    elif value is False:
        await strip.children[index].turn_off()
    await strip.disconnect()


def power_set(host: str, port: str, index, value):
    asyncio.run(_power_set(host, port, index, value))


async def _power_get(host: str, port: str, index) -> bool:
    assert port is None
    index = int(index)
    strip = await Device.connect(
        config=DeviceConfig(
            host=host, credentials=_get_credentials(), connection_type=_get_connection_type(), uses_http=True
        )
    )
    await strip.update()
    assert len(strip.children) > index, "Trying to access non-existant plug socket on strip"
    pwr_state = strip.children[index].is_on
    await strip.disconnect()
    return pwr_state


def power_get(host: str, port: str, index) -> bool:
    return asyncio.run(_power_get(host, port, index))
