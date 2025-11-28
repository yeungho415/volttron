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

# To run these tests, create a helper toggle named volttrontest in your Home Assistant instance.
# This can be done by going to Settings > Devices & services > Helpers > Create Helper > Toggle
HOMEASSISTANT_TEST_IP = ""
ACCESS_TOKEN = ""
PORT = ""

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


@pytest.fixture(scope="module")
def config_store(volttron_instance, platform_driver):

    capabilities = [{"edit_config_store": {"identity": PLATFORM_DRIVER}}]
    volttron_instance.add_capabilities(volttron_instance.dynamic_agent.core.publickey, capabilities)

    registry_config = "homeassistant_test.json"
    registry_obj = [
        create_registry_config("input_boolean.volttrontest", "state", "bool_state", "On / Off", "off: 0, on: 1", True, 3, "int", "lights hallway"),
        create_registry_config("fan.volttrontest", "state", "fan_state", "On / Off", "off: 0, on: 1", True, 0, "int", "fan state control"),
        create_registry_config("fan.volttrontest", "percentage", "fan_percentage", "Percent", "0-100", True, 0, "int", "fan speed percentage"),
        create_registry_config("fan.volttrontest", "preset_mode", "fan_preset_mode", "Mode", "string preset mode", True, "auto", "string", "fan preset mode"),
        create_registry_config("fan.volttrontest", "direction", "fan_direction", "Direction", "forward or reverse", True, "forward", "string", "fan direction"),
        create_registry_config("fan.volttrontest", "oscillating", "fan_oscillating", "On / Off", "off: 0, on: 1", True, 0, "int", "fan oscillating control")
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
