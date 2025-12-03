.. _HomeAssistant-Driver:

Home Assistant Driver
=====================

The Home Assistant driver enables VOLTTRON to read any data point from any Home Assistant controlled device.
Currently control(write access) is supported for lights (state and brightness), thermostats (state and temperature), switches (state), fans (state, percentage, preset mode, direction, oscillation), sirens (state, volume level, tone, duration), humidifiers (state, humidity, mode), and lawn mowers (state: dock/mow/pause).

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
Examples for lights and thermostats are provided below.

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
such as "light.",  "climate." etc. The driver uses these prefixes to convert states into integers.
Like mentioned before, the driver can only control lights and thermostats but can get data from all devices
controlled by home assistant

Each entry in a registry file should also have a 'Entity Point' and a unique value for 'Volttron Point Name'. The 'Entity ID' maps to the device instance, the 'Entity Point' extracts the attribute or state, and 'Volttron Point Name' determines the name of that point as it appears in VOLTTRON.

Attributes can be located in the developer tools in the Home Assistant GUI.

.. image:: home-assistant.png


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
           "Type": "boolean",
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
           "Writable": true,
           "Starting Value": 72,
           "Type": "float",
           "Notes": "Current temperature reading"
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

Write Operations
================

The Home Assistant driver now supports write-access functionality for controlling devices. This allows you to send commands to devices through VOLTTRON's platform driver.

Supported Writable Devices
---------------------------

The following device types support write operations:

1. **Switch** - Simple on/off devices (smart plugs, relays, etc.)
2. **Siren** - Alarm/notification devices with sound control
3. **Humidifier** - Humidity control devices
4. **Lawn Mower** - Robotic lawn mowing devices
5. **Light** - Lighting devices with brightness control
6. **Fan** - Fan devices with speed and direction control
7. **Climate** - HVAC/thermostat devices
8. **Input Boolean** - Virtual on/off switches

Configuring Writable Points
----------------------------

To enable write operations for a device, set the ``Writable`` field to ``TRUE`` in your device registry CSV file.

**Example CSV configuration for a writable switch:**

.. code-block:: csv

   Volttron Point Name,Entity ID,Entity Point,Units,Units Details,Writable,Type,Notes
   switch_state,switch.living_room_plug,state,On/Off,1/0,TRUE,int,Living room smart plug
   switch_power,switch.living_room_plug,current_power_w,W,Watts,FALSE,float,Current power consumption

Switch Operations
-----------------

Switches are simple on/off devices like smart plugs and relays.

**Set switch state (on/off):**

.. code-block:: bash

   # Turn switch ON
   vctl rpc platform.driver set_point BUILDING/ROOM/switch switch_state 1

   # Turn switch OFF
   vctl rpc platform.driver set_point BUILDING/ROOM/switch switch_state 0

**Supported write points:**

- ``state``: 0 (off) or 1 (on)

Siren Operations
----------------

Sirens are alarm/notification devices that can produce sound with customizable properties.

**Set siren state:**

.. code-block:: bash

   # Turn siren ON
   vctl rpc platform.driver set_point BUILDING/ROOM/siren siren_state 1

   # Turn siren OFF
   vctl rpc platform.driver set_point BUILDING/ROOM/siren siren_state 0

**Set siren volume level:**

.. code-block:: bash

   # Set volume to 50% (0.5)
   vctl rpc platform.driver set_point BUILDING/ROOM/siren siren_volume_level 0.5

   # Set volume to maximum (1.0)
   vctl rpc platform.driver set_point BUILDING/ROOM/siren siren_volume_level 1.0

**Set siren tone:**

.. code-block:: bash

   # Set a specific tone (check your device's available_tones attribute)
   vctl rpc platform.driver set_point BUILDING/ROOM/siren siren_tone "emergency"

**Set siren duration:**

.. code-block:: bash

   # Sound siren for 30 seconds
   vctl rpc platform.driver set_point BUILDING/ROOM/siren siren_duration 30

**Supported write points:**

