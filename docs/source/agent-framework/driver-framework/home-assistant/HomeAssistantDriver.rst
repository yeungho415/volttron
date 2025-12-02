.. _HomeAssistant-Driver:

Home Assistant Driver
=====================

The Home Assistant driver enables VOLTTRON to read any data point from any Home Assistant controlled device.
Write access (control) is supported for the following device types:

- **Lights** - state (on/off) and brightness
- **Climate/Thermostats** - state (HVAC mode) and temperature
- **Fans** - state, percentage, preset_mode, direction, and oscillating
- **Switches** - state (on/off)
- **Sirens** - state, volume_level, tone, and duration
- **Humidifiers** - state, humidity, and mode
- **Lawn Mowers** - state (dock/mow/pause)

The following diagram shows interaction between platform driver agent and home assistant driver.

.. mermaid::

   sequenceDiagram
       HomeAssistant Driver->>HomeAssistant: Retrieve Entity Data (REST API)
       HomeAssistant-->>HomeAssistant Driver: Entity Data (Status Code: 200)
       HomeAssistant Driver->>PlatformDriverAgent: Publish Entity Data
       PlatformDriverAgent->>Controller Agent: Publish Entity Data

       Controller Agent->>HomeAssistant Driver: Instruct to Turn Off Light
       HomeAssistant Driver->>HomeAssistant: Send Turn Off Light Command (REST API)
       HomeAssistant-->>HomeAssistant Driver: Command Acknowledgement (Status Code: 200)

Pre-requisites
--------------
Before proceeding, find your Home Assistant IP address and long-lived access token from `here <https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token>`_.

Clone the repository, start volttron, install the listener agent, and the platform driver agent.

- `Listener agent <https://volttron.readthedocs.io/en/main/introduction/platform-install.html#installing-and-running-agents>`_
- `Platform driver agent <https://volttron.readthedocs.io/en/main/agent-framework/core-service-agents/platform-driver/platform-driver-agent.html?highlight=platform%20driver%20isntall#configuring-the-platform-driver>`_

Configuration
--------------

After cloning, generate configuration files. Each device requires one device configuration file and one registry file.
Ensure your registry_config parameter in your device configuration file, links to correct registry config name in the
config store. For more details on how volttron platform driver agent works with volttron configuration store see,
`Platform driver configuration <https://volttron.readthedocs.io/en/main/agent-framework/driver-framework/platform-driver/platform-driver.html#configuration-and-installation>`_
Examples for various device types are provided below.

Device configuration
++++++++++++++++++++

Device configuration file contains the connection details to you home assistant instance and driver_type as "home_assistant"

.. code-block:: json

   {
       "driver_config": {
           "ip_address": "Your Home Assistant IP",
           "access_token": "Your Home Assistant Access Token",
           "port": "Your Port"
       },
       "driver_type": "home_assistant",
       "registry_config": "config://light.example.json",
       "interval": 30,
       "timezone": "UTC"
   }

Registry Configuration
+++++++++++++++++++++++

Registry file can contain one single device and its attributes or a logical group of devices and its
attributes. Each entry should include the full entity id of the device, including but not limited to home assistant provided prefix
such as "light.", "climate." etc. The driver uses these prefixes to convert states into integers.

Each entry in a registry file should also have a 'Entity Point' and a unique value for 'Volttron Point Name'. The 'Entity ID' maps to the device instance, the 'Entity Point' extracts the attribute or state, and 'Volttron Point Name' determines the name of that point as it appears in VOLTTRON.

Attributes can be located in the developer tools in the Home Assistant GUI.

.. image:: home-assistant.png

Supported Entity Types
**********************

The following table summarizes all supported entity types and their writable points:

.. list-table:: Supported Entities and Writable Points
   :header-rows: 1
   :widths: 20 30 50

   * - Entity Type
     - Entity Prefix
     - Writable Points
   * - Light
     - ``light.``
     - state (0/1), brightness (0-255)
   * - Climate/Thermostat
     - ``climate.``
     - state (0=off, 2=heat, 3=cool, 4=auto), temperature
   * - Fan
     - ``fan.``
     - state (0/1), percentage (0-100), preset_mode, direction (forward/reverse), oscillating (0/1)
   * - Switch
     - ``switch.``
     - state (0/1)
   * - Siren
     - ``siren.``
     - state (0/1), volume_level (0.0-1.0), tone (string), duration (seconds)
   * - Humidifier
     - ``humidifier.``
     - state (0/1), humidity (0-100), mode (string)
   * - Lawn Mower
     - ``lawn_mower.``
     - state (0=docked, 1=mowing, 2=paused; read: 3=returning, 4=error)
   * - Input Boolean
     - ``input_boolean.``
     - state (0/1)

Example Light Registry
**********************

Below is an example file named light.example.json which has attributes of a single light instance with entity
id 'light.example':


.. code-block:: json

   [
       {
           "Entity ID": "light.example",
           "Entity Point": "state",
           "Volttron Point Name": "light_state",
           "Units": "On / Off",
           "Units Details": "on/off",
           "Writable": true,
           "Starting Value": true,
           "Type": "int",
           "Notes": "lights hallway"
       },
       {
           "Entity ID": "light.example",
           "Entity Point": "brightness",
           "Volttron Point Name": "light_brightness",
           "Units": "int",
           "Units Details": "light level",
           "Writable": true,
           "Starting Value": 0,
           "Type": "int",
           "Notes": "brightness control, 0 - 255"
       }
   ]


.. note::

   When using a single registry file to represent a logical group of multiple physical entities, make sure the
   "Volttron Point Name" is unique within a single registry file.

   For example, if a registry file contains entities with
   id  'light.instance1' and 'light.instance2' the entry for the attribute brightness for these two light instances could
   have "Volttron Point Name" as 'light1/brightness' and 'light2/brightness' respectively. This would ensure that data
   is posted to unique topic names and brightness data from light1 is not overwritten by light2 or vice-versa.

Example Thermostat Registry
***************************

For thermostats, the state is converted into numbers as follows: "0: Off, 2: heat, 3: Cool, 4: Auto",

.. code-block:: json

   [
       {
           "Entity ID": "climate.my_thermostat",
           "Entity Point": "state",
           "Volttron Point Name": "thermostat_state",
           "Units": "Enumeration",
           "Units Details": "0: Off, 2: heat, 3: Cool, 4: Auto",
           "Writable": true,
           "Starting Value": 1,
           "Type": "int",
           "Notes": "Mode of the thermostat"
       },
       {
           "Entity ID": "climate.my_thermostat",
           "Entity Point": "current_temperature",
           "Volttron Point Name": "volttron_current_temperature",
           "Units": "F",
           "Units Details": "Current Ambient Temperature",
           "Writable": false,
           "Starting Value": 72,
           "Type": "float",
           "Notes": "Current temperature reading (read-only)"
       },
       {
           "Entity ID": "climate.my_thermostat",
           "Entity Point": "temperature",
           "Volttron Point Name": "set_temperature",
           "Units": "F",
           "Units Details": "Desired Temperature",
           "Writable": true,
           "Starting Value": 75,
           "Type": "float",
           "Notes": "Target Temp"
       }
   ]

Example Fan Registry
********************

Fans support state, speed percentage, preset modes, direction, and oscillation control.

.. code-block:: json

   [
       {
           "Entity ID": "fan.living_room",
           "Entity Point": "state",
           "Volttron Point Name": "fan_state",
           "Units": "On / Off",
           "Units Details": "off: 0, on: 1",
           "Writable": true,
           "Starting Value": 0,
           "Type": "int",
           "Notes": "Fan on/off control"
       },
       {
           "Entity ID": "fan.living_room",
           "Entity Point": "percentage",
           "Volttron Point Name": "fan_percentage",
           "Units": "Percent",
           "Units Details": "0-100",
           "Writable": true,
           "Starting Value": 0,
           "Type": "int",
           "Notes": "Fan speed percentage"
       },
       {
           "Entity ID": "fan.living_room",
           "Entity Point": "preset_mode",
           "Volttron Point Name": "fan_preset_mode",
           "Units": "Mode",
           "Units Details": "Device-specific modes (e.g., eco, auto, turbo)",
           "Writable": true,
           "Starting Value": "auto",
           "Type": "string",
           "Notes": "Fan preset mode"
       },
       {
           "Entity ID": "fan.living_room",
           "Entity Point": "direction",
           "Volttron Point Name": "fan_direction",
           "Units": "Direction",
           "Units Details": "forward or reverse",
           "Writable": true,
           "Starting Value": "forward",
           "Type": "string",
           "Notes": "Fan rotation direction"
       },
       {
           "Entity ID": "fan.living_room",
           "Entity Point": "oscillating",
           "Volttron Point Name": "fan_oscillating",
           "Units": "On / Off",
           "Units Details": "off: 0, on: 1",
           "Writable": true,
           "Starting Value": 0,
           "Type": "int",
           "Notes": "Fan oscillation control"
       }
   ]

