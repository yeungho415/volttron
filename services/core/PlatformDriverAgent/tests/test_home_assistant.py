# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2023 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}

import json
import logging
import pytest
import gevent

from volttron.platform.agent.known_identities import (
    PLATFORM_DRIVER,
    CONFIGURATION_STORE,
)
from volttron.platform import get_services_core
from volttron.platform.agent import utils
from volttron.platform.keystore import KeyStore
from volttrontesting.utils.platformwrapper import PlatformWrapper

utils.setup_logging()
logger = logging.getLogger(__name__)

# =============================================================================
# TEST CONFIGURATION
# =============================================================================
# To run these tests, you need:
# 1. A running Home Assistant instance
# 2. A Long-Lived Access Token (from your HA Profile page)
# 3. Test entities set up in Home Assistant:
#
#    REQUIRED ENTITIES:
#    - input_boolean.volttrontest : Settings > Helpers > Create Helper > Toggle
#    - fan.volttrontest           : Create via HACS virtual integration or use real fan
#    - switch.volttrontest        : Settings > Helpers > Create Helper > Toggle (or real switch)
#    - siren.volttrontest         : Requires HACS virtual siren or real device
#    - humidifier.volttrontest    : Requires HACS virtual humidifier or real device
#    - lawn_mower.volttrontest    : Requires HACS virtual lawn mower or real device
#
#    For virtual devices, install HACS and add the "Virtual" integration:
#    https://github.com/twrecked/hass-virtual
#
# 4. Set the configuration variables below:
HOMEASSISTANT_TEST_IP = ""  # e.g., "192.168.1.100"
ACCESS_TOKEN = ""           # Long-lived access token from HA Profile
PORT = ""                   # Usually "8123"

skip_msg = "Some configuration variables are not set. Check HOMEASSISTANT_TEST_IP, ACCESS_TOKEN, and PORT"

# Skip tests if variables are not set
pytestmark = pytest.mark.skipif(
    not (HOMEASSISTANT_TEST_IP and ACCESS_TOKEN and PORT),
    reason=skip_msg
)
HOMEASSISTANT_DEVICE_TOPIC = "devices/home_assistant"


def create_registry_config(entity_id, entity_point, point_name, units, units_details, writable, starting_value, type_name, notes):
    """Helper function to create registry configuration entries for any Home Assistant entity."""
    return {
        "Entity ID": entity_id,
        "Entity Point": entity_point,
        "Volttron Point Name": point_name,
        "Units": units,
        "Units Details": units_details,
        "Writable": writable,
        "Starting Value": starting_value,
        "Type": type_name,
        "Notes": notes
    }


# Get the point which will should be off
def test_get_point(volttron_instance, config_store):
    expected_values = 0
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'bool_state').get(timeout=20)
    assert result == expected_values, "The result does not match the expected result."


# The default value for this fake light is 3. If the test cannot reach out to home assistant,
# the value will default to 3 making the test fail.
def test_data_poll(volttron_instance: PlatformWrapper, config_store):
    expected_values = [{'bool_state': 0}, {'bool_state': 1}]
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all', 'home_assistant').get(timeout=20)
    assert result in expected_values, "The result does not match the expected result."


# Turn on the light. Light is automatically turned off every 30 seconds to allow test to turn
# it on and receive the correct value.
def test_set_point(volttron_instance, config_store):
    expected_values = {'bool_state': 1}
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'bool_state', 1)
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all', 'home_assistant').get(timeout=20)
    assert result == expected_values, "The result does not match the expected result."


# Test fan state control (on/off)
def test_fan_set_state(volttron_instance, config_store):
    agent = volttron_instance.dynamic_agent
    # Test turning fan on
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'fan_state', 1)
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'fan_state').get(timeout=20)
    assert result == 1, "Fan state should be 1 (on)"

    # Test turning fan off
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'fan_state', 0)
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'fan_state').get(timeout=20)
    assert result == 0, "Fan state should be 0 (off)"


# Test fan percentage control
def test_fan_set_percentage(volttron_instance, config_store):
    agent = volttron_instance.dynamic_agent
    # Test setting percentage to 50
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'fan_percentage', 50)
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'fan_percentage').get(timeout=20)
    assert result == 50, "Fan percentage should be 50"

    # Test setting percentage to 100
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'fan_percentage', 100)
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'fan_percentage').get(timeout=20)
    assert result == 100, "Fan percentage should be 100"


# Test fan preset mode control
def test_fan_set_preset_mode(volttron_instance, config_store):
    agent = volttron_instance.dynamic_agent
    # Test setting preset mode to 'eco'
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'fan_preset_mode', 'eco')
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'fan_preset_mode').get(timeout=20)
    assert result == 'eco', "Fan preset mode should be 'eco'"