- ``state``: 0 (off) or 1 (on)
- ``volume_level``: 0.0 to 1.0 (0% to 100%)
- ``tone``: String (must be one of the device's available tones)
- ``duration``: Positive integer (seconds)

**Example CSV configuration:**

.. code-block:: csv

   Volttron Point Name,Entity ID,Entity Point,Units,Units Details,Writable,Type,Notes
   siren_state,siren.alarm,state,On/Off,1/0,TRUE,int,Alarm siren state
   siren_volume_level,siren.alarm,volume_level,Percent,0.0-1.0,TRUE,float,Siren volume level
   siren_tone,siren.alarm,tone,String,Tone name,TRUE,string,Siren tone selection

Humidifier Operations
---------------------

Humidifiers control humidity levels in a space.

**Set humidifier state:**

.. code-block:: bash

   # Turn humidifier ON
   vctl rpc platform.driver set_point BUILDING/ROOM/humidifier humidifier_state 1

   # Turn humidifier OFF
   vctl rpc platform.driver set_point BUILDING/ROOM/humidifier humidifier_state 0

**Set target humidity:**

.. code-block:: bash

   # Set target humidity to 60%
   vctl rpc platform.driver set_point BUILDING/ROOM/humidifier humidifier_humidity 60

**Set humidifier mode:**

.. code-block:: bash

   # Set to normal mode (check your device's available_modes attribute)
   vctl rpc platform.driver set_point BUILDING/ROOM/humidifier humidifier_mode "normal"

**Supported write points:**

- ``state``: 0 (off) or 1 (on)
- ``humidity``: 0 to 100 (target humidity percentage)
- ``mode``: String (must be one of the device's available modes, e.g., "normal", "eco", "boost")

**Example CSV configuration:**

.. code-block:: csv

   Volttron Point Name,Entity ID,Entity Point,Units,Units Details,Writable,Type,Notes
   humidifier_state,humidifier.bedroom,state,On/Off,1/0,TRUE,int,Bedroom humidifier state
   humidifier_humidity,humidifier.bedroom,humidity,Percent,%,TRUE,int,Target humidity level
   humidifier_mode,humidifier.bedroom,mode,String,Mode name,TRUE,string,Operating mode
   current_humidity,humidifier.bedroom,current_humidity,Percent,%,FALSE,int,Current humidity reading

Lawn Mower Operations
---------------------

Lawn mowers are robotic mowing devices with multiple operational states.

**Control lawn mower:**

.. code-block:: bash

   # Start mowing
   vctl rpc platform.driver set_point BUILDING/YARD/mower mower_state 1

   # Pause mowing
   vctl rpc platform.driver set_point BUILDING/YARD/mower mower_state 2

   # Return to dock
   vctl rpc platform.driver set_point BUILDING/YARD/mower mower_state 0

**State mapping:**

- ``0``: Docked (sends mower to dock)
- ``1``: Mowing (starts mowing operation)
- ``2``: Paused (pauses current operation)
- ``3``: Returning (read-only state - mower is returning to dock)
- ``4``: Error (read-only state - mower encountered an error)

**Supported write points:**

- ``state``: 0 (dock), 1 (start_mowing), or 2 (pause)

**Example CSV configuration:**

.. code-block:: csv

   Volttron Point Name,Entity ID,Entity Point,Units,Units Details,Writable,Type,Notes
   mower_state,lawn_mower.backyard,state,State,0-4,TRUE,int,Lawn mower operational state
   mower_battery,lawn_mower.backyard,battery_level,Percent,%,FALSE,int,Battery level

Reading Device States
---------------------

All writable devices can also be read to check their current state:

.. code-block:: bash

   # Read current state
   vctl rpc platform.driver get_point BUILDING/ROOM/device device_state

   # Scrape all points for a device
   vctl rpc platform.driver scrape_all BUILDING/ROOM/device

Complete Configuration Example
-------------------------------

Here's a complete example showing multiple writable devices in a single registry file:

**multi_device.csv:**

.. code-block:: csv

   Volttron Point Name,Entity ID,Entity Point,Units,Units Details,Writable,Type,Notes
   switch_state,switch.living_room_plug,state,On/Off,1/0,TRUE,int,Smart plug control
   siren_state,siren.security_alarm,state,On/Off,1/0,TRUE,int,Security alarm
   siren_volume,siren.security_alarm,volume_level,Level,0.0-1.0,TRUE,float,Alarm volume
   humidifier_state,humidifier.bedroom,state,On/Off,1/0,TRUE,int,Bedroom humidifier
   humidifier_target,humidifier.bedroom,humidity,Percent,%,TRUE,int,Target humidity
   mower_state,lawn_mower.backyard,state,State,0-4,TRUE,int,Robotic mower control

**Configuration file (multi_device.config):**

.. code-block:: json

   {
       "driver_config": {
           "ip": "192.168.1.100",
           "port": 8123,
           "token": "your_long_lived_access_token_here"
       },
       "driver_type": "homeassistant",
       "registry_config": "config://multi_device.csv",
       "interval": 5,
       "timezone": "UTC"
   }

**Install the configuration:**

.. code-block:: bash

   vctl config store platform.driver multi_device.csv multi_device.csv --csv
   vctl config store platform.driver devices/BUILDING/ROOM/multi_device multi_device.config

Error Handling
--------------

When a write operation fails, the driver will log an error message. Common errors include:

- **Invalid value**: The value provided is outside the acceptable range
- **Connection error**: Cannot reach the Home Assistant instance
- **Permission denied**: The access token doesn't have permission to control the device
- **Device unavailable**: The device is offline or not responding

Check ``volttron.log`` for detailed error messages:

.. code-block:: bash

   tail -f volttron.log


Running Tests
+++++++++++++++++++++++

Prerequisites for Testing
**************************

To run tests on the VOLTTRON Home Assistant driver, you need to create test entities in your Home Assistant instance:

**Required Test Entities:**

1. **Input Boolean**: Settings > Devices & services > Helpers > Create Helper > Toggle
   - Name: ``volttrontest``

2. **Fan**: Create via HACS virtual integration or use a real fan device
   - Entity ID: ``fan.volttrontest``

3. **Switch**: Settings > Devices & services > Helpers > Create Helper > Toggle (or use real switch)
   - Entity ID: ``switch.volttrontest``

4. **Siren**: Requires HACS virtual siren or real device
   - Entity ID: ``siren.volttrontest``

5. **Humidifier**: Requires HACS virtual humidifier or real device
   - Entity ID: ``humidifier.volttrontest``

6. **Lawn Mower**: Requires HACS virtual lawn mower or real device
   - Entity ID: ``lawn_mower.volttrontest``

For virtual devices, install HACS (Home Assistant Community Store) and add the "Virtual" integration from: https://github.com/twrecked/hass-virtual

Running the Tests
*****************

After setting up the required test entities and configuring your test credentials in ``test_home_assistant.py``, run the tests from the root of your VOLTTRON installation:

.. code-block:: bash

    pytest services/core/PlatformDriverAgent/tests/test_home_assistant.py -v

The test suite includes comprehensive integration tests for all supported entity types:

- Input Boolean tests (existing)
- Fan tests (existing)
- Switch tests (on/off control)
- Siren tests (state, volume, tone, duration)
- Humidifier tests (state, humidity level, mode)
- Lawn Mower tests (start, pause, dock, full cycle)

If all tests pass successfully, you should see approximately **28+ passed tests** (the exact number may vary as tests are added).
