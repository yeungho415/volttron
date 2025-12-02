# -*- coding: utf-8 -*-
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


import random
from math import pi
import json
import sys
from platform_driver.interfaces import BaseInterface, BaseRegister, BasicRevert
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent
import logging
import requests
from requests import get

_log = logging.getLogger(__name__)


# ===================
# Types and Registers
# ===================

type_mapping = {
    "string": str,
    "int": int,
    "integer": int,
    "float": float,
    "bool": bool,
    "boolean": bool,
}


class HomeAssistantRegister(BaseRegister):
    def __init__(
        self,
        read_only,
        pointName,
        units,
        reg_type,
        attributes,
        entity_id,
        entity_point,
        default_value=None,
        description="",
    ):
        super(HomeAssistantRegister, self).__init__(
            "byte", read_only, pointName, units, description=""
        )
        self.reg_type = reg_type
        self.attributes = attributes
        self.entity_id = entity_id
        self.value = None
        self.entity_point = entity_point


# ================
# HTTP API Wrapper
# ================


class HomeAssistantAPI:
    """Thin wrapper for HA HTTP API."""

    def __init__(self, ip, port, token):
        self.base_url = f"http://{ip}:{port}/api"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def get_state(self, entity_id):
        url = f"{self.base_url}/states/{entity_id}"
        try:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
            raise Exception(f"GET {url} failed {resp.status_code} {resp.text}")
        except requests.RequestException as e:
            raise Exception(f"GET {url} error {e}") from e

    def service_call(self, device, action, payload, desc):
        url = f"{self.base_url}/services/{device}/{action}"
        try:
            resp = requests.post(url, headers=self.headers, json=payload)
            if resp.status_code == 200:
                _log.info("Success: %s", desc)
                return resp.json() if resp.content else None
            msg = f"Failed to {desc}. Status code {resp.status_code}. Response {resp.text}"
            _log.error(msg)
            raise Exception(msg)
        except requests.RequestException as e:
            msg = f"Error when attempting {desc}: {e}"
            _log.error(msg)
            raise Exception(msg) from e


# ===================
# Entity Abstractions
# ===================


class HomeAssistantEntity:
    def __init__(self, api, entity_id):
        self.api = api
        self.entity_id = entity_id

    # Common caller
    def call(self, device, action, **data):
        payload = {"entity_id": self.entity_id}
        payload.update(data)
        self.api.service_call(
            device, action, payload, f"{device}/{action} {self.entity_id}"
        )

    # Default implementations raise unless overridden
    def set_state(self, value):
        raise ValueError(f"State not supported for {self.entity_id}")


class LightEntity(HomeAssistantEntity):
    def set_state(self, value):
        if isinstance(value, int) and value in (0, 1):
            if value == 1:
                self.call("light", "turn_on")
            else:
                self.call("light", "turn_off")
        else:
            raise ValueError("Light state must be 0 or 1")

    def set_brightness(self, value):
        if isinstance(value, int) and 0 <= value <= 255:
            self.call("light", "turn_on", brightness=value)
        else:
            raise ValueError("Brightness must be an int 0..255")


class InputBooleanEntity(HomeAssistantEntity):
    def set_state(self, value):
        if isinstance(value, int) and value in (0, 1):
            action = "turn_on" if value == 1 else "turn_off"
            self.call("input_boolean", action)
        else:
            raise ValueError("Input boolean state must be 0 or 1")


class ClimateEntity(HomeAssistantEntity):
    MODE_MAP = {0: "off", 2: "heat", 3: "cool", 4: "auto"}

    def set_state(self, value):
        if isinstance(value, int) and value in self.MODE_MAP:
            self.call("climate", "set_hvac_mode", hvac_mode=self.MODE_MAP[value])
        else:
            raise ValueError("Climate state must be one of 0, 2, 3, 4")

    def set_temperature(self, value, units=None):
        if not isinstance(value, (int, float)):
            raise ValueError("Temperature must be numeric")
        temperature = value
        if units == "C":
            # Convert F to C
            temperature = round((value - 32) * 5 / 9, 1)
        self.call("climate", "set_temperature", temperature=temperature)