# Test fan direction control
def test_fan_set_direction(volttron_instance, config_store):
    agent = volttron_instance.dynamic_agent
    # Test setting direction to 'reverse'
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'fan_direction', 'reverse')
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'fan_direction').get(timeout=20)
    assert result == 'reverse', "Fan direction should be 'reverse'"

    # Test setting direction back to 'forward'
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'fan_direction', 'forward')
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'fan_direction').get(timeout=20)
    assert result == 'forward', "Fan direction should be 'forward'"


# Test fan oscillating control
def test_fan_set_oscillating(volttron_instance, config_store):
    agent = volttron_instance.dynamic_agent
    # Test turning oscillating on
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'fan_oscillating', 1)
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'fan_oscillating').get(timeout=20)
    assert result == 1, "Fan oscillating should be 1 (on)"

    # Test turning oscillating off
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'fan_oscillating', 0)
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'fan_oscillating').get(timeout=20)
    assert result == 0, "Fan oscillating should be 0 (off)"


# ============================================================================
# SWITCH ENTITY TESTS
# ============================================================================

def test_switch_set_state_on(volttron_instance, config_store):
    """Test turning switch on."""
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'switch_state', 1)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'switch_state').get(timeout=20)
    assert result == 1, "Switch state should be 1 (on)"


def test_switch_set_state_off(volttron_instance, config_store):
    """Test turning switch off."""
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'switch_state', 0)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'switch_state').get(timeout=20)
    assert result == 0, "Switch state should be 0 (off)"


def test_switch_scrape_all(volttron_instance, config_store):
    """Test that switch state is included in scrape_all results."""
    agent = volttron_instance.dynamic_agent
    # First set a known state
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'switch_state', 1)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all', 'home_assistant').get(timeout=20)
    assert 'switch_state' in result, "switch_state should be in scrape_all results"
    assert result['switch_state'] == 1, "Switch state should be 1 in scrape_all"


# ============================================================================
# SIREN ENTITY TESTS
# ============================================================================

def test_siren_set_state_on(volttron_instance, config_store):
    """Test turning siren on."""
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'siren_state', 1)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'siren_state').get(timeout=20)
    assert result == 1, "Siren state should be 1 (on)"


def test_siren_set_state_off(volttron_instance, config_store):
    """Test turning siren off."""
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'siren_state', 0)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'siren_state').get(timeout=20)
    assert result == 0, "Siren state should be 0 (off)"


def test_siren_set_volume(volttron_instance, config_store):
    """Test setting siren volume level."""
    agent = volttron_instance.dynamic_agent
    # Set volume to 0.7 (70%)
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'siren_volume', 0.7)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'siren_volume').get(timeout=20)
    # Volume might be rounded, so check if it's close
    assert abs(result - 0.7) < 0.1, f"Siren volume should be approximately 0.7, got {result}"


def test_siren_set_tone(volttron_instance, config_store):
    """Test setting siren tone."""
    agent = volttron_instance.dynamic_agent
    # Note: Available tones depend on the specific siren device
    # This test assumes 'default' or 'alarm' tone is available
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'siren_tone', 'default')
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'siren_tone').get(timeout=20)
    assert result == 'default', f"Siren tone should be 'default', got {result}"


def test_siren_scrape_all(volttron_instance, config_store):
    """Test that siren state is included in scrape_all results."""
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all', 'home_assistant').get(timeout=20)
    assert 'siren_state' in result, "siren_state should be in scrape_all results"
    assert 'siren_volume' in result, "siren_volume should be in scrape_all results"


# ============================================================================
# HUMIDIFIER ENTITY TESTS
# ============================================================================

def test_humidifier_set_state_on(volttron_instance, config_store):
    """Test turning humidifier on."""
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'humidifier_state', 1)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'humidifier_state').get(timeout=20)
    assert result == 1, "Humidifier state should be 1 (on)"


def test_humidifier_set_state_off(volttron_instance, config_store):
    """Test turning humidifier off."""
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'humidifier_state', 0)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'humidifier_state').get(timeout=20)
    assert result == 0, "Humidifier state should be 0 (off)"


def test_humidifier_set_humidity(volttron_instance, config_store):
    """Test setting humidifier target humidity."""
    agent = volttron_instance.dynamic_agent
    # Set target humidity to 55%
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'humidifier_humidity', 55)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'humidifier_humidity').get(timeout=20)
    assert result == 55, f"Humidifier target humidity should be 55, got {result}"


def test_humidifier_set_humidity_range(volttron_instance, config_store):
    """Test setting humidifier humidity to different values within range."""
    agent = volttron_instance.dynamic_agent

    # Test low humidity
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'humidifier_humidity', 30)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'humidifier_humidity').get(timeout=20)
    assert result == 30, f"Humidifier humidity should be 30, got {result}"

    # Test high humidity
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'humidifier_humidity', 80)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'humidifier_humidity').get(timeout=20)
    assert result == 80, f"Humidifier humidity should be 80, got {result}"


