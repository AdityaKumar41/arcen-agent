---
name: homeassistant-on-this-box
description: "Control and automate Home Assistant — manage entities, automations, lights, switches, climate, and scripts via the HA REST API or CLI."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [home-assistant, smart-home, iot, automation, hass]
    category: smart-home
    related_skills: [openhue]
---

# Home Assistant Skill

Control a local or remote Home Assistant instance — toggle lights, switches,
run scripts, trigger automations, query entity states, and build complex
automations — all via the HA REST API, `hass-cli`, or direct WebSocket.

## When to Use

Use this skill whenever the user mentions:
- "Home Assistant" or "HA" or "HASS"
- Controlling smart home devices through HA
- Running HA automations or scripts
- Checking entity states, sensors, or device statuses
- Creating or editing HA automations and scripts

## Prerequisites

```bash
# Python REST client
pip install requests

# hass-cli (Home Assistant CLI)
pip install homeassistant-cli
# OR via homebrew:
brew install homeassistant-cli   # macOS

# Configure hass-cli
hass-cli --server http://homeassistant.local:8123 \
          --token "YOUR_LONG_LIVED_TOKEN" \
          info
```

**Get a Long-Lived Access Token:**
1. Go to your HA UI → Profile (bottom left)
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token" → name it → copy it

Store the token in your `.env` or `~/.config/hass-cli/config.yaml`:
```yaml
server: "http://homeassistant.local:8123"
token: "YOUR_LONG_LIVED_TOKEN"
```

## Quick Reference

| Task | REST API | hass-cli |
|---|---|---|
| Get entity state | `GET /api/states/{entity_id}` | `hass-cli state get {entity_id}` |
| Call a service | `POST /api/services/{domain}/{service}` | `hass-cli service call {domain}.{service}` |
| List entities | `GET /api/states` | `hass-cli state list` |
| Fire an event | `POST /api/events/{event_type}` | `hass-cli event fire {event_type}` |
| Check HA status | `GET /api/` | `hass-cli info` |

## REST API Usage

```python
import requests
import os

HA_URL = "http://homeassistant.local:8123"
TOKEN = os.environ.get("HA_TOKEN", "YOUR_LONG_LIVED_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

def get_state(entity_id: str) -> dict:
    """Get the current state of a HA entity."""
    resp = requests.get(f"{HA_URL}/api/states/{entity_id}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def call_service(domain: str, service: str, data: dict = None) -> list:
    """Call a HA service (e.g., light.turn_on)."""
    resp = requests.post(
        f"{HA_URL}/api/services/{domain}/{service}",
        headers=HEADERS,
        json=data or {}
    )
    resp.raise_for_status()
    return resp.json()

def list_entities(domain: str = None) -> list:
    """List all entity states, optionally filtered by domain."""
    resp = requests.get(f"{HA_URL}/api/states", headers=HEADERS)
    resp.raise_for_status()
    states = resp.json()
    if domain:
        states = [s for s in states if s["entity_id"].startswith(f"{domain}.")]
    return states
```

## Common Operations

### Toggle Lights

```python
# Turn on a specific light
call_service("light", "turn_on", {
    "entity_id": "light.living_room",
    "brightness": 200,           # 0-255
    "color_temp": 3000,          # Kelvin
})

# Turn off
call_service("light", "turn_off", {"entity_id": "light.bedroom"})

# Toggle
call_service("light", "toggle", {"entity_id": "light.kitchen"})

# Turn on all lights in an area
call_service("light", "turn_on", {"area_id": "living_room"})
```

### Control Switches

```python
call_service("switch", "turn_on", {"entity_id": "switch.coffee_maker"})
call_service("switch", "turn_off", {"entity_id": "switch.coffee_maker"})
```

### Climate Control

```python
# Set temperature
call_service("climate", "set_temperature", {
    "entity_id": "climate.thermostat",
    "temperature": 22,            # Celsius
    "hvac_mode": "cool"           # heat, cool, auto, off
})

# Check current state
state = get_state("climate.thermostat")
print(f"Current temp: {state['attributes']['current_temperature']}°C")
print(f"Target temp: {state['attributes']['temperature']}°C")
print(f"Mode: {state['state']}")
```

### Run Scripts & Automations

```python
# Run a script
call_service("script", "turn_on", {"entity_id": "script.good_morning"})

# Trigger an automation
call_service("automation", "trigger", {"entity_id": "automation.evening_mode"})

# Enable/disable an automation
call_service("automation", "turn_on", {"entity_id": "automation.evening_mode"})
call_service("automation", "turn_off", {"entity_id": "automation.evening_mode"})
```

### Query Sensors

```python
# Read a temperature sensor
state = get_state("sensor.outdoor_temperature")
print(f"Outdoor temp: {state['state']} {state['attributes']['unit_of_measurement']}")

# List all sensors
sensors = list_entities("sensor")
for sensor in sensors:
    print(f"{sensor['entity_id']}: {sensor['state']}")
```

### Using hass-cli

```bash
# Check connection
hass-cli info

# Get entity state
hass-cli state get light.living_room

# List all lights
hass-cli state list --filter-entity-id "light.*"

# Call a service
hass-cli service call light.turn_on \
  --arguments entity_id=light.living_room,brightness=200

# Trigger an automation
hass-cli service call automation.trigger \
  --arguments entity_id=automation.morning_routine

# Fire a custom event
hass-cli event fire my_custom_event --json '{"key": "value"}'

# List all automations
hass-cli state list --filter-entity-id "automation.*"
```

## Automation YAML Structure

When the user wants to create an automation, generate valid YAML for
`configuration.yaml` or the `/config/automations.yaml` file:

```yaml
automation:
  - id: "unique_automation_id"
    alias: "Evening Mode"
    description: "Turn on lights at sunset"
    trigger:
      - platform: sun
        event: sunset
        offset: "-00:30:00"    # 30 min before sunset
    condition:
      - condition: time
        weekday:
          - mon
          - tue
          - wed
          - thu
          - fri
    action:
      - service: light.turn_on
        target:
          area_id: living_room
        data:
          brightness: 150
          color_temp: 3000
      - delay:
          minutes: 5
      - service: light.turn_on
        target:
          entity_id: light.kitchen
        data:
          brightness: 200
```

After generating, tell the user to:
1. Add it to `automations.yaml`
2. Call `call_service("homeassistant", "reload_all", {})` or run
   `hass-cli service call homeassistant.reload_all`

## Error Handling

```python
def safe_call_service(domain, service, data=None):
    try:
        result = call_service(domain, service, data)
        return {"ok": True, "result": result}
    except requests.HTTPError as e:
        return {"ok": False, "error": str(e), "status": e.response.status_code}
    except requests.ConnectionError:
        return {"ok": False, "error": "Cannot reach Home Assistant. Check URL and network."}
```

## Gotchas

- **Entity IDs are exact:** `light.living_room` ≠ `light.Living_Room`.
  Use `list_entities()` to discover the correct ID.
- **Token expiry:** Long-lived tokens don't expire unless you delete them.
  Store them securely in `.env`, never in source code.
- **WebSocket for real-time:** For watching entity state changes live, use
  the WebSocket API (`ws://homeassistant.local:8123/api/websocket`). REST
  API is request-response only.
- **SSL:** Production HA setups use HTTPS. Replace `http://` with `https://`
  and set `verify=True` in requests (or point to your CA certificate).
- **Area vs entity targeting:** `area_id` applies the action to all entities
  in a named area. `entity_id` targets a specific entity.