class FanEntity(HomeAssistantEntity):
    """
    Entity handler for Home Assistant fan domain.

    """
    def set_state(self, value):
        if isinstance(value, int) and value in (0, 1):
            if value == 1:
                self.call("fan", "turn_on")
            else:
                self.call("fan", "turn_off")
        else:
            raise ValueError("Fan state must be 0 or 1")

    def set_percentage(self, value):
        if isinstance(value, (int, float)) and 0 <= value <= 100:
            self.call("fan", "set_percentage", percentage=value)
        else:
            raise ValueError("Fan percentage must be 0..100")

    def set_preset_mode(self, value):
        if isinstance(value, str):
            self.call("fan", "set_preset_mode", preset_mode=value)
        else:
            raise ValueError("Fan preset_mode must be string")

    def set_direction(self, value):
        if isinstance(value, str) and value.lower() in ("forward", "reverse"):
            self.call("fan", "set_direction", direction=value.lower())
        else:
            raise ValueError("Fan direction must be 'forward' or 'reverse'")

    def set_oscillating(self, value):
        if isinstance(value, (bool, int)) and value in (0, 1, True, False):
            self.call("fan", "oscillate", oscillating=bool(value))
        else:
            raise ValueError("Fan oscillating must be bool or 0/1")


class SwitchEntity(HomeAssistantEntity):
    """
    Entity handler for Home Assistant switch domain.

    Switches are simple on/off devices like smart plugs, relays, etc.
    """

    def set_state(self, value):
        if isinstance(value, int) and value in (0, 1):
            if value == 1:
                self.call("switch", "turn_on")
            else:
                self.call("switch", "turn_off")
        else:
            raise ValueError("Switch state must be 0 or 1")


class SirenEntity(HomeAssistantEntity):
    """
    Entity handler for Home Assistant siren domain.

    Sirens are alarm/notification devices that can produce sound.
    """

    def set_state(self, value):
        if isinstance(value, int) and value in (0, 1):
            if value == 1:
                self.call("siren", "turn_on")
            else:
                self.call("siren", "turn_off")
        else:
            raise ValueError("Siren state must be 0 or 1")

    def set_volume_level(self, value):
        """Set siren volume level (0.0 to 1.0)."""
        if isinstance(value, (int, float)) and 0 <= value <= 1:
            self.call("siren", "turn_on", volume_level=float(value))
        else:
            raise ValueError("Siren volume_level must be 0.0..1.0")

    def set_tone(self, value):
        """Set siren tone (must be one of the available_tones for the device)."""
        if isinstance(value, str):
            self.call("siren", "turn_on", tone=value)
        else:
            raise ValueError("Siren tone must be a string")

    def set_duration(self, value):
        """Set siren duration in seconds."""
        if isinstance(value, (int, float)) and value > 0:
            self.call("siren", "turn_on", duration=int(value))
        else:
            raise ValueError("Siren duration must be a positive number (seconds)")


class HumidifierEntity(HomeAssistantEntity):
    """
    Entity handler for Home Assistant humidifier domain.

    Humidifiers control humidity levels in a space.
    """

    def set_state(self, value):
        if isinstance(value, int) and value in (0, 1):
            if value == 1:
                self.call("humidifier", "turn_on")
            else:
                self.call("humidifier", "turn_off")
        else:
            raise ValueError("Humidifier state must be 0 or 1")

    def set_humidity(self, value):
        """Set target humidity level (typically 0-100%)."""
        if isinstance(value, (int, float)) and 0 <= value <= 100:
            self.call("humidifier", "set_humidity", humidity=int(value))
        else:
            raise ValueError("Humidifier humidity must be 0..100")

    def set_mode(self, value):
        """Set humidifier mode (must be one of the available_modes for the device)."""
        if isinstance(value, str):
            self.call("humidifier", "set_mode", mode=value)
        else:
            raise ValueError("Humidifier mode must be a string")