def test_humidifier_set_mode(volttron_instance, config_store):
    """Test setting humidifier mode."""
    agent = volttron_instance.dynamic_agent
    # Note: Available modes depend on the specific humidifier device
    # Common modes: 'normal', 'eco', 'boost', 'sleep', 'auto'
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'humidifier_mode', 'normal')
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'humidifier_mode').get(timeout=20)
    assert result == 'normal', f"Humidifier mode should be 'normal', got {result}"


def test_humidifier_scrape_all(volttron_instance, config_store):
    """Test that humidifier points are included in scrape_all results."""
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all', 'home_assistant').get(timeout=20)
    assert 'humidifier_state' in result, "humidifier_state should be in scrape_all results"
    assert 'humidifier_humidity' in result, "humidifier_humidity should be in scrape_all results"
    assert 'humidifier_mode' in result, "humidifier_mode should be in scrape_all results"


def test_humidifier_read_current_humidity(volttron_instance, config_store):
    """Test reading current humidity (read-only attribute)."""
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'humidifier_current').get(timeout=20)
    # Current humidity should be a number between 0 and 100
    assert isinstance(result, (int, float)), f"Current humidity should be numeric, got {type(result)}"
    assert 0 <= result <= 100, f"Current humidity should be 0-100, got {result}"


# ============================================================================
# LAWN MOWER ENTITY TESTS
# ============================================================================

def test_lawn_mower_start_mowing(volttron_instance, config_store):
    """Test starting the lawn mower (state = 1)."""
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'mower_state', 1)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'mower_state').get(timeout=20)
    # State should be 1 (mowing) after start command
    assert result == 1, f"Lawn mower state should be 1 (mowing), got {result}"


def test_lawn_mower_pause(volttron_instance, config_store):
    """Test pausing the lawn mower (state = 2)."""
    agent = volttron_instance.dynamic_agent
    # First start mowing
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'mower_state', 1)
    gevent.sleep(5)
    # Then pause
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'mower_state', 2)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'mower_state').get(timeout=20)
    # State should be 2 (paused) after pause command
    assert result == 2, f"Lawn mower state should be 2 (paused), got {result}"


def test_lawn_mower_dock(volttron_instance, config_store):
    """Test docking the lawn mower (state = 0)."""
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'mower_state', 0)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'mower_state').get(timeout=20)
    # State should be 0 (docked) or 3 (returning) after dock command
    assert result in [0, 3], f"Lawn mower state should be 0 (docked) or 3 (returning), got {result}"


def test_lawn_mower_full_cycle(volttron_instance, config_store):
    """Test full lawn mower cycle: dock -> mow -> pause -> dock."""
    agent = volttron_instance.dynamic_agent

    # Start from docked state
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'mower_state', 0)
    gevent.sleep(5)

    # Start mowing
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'mower_state', 1)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'mower_state').get(timeout=20)
    assert result == 1, f"After start: state should be 1 (mowing), got {result}"

    # Pause
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'mower_state', 2)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'mower_state').get(timeout=20)
    assert result == 2, f"After pause: state should be 2 (paused), got {result}"

    # Return to dock
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'mower_state', 0)
    gevent.sleep(5)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'mower_state').get(timeout=20)
    assert result in [0, 3], f"After dock: state should be 0 (docked) or 3 (returning), got {result}"


def test_lawn_mower_scrape_all(volttron_instance, config_store):
    """Test that lawn mower points are included in scrape_all results."""
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all', 'home_assistant').get(timeout=20)
    assert 'mower_state' in result, "mower_state should be in scrape_all results"
    assert 'mower_battery' in result, "mower_battery should be in scrape_all results"


def test_lawn_mower_read_battery(volttron_instance, config_store):
    """Test reading lawn mower battery level (read-only attribute)."""
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'mower_battery').get(timeout=20)
    # Battery level should be a number between 0 and 100
    assert isinstance(result, (int, float)), f"Battery level should be numeric, got {type(result)}"
    assert 0 <= result <= 100, f"Battery level should be 0-100, got {result}"


# ============================================================================
# COMBINED SCRAPE ALL TEST
# ============================================================================

def test_scrape_all_includes_all_entities(volttron_instance, config_store):
    """Test that scrape_all includes points from all entity types."""
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all', 'home_assistant').get(timeout=20)

    # Check that all expected points are present
    expected_points = [
        'bool_state',           # input_boolean
        'fan_state',            # fan
        'switch_state',         # switch (new)
        'siren_state',          # siren (new)
        'humidifier_state',     # humidifier (new)
        'mower_state',          # lawn_mower (new)
    ]

    for point in expected_points:
        assert point in result, f"{point} should be in scrape_all results"

    logger.info("scrape_all result: %s", result)