Example Switch Registry
***********************

Switches are simple on/off devices like smart plugs, relays, etc.

.. code-block:: json

   [
       {
           "Entity ID": "switch.smart_plug",
           "Entity Point": "state",
           "Volttron Point Name": "switch_state",
           "Units": "On / Off",
           "Units Details": "off: 0, on: 1",
           "Writable": true,
           "Starting Value": 0,
           "Type": "int",
           "Notes": "Smart plug on/off control"
       }
   ]

Example Siren Registry
**********************

Sirens are alarm/notification devices that can produce sound with configurable volume, tone, and duration.

.. code-block:: json

   [
       {
           "Entity ID": "siren.alarm",
           "Entity Point": "state",
           "Volttron Point Name": "siren_state",
           "Units": "On / Off",
           "Units Details": "off: 0, on: 1",
           "Writable": true,
           "Starting Value": 0,
           "Type": "int",
           "Notes": "Siren on/off control"
       },
       {
           "Entity ID": "siren.alarm",
           "Entity Point": "volume_level",
           "Volttron Point Name": "siren_volume",
           "Units": "Volume",
           "Units Details": "0.0 to 1.0",
           "Writable": true,
           "Starting Value": 0.5,
           "Type": "float",
           "Notes": "Siren volume level"
       },
       {
           "Entity ID": "siren.alarm",
           "Entity Point": "tone",
           "Volttron Point Name": "siren_tone",
           "Units": "Tone",
           "Units Details": "Device-specific tone names",
           "Writable": true,
           "Starting Value": "default",
           "Type": "string",
           "Notes": "Siren tone selection"
       }
   ]

Example Humidifier Registry
***************************

Humidifiers control humidity levels with configurable target humidity and operating modes.

.. code-block:: json

   [
       {
           "Entity ID": "humidifier.bedroom",
           "Entity Point": "state",
           "Volttron Point Name": "humidifier_state",
           "Units": "On / Off",
           "Units Details": "off: 0, on: 1",
           "Writable": true,
           "Starting Value": 0,
           "Type": "int",
           "Notes": "Humidifier on/off control"
       },
       {
           "Entity ID": "humidifier.bedroom",
           "Entity Point": "humidity",
           "Volttron Point Name": "humidifier_target",
           "Units": "Percent",
           "Units Details": "0-100",
           "Writable": true,
           "Starting Value": 50,
           "Type": "int",
           "Notes": "Target humidity level"
       },
       {
           "Entity ID": "humidifier.bedroom",
           "Entity Point": "mode",
           "Volttron Point Name": "humidifier_mode",
           "Units": "Mode",
           "Units Details": "Device-specific modes (e.g., normal, eco, boost)",
           "Writable": true,
           "Starting Value": "normal",
           "Type": "string",
           "Notes": "Humidifier operating mode"
       },
       {
           "Entity ID": "humidifier.bedroom",
           "Entity Point": "current_humidity",
           "Volttron Point Name": "humidifier_current",
           "Units": "Percent",
           "Units Details": "0-100",
           "Writable": false,
           "Starting Value": 0,
           "Type": "int",
           "Notes": "Current humidity reading (read-only)"
       }
   ]

Example Lawn Mower Registry
***************************

Lawn mowers are robotic mowing devices that can be controlled to mow, pause, or return to dock.

State mapping:

- **Write values**: 0 = dock, 1 = start mowing, 2 = pause
- **Read values**: 0 = docked, 1 = mowing, 2 = paused, 3 = returning, 4 = error

.. code-block:: json

   [
       {
           "Entity ID": "lawn_mower.garden",
           "Entity Point": "state",
           "Volttron Point Name": "mower_state",
           "Units": "State",
           "Units Details": "Write: 0=dock, 1=mow, 2=pause; Read: 0=docked, 1=mowing, 2=paused, 3=returning, 4=error",
           "Writable": true,
           "Starting Value": 0,
           "Type": "int",
           "Notes": "Lawn mower state control"
       },
       {
           "Entity ID": "lawn_mower.garden",
           "Entity Point": "battery_level",
           "Volttron Point Name": "mower_battery",
           "Units": "Percent",
           "Units Details": "0-100",
           "Writable": false,
           "Starting Value": 0,
           "Type": "int",
           "Notes": "Battery level (read-only)"
       }
   ]

Storing Configuration
+++++++++++++++++++++

Transfer the registers files and the config files into the VOLTTRON config store using the commands below:

.. code-block:: bash

   vctl config store platform.driver light.example.json HomeAssistant_Driver/light.example.json
   vctl config store platform.driver devices/BUILDING/ROOM/light.example HomeAssistant_Driver/light.example.config

Upon completion, initiate the platform driver. Utilize the listener agent to verify the driver output:

.. code-block:: bash

   2023-09-12 11:37:00,226 (listeneragent-3.3 211531) __main__ INFO: Peer: pubsub, Sender: platform.driver:, Bus: , Topic: devices/BUILDING/ROOM/light.example/all, Headers: {'Date': '2023-09-12T18:37:00.224648+00:00', 'TimeStamp': '2023-09-12T18:37:00.224648+00:00', 'SynchronizedTimeStamp': '2023-09-12T18:37:00.000000+00:00', 'min_compatible_version': '3.0', 'max_compatible_version': ''}, Message:
   [{'light_brightness': 254, 'state': 'on'},
    {'light_brightness': {'type': 'integer', 'tz': 'UTC', 'units': 'int'},
     'state': {'type': 'integer', 'tz': 'UTC', 'units': 'On / Off'}}]

Running Tests
+++++++++++++++++++++++

To run tests on the VOLTTRON home assistant driver you need to create test entities in your Home Assistant instance.

**Required Test Entities:**

1. **Input Boolean** (required): Go to **Settings > Devices & services > Helpers > Create Helper > Toggle**. Name it **volttrontest**. This creates ``input_boolean.volttrontest``.

2. **Optional entities** for full test coverage (requires `HACS Virtual integration <https://github.com/twrecked/hass-virtual>`_):
   
   - ``fan.volttrontest`` - Virtual fan
   - ``switch.volttrontest`` - Virtual switch
   - ``siren.volttrontest`` - Virtual siren
   - ``humidifier.volttrontest`` - Virtual humidifier
   - ``lawn_mower.volttrontest`` - Virtual lawn mower

**Configure test credentials** in ``services/core/PlatformDriverAgent/tests/test_home_assistant.py``:

.. code-block:: python

   HOMEASSISTANT_TEST_IP = ""  # localhost since HA is running locally
   ACCESS_TOKEN = ""  #: Add your long-lived access token from Home Assistant
   PORT = ""# Default Home Assistant port

**Run the tests** from the root of your VOLTTRON directory:

.. code-block:: bash

   export PYTHONPATH="/path/to/volttron:$PYTHONPATH"
   pytest services/core/PlatformDriverAgent/tests/test_home_assistant.py -v

**Test Summary:**

- With only ``input_boolean.volttrontest``: 3 tests will pass
- With all virtual entities: 30 tests will pass (remaining tests are skipped due to RabbitMQ configuration)

Home Assistant REST API Reference
+++++++++++++++++++++++++++++++++

The driver uses the Home Assistant REST API for all operations. For more information, see:

- `Home Assistant REST API Documentation <https://developers.home-assistant.io/docs/api/rest>`_
- `Home Assistant Entity Documentation <https://developers.home-assistant.io/docs/core/entity>`_