class LawnMowerEntity(HomeAssistantEntity):
    """
    Entity handler for Home Assistant lawn_mower domain.

    Lawn mowers are robotic mowing devices.
    State mapping: 0=docked, 1=mowing, 2=paused, 3=returning, 4=error
    """

    STATE_MAP = {0: "docked", 1: "mowing", 2: "paused", 3: "returning", 4: "error"}
    STATE_MAP_REV = {v: k for k, v in STATE_MAP.items()}

    def set_state(self, value):
        """Set lawn mower state: 0=dock, 1=start_mowing, 2=pause."""
        if isinstance(value, int):
            if value == 0:
                self.call("lawn_mower", "dock")
            elif value == 1:
                self.call("lawn_mower", "start_mowing")
            elif value == 2:
                self.call("lawn_mower", "pause")
            else:
                raise ValueError(
                    "Lawn mower state must be 0 (dock), 1 (start_mowing), or 2 (pause)"
                )
        else:
            raise ValueError("Lawn mower state must be an integer")


# ========================
# Entity Factory
# ========================

class EntityFactory:
    """Factory that creates entity handlers based on HA domain."""

    def __init__(self, api):
        self.api = api
        self._registry = {
            "light": LightEntity,
            "fan": FanEntity,
            "climate": ClimateEntity,
            "input_boolean": InputBooleanEntity,
            "switch": SwitchEntity,
            "siren": SirenEntity,
            "humidifier": HumidifierEntity,
            "lawn_mower": LawnMowerEntity,
        }

    def register(self, domain, entity_cls):
        """Allow overriding or adding new domain handlers."""
        self._registry[domain] = entity_cls

    def create(self, entity_id):
        if not self.api:
            raise Exception("API not initialized")
        domain = entity_id.split(".", 1)[0]
        entity_cls = self._registry.get(domain, HomeAssistantEntity)
        return entity_cls(self.api, entity_id)


# =======================
# Main VOLTTRON Interface
# =======================