@pytest.fixture(scope="module")
def config_store(volttron_instance, platform_driver):

    capabilities = [{"edit_config_store": {"identity": PLATFORM_DRIVER}}]
    volttron_instance.add_capabilities(volttron_instance.dynamic_agent.core.publickey, capabilities)

    registry_config = "homeassistant_test.json"
    registry_obj = [
        # Input Boolean (existing)
        create_registry_config("input_boolean.volttrontest", "state", "bool_state", "On / Off", "off: 0, on: 1", True, 3, "int", "lights hallway"),
        # Fan (new)
        create_registry_config("fan.volttrontest", "state", "fan_state", "On / Off", "off: 0, on: 1", True, 0, "int", "fan state control"),
        create_registry_config("fan.volttrontest", "percentage", "fan_percentage", "Percent", "0-100", True, 0, "int", "fan speed percentage"),
        create_registry_config("fan.volttrontest", "preset_mode", "fan_preset_mode", "Mode", "string preset mode", True, "auto", "string", "fan preset mode"),
        create_registry_config("fan.volttrontest", "direction", "fan_direction", "Direction", "forward or reverse", True, "forward", "string", "fan direction"),
        create_registry_config("fan.volttrontest", "oscillating", "fan_oscillating", "On / Off", "off: 0, on: 1", True, 0, "int", "fan oscillating control"),
        # Switch (new)
        create_registry_config("switch.volttrontest", "state", "switch_state", "On / Off", "off: 0, on: 1", True, 0, "int", "switch state control"),
        # Siren (new)
        create_registry_config("siren.volttrontest", "state", "siren_state", "On / Off", "off: 0, on: 1", True, 0, "int", "siren state control"),
        create_registry_config("siren.volttrontest", "volume_level", "siren_volume", "Volume", "0.0-1.0", True, 0.5, "float", "siren volume level"),
        create_registry_config("siren.volttrontest", "tone", "siren_tone", "Tone", "string tone name", True, "default", "string", "siren tone"),
        # Humidifier (new)
        create_registry_config("humidifier.volttrontest", "state", "humidifier_state", "On / Off", "off: 0, on: 1", True, 0, "int", "humidifier state control"),
        create_registry_config("humidifier.volttrontest", "humidity", "humidifier_humidity", "Percent", "0-100", True, 50, "int", "humidifier target humidity"),
        create_registry_config("humidifier.volttrontest", "mode", "humidifier_mode", "Mode", "string mode name", True, "normal", "string", "humidifier mode"),
        create_registry_config("humidifier.volttrontest", "current_humidity", "humidifier_current", "Percent", "0-100", False, 0, "int", "humidifier current humidity (read-only)"),
        # Lawn Mower (new)
        create_registry_config("lawn_mower.volttrontest", "state", "mower_state", "State", "0=docked, 1=mowing, 2=paused, 3=returning, 4=error", True, 0, "int", "lawn mower state control"),
        create_registry_config("lawn_mower.volttrontest", "battery_level", "mower_battery", "Percent", "0-100", False, 0, "int", "lawn mower battery level (read-only)"),
    ]

    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE,
                                                 "manage_store",
                                                 PLATFORM_DRIVER,
                                                 registry_config,
                                                 json.dumps(registry_obj),
                                                 config_type="json")
    gevent.sleep(2)
    # driver config
    driver_config = {
        "driver_config": {"ip_address": HOMEASSISTANT_TEST_IP, "access_token": ACCESS_TOKEN, "port": PORT},
        "driver_type": "home_assistant",
        "registry_config": f"config://{registry_config}",
        "timezone": "US/Pacific",
        "interval": 30,
    }

    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE,
                                                 "manage_store",
                                                 PLATFORM_DRIVER,
                                                 HOMEASSISTANT_DEVICE_TOPIC,
                                                 json.dumps(driver_config),
                                                 config_type="json"
                                                 )
    gevent.sleep(2)

    yield platform_driver

    print("Wiping out store.")
    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE, "manage_delete_store", PLATFORM_DRIVER)
    gevent.sleep(0.1)


@pytest.fixture(scope="module")
def platform_driver(volttron_instance):
    # Start the platform driver agent which would in turn start the bacnet driver
    platform_uuid = volttron_instance.install_agent(
        agent_dir=get_services_core("PlatformDriverAgent"),
        config_file={
            "publish_breadth_first_all": False,
            "publish_depth_first": False,
            "publish_breadth_first": False,
        },
        start=True,
    )
    gevent.sleep(2)  # wait for the agent to start and start the devices
    assert volttron_instance.is_agent_running(platform_uuid)
    yield platform_uuid

    volttron_instance.stop_agent(platform_uuid)
    if not volttron_instance.debug_mode:
        volttron_instance.remove_agent(platform_uuid)
