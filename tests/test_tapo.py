import os
from unittest.mock import AsyncMock, patch

import pytest

from labgrid.driver.power.tapo import _get_credentials, _power_get, _power_set, power_get


# Mock device configuration
@pytest.fixture
def mock_device_strip():
    device = AsyncMock()
    device.children = [
        AsyncMock(is_on=True),
        AsyncMock(is_on=False),
        AsyncMock(is_on=True)
    ]
    return device


@pytest.fixture
def mock_device_single_plug():
    device = AsyncMock()
    device.children = []
    return device


@pytest.fixture
def mock_env():
    os.environ['KASA_USERNAME'] = 'test_user'
    os.environ['KASA_PASSWORD'] = 'test_pass'
    yield
    del os.environ['KASA_USERNAME']
    del os.environ['KASA_PASSWORD']


class TestTapoPowerDriver:
    def test_should_raise_value_error_when_credentials_missing(self):
        """Test that missing credentials raise ValueError"""
        # Save existing environment variables
        saved_username = os.environ.pop('KASA_USERNAME', None)
        saved_password = os.environ.pop('KASA_PASSWORD', None)

        try:
            with pytest.raises(ValueError, match="Set KASA_USERNAME and KASA_PASSWORD"):
                _get_credentials()
        finally:
            # Restore environment variables if they existed
            if saved_username is not None:
                os.environ['KASA_USERNAME'] = saved_username
            if saved_password is not None:
                os.environ['KASA_PASSWORD'] = saved_password

    def test_credentials_valid(self, mock_env):
        """Test that valid credentials are returned"""
        creds = _get_credentials()
        assert creds.username == 'test_user'
        assert creds.password == 'test_pass'

    @pytest.mark.asyncio
    async def test_power_get_single_plug(self, mock_device_single_plug, mock_env):
        """Test power state retrieval for single plug device"""
        mock_device_single_plug.is_on = True  # Set the power state for single plug

        with patch('kasa.Device.connect', return_value=mock_device_single_plug):
            # Test single plug state (on)
            result = await _power_get('192.168.1.100', None, "0")
            assert result is True

            # Test after changing state to off
            mock_device_single_plug.is_on = False
            result = await _power_get('192.168.1.100', None, "0")
            assert result is False

    @pytest.mark.asyncio
    async def test_power_get_single_plug_should_not_care_for_index(self, mock_device_single_plug, mock_env):
        """Test that index is ignored for single plug device"""
        invalid_index = "7"
        mock_device_single_plug.is_on = True  # Set the power state for single plug

        with patch('kasa.Device.connect', return_value=mock_device_single_plug):
            # Test single plug state (on)
            result = await _power_get('192.168.1.100', None, invalid_index)
            assert result is True

    @pytest.mark.asyncio
    async def test_power_set_single_plug_turn_on(self, mock_device_single_plug, mock_env):
        """Test turning on single plug device"""
        with patch('kasa.Device.connect', return_value=mock_device_single_plug):
            # Test turning single plug on
            await _power_set('192.168.1.100', None, "0", True)
            mock_device_single_plug.turn_on.assert_called_once()

    @pytest.mark.asyncio
    async def test_power_set_single_plug_turn_off(self, mock_device_single_plug, mock_env):
        """Test turning off single plug device"""
        with patch('kasa.Device.connect', return_value=mock_device_single_plug):
            # Test turning single plug off
            await _power_set('192.168.1.100', None, "0", False)
            mock_device_single_plug.turn_off.assert_called_once()

    @pytest.mark.asyncio
    async def test_power_get_strip_valid_socket(self, mock_device_strip, mock_env):
        """Test power state retrieval"""
        with patch('kasa.Device.connect', return_value=mock_device_strip):
            # Test first outlet (on)
            result = await _power_get('192.168.1.100', None, "0")
            assert result is True

            # Test second outlet (off)
            result = await _power_get('192.168.1.100', None, "1")
            assert result is False

            # Test third outlet (on)
            result = await _power_get('192.168.1.100', None, "2")
            assert result is True

    @pytest.mark.asyncio
    async def test_power_set_strip_valid_socket(self, mock_device_strip, mock_env):
        """Test power state setting"""
        with patch('kasa.Device.connect', return_value=mock_device_strip):
            # Test turning outlet on
            await _power_set('192.168.1.100', None, "0", True)
            mock_device_strip.children[0].turn_on.assert_called_once()

            # Test turning outlet off
            await _power_set('192.168.1.100', None, "1", False)
            mock_device_strip.children[1].turn_off.assert_called_once()

    def test_should_raise_assertion_error_when_invalid_index_strip(self, mock_device_strip, mock_env):
        """Test accessing invalid outlet index"""
        invalid_socket = "5"
        with patch('kasa.Device.connect', return_value=mock_device_strip):
            with pytest.raises(AssertionError, match="Trying to access non-existant plug socket"):
                power_get('192.168.1.100', None, invalid_socket)

    def test_invalid_port_strip(self, mock_device_strip):
        """Test that non-None port raises AssertionError"""
        with patch('kasa.Device.connect', return_value=mock_device_strip):
            with pytest.raises(AssertionError):
                power_get('192.168.1.100', '8080', "0")

    def test_invalid_port_single_socket(self, mock_device_single_plug):
        """Test that non-None port raises AssertionError"""
        with patch('kasa.Device.connect', return_value=mock_device_single_plug):
            with pytest.raises(AssertionError):
                power_get('192.168.1.100', '8080', "0")