class Interface(BasicRevert, BaseInterface):
    def __init__(self, **kwargs):
        super(Interface, self).__init__(**kwargs)
        self.point_name = None
        self.ip_address = None
        self.access_token = None
        self.port = None
        self.units = None
        self.api = None
        self.entity_factory = None

    def configure(self, config_dict, registry_config_str):
        self.ip_address = config_dict.get("ip_address")
        self.access_token = config_dict.get("access_token")
        self.port = config_dict.get("port")

        if not self.ip_address:
            _log.error("IP address is not set.")
            raise ValueError("IP address is required.")
        if not self.access_token:
            _log.error("Access token is not set.")
            raise ValueError("Access token is required.")
        if self.port is None:
            _log.error("Port is not set.")
            raise ValueError("Port is required.")

        self.api = HomeAssistantAPI(self.ip_address, int(self.port), self.access_token)
        self.entity_factory = EntityFactory(self.api)
        self.parse_config(registry_config_str)

    def get_entity_data(self, entity_id):
        if not self.api:
            raise Exception("API not initialized")
        return self.api.get_state(entity_id)

    # points API

    def get_point(self, point_name):
        register = self.get_register_by_name(point_name)
        entity_data = self.get_entity_data(register.entity_id)
        if register.point_name == "state":
            return entity_data.get("state")
        return entity_data.get("attributes", {}).get(register.point_name, 0)

    def _set_point(self, point_name, value):
        register = self.get_register_by_name(point_name)
        if register.read_only:
            raise IOError(
                "Trying to write to a point configured read only: " + point_name
            )

        # cast value to register type
        try:
            cast_value = register.reg_type(value)
        except Exception as e:
            raise ValueError(f"Cannot cast {value!r} to {register.reg_type}") from e

        handler = self.entity_factory.create(register.entity_id)
        entity_point = register.entity_point

        if entity_point == "state":
            handler.set_state(cast_value)
        else:
            method_name = f"set_{entity_point}"
            if isinstance(handler, ClimateEntity) and entity_point == "temperature":
                # pass units context
                getattr(handler, method_name)(cast_value, units=self.units)
            elif hasattr(handler, method_name):
                getattr(handler, method_name)(cast_value)
            else:
                raise ValueError(
                    f"Unexpected point_name {point_name} for entity {register.entity_id}"
                )

        register.value = cast_value
        return register.value

    def _scrape_all(self):
        """Read all points and normalize states to numbers where needed."""
        result = {}
        read_registers = self.get_registers_by_type("byte", True)
        write_registers = self.get_registers_by_type("byte", False)

        for register in read_registers + write_registers:
            entity_id = register.entity_id
            entity_point = register.entity_point
            domain = entity_id.split(".", 1)[0]

            try:
                entity_data = self.get_entity_data(entity_id)
                state = entity_data.get("state")
                attrs = entity_data.get("attributes", {})

                if domain == "climate":
                    if entity_point == "state":
                        map_rev = {"off": 0, "heat": 2, "cool": 3, "auto": 4}
                        if state in map_rev:
                            numeric = map_rev[state]
                            register.value = numeric
                            result[register.point_name] = numeric
                        else:
                            _log.error(
                                "State %s from %s is not yet supported",
                                state,
                                entity_id,
                            )
                    else:
                        attribute = attrs.get(entity_point, 0)
                        register.value = attribute
                        result[register.point_name] = attribute

                elif domain in ("fan", "light", "input_boolean", "switch", "siren", "humidifier"):
                    if entity_point == "state":
                        numeric = 1 if state == "on" else 0
                        register.value = numeric
                        result[register.point_name] = numeric
                    else:
                        attribute = attrs.get(entity_point, 0)
                        register.value = attribute
                        result[register.point_name] = attribute

                elif domain == "lawn_mower":
                    if entity_point == "state":
                        map_rev = {
                            "docked": 0,
                            "mowing": 1,
                            "paused": 2,
                            "returning": 3,
                            "error": 4,
                        }
                        if state in map_rev:
                            numeric = map_rev[state]
                            register.value = numeric
                            result[register.point_name] = numeric
                        else:
                            _log.error(
                                "State %s from %s is not yet supported",
                                state,
                                entity_id,
                            )
                    else:
                        attribute = attrs.get(entity_point, 0)
                        register.value = attribute
                        result[register.point_name] = attribute

                else:
                    if entity_point == "state":
                        register.value = state
                        result[register.point_name] = state
                    else:
                        attribute = attrs.get(entity_point, 0)
                        register.value = attribute
                        result[register.point_name] = attribute

            except Exception as e:
                _log.error("Unexpected error for entity_id %s: %s", entity_id, e)

        return result

    def parse_config(self, config_dict):
        if config_dict is None:
            return
        for regDef in config_dict:
            if not regDef.get("Entity ID"):
                continue

            read_only = str(regDef.get("Writable", "")).lower() != "true"
            entity_id = regDef["Entity ID"]
            entity_point = regDef["Entity Point"]
            self.point_name = regDef["Volttron Point Name"]
            self.units = regDef.get("Units")
            description = regDef.get("Notes", "")
            default_value = "Starting Value"
            type_name = regDef.get("Type", "string")
            reg_type = type_mapping.get(type_name, str)
            attributes = regDef.get("Attributes", {})

            register = HomeAssistantRegister(
                read_only,
                self.point_name,
                self.units,
                reg_type,
                attributes,
                entity_id,
                entity_point,
                default_value=default_value,
                description=description,
            )

            if default_value is not None:
                self.set_default(self.point_name, register.value)

            self.insert_register(register)
