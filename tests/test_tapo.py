import os
from unittest.mock import AsyncMock, patch

import pytest

from labgrid.driver.power.tapo import _get_credentials, _power_get, _power_set, power_get


# Mock device configuration
@pytest.fixture
def mock_device():
    device = AsyncMock()
    device.children = [
        AsyncMock(is_on=True),
        AsyncMock(is_on=False),
        AsyncMock(is_on=True)
    ]
    return device


@pytest.fixture
def mock_env():
    os.environ['KASA_USERNAME'] = 'test_user'
    os.environ['KASA_PASSWORD'] = 'test_pass'
    yield
    del os.environ['KASA_USERNAME']
    del os.environ['KASA_PASSWORD']


class TestTapoPowerDriver:
    def test_credentials_missing(self):
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
    async def test_power_get(self, mock_device, mock_env):
        """Test power state retrieval"""
        with patch('kasa.Device.connect', return_value=mock_device):
            # Test first outlet (on)
            result = await _power_get('192.168.1.100', None, 0)  # Use _power_get directly
            assert result is True

            # Test second outlet (off)
            result = await _power_get('192.168.1.100', None, 1)  # Use _power_get directly
            assert result is False

    @pytest.mark.asyncio
    async def test_power_set(self, mock_device, mock_env):
        """Test power state setting"""
        with patch('kasa.Device.connect', return_value=mock_device):
            # Test turning outlet on
            await _power_set('192.168.1.100', None, 0, True)
            mock_device.children[0].turn_on.assert_called_once()

            # Test turning outlet off
            await _power_set('192.168.1.100', None, 1, False)
            mock_device.children[1].turn_off.assert_called_once()

    def test_invalid_index(self, mock_device, mock_env):
        """Test accessing invalid outlet index"""
        with patch('kasa.Device.connect', return_value=mock_device):
            with pytest.raises(AssertionError, match="Trying to access non-existant plug socket"):
                power_get('192.168.1.100', None, 5)

    def test_invalid_port(self, mock_device):
        """Test that non-None port raises AssertionError"""
        with patch('kasa.Device.connect', return_value=mock_device):
            with pytest.raises(AssertionError):
                power_get('192.168.1.100', '8080', 0)
