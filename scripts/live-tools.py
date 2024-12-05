from pywebio.input import *
from pywebio.output import *
from pywebio import start_server
import requests
import time

#######################################################
#Hard Coded Variables
#######################################################

BASE_URL = 'https://api.meraki.com/api/v1'
org_id = 12345678 # Paste your Org ID here
api_key = "ABCDEFG12345678#!@" # Paste your API Key here

#######################################################
#Shared Functions
#######################################################

#Function to get a list of networks in the organization
def get_organization_networks(api_key):
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    headers = {
        "Content-Type": "application/json",
        "X-Cisco-Meraki-API-Key": api_key
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response

#Function to get a list of devices in the organization
def get_organization_devices(api_key):
    url = f"{BASE_URL}/organizations/{org_id}/devices"
    headers = {
        "X-Cisco-Meraki-API-Key": api_key
    }
    response = requests.get(url, headers=headers)
    return response

#######################################################
#Live Tools
#######################################################

#Function to blink device LEDs
def blink_device_leds(api_key, serial):
    url = f"{BASE_URL}/devices/{serial}/blinkLeds"
    headers = {
        "Content-Type": "application/json",
        "X-Cisco-Meraki-API-Key": api_key
    }
    response = requests.post(url, headers=headers)
    return response

#Function to handle the "Blink LED" process
def blink_led():
    clear()
    put_markdown("## Blink Device LED")

    #Fetch the list of devices in the organization
    response = get_organization_devices(api_key)
    if response.status_code == 200:
        devices = response.json()
        device_options = [{"label": f"{device['name']} ({device['serial']})", "value": device["serial"]} for device in devices if device.get("networkId")]
        selected_devices = checkbox("Select device(s) to blink their LEDs:", options=device_options)

        # Call the API to blink the device LEDs for each selected device
        for serial in selected_devices:
            response = blink_device_leds(api_key, serial)
            if response.status_code == 202:
                put_text(f"LEDs on device with serial '{serial}' are blinking!")
            else:
                put_error(f"Failed to blink LEDs on device with serial '{serial}'. Status code: {response.status_code}, Error: {response.text}")
    else:
        put_error(f"Failed to retrieve devices. Status code: {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Function to Create a Ping from a Meraki Device
def create_ping(device_serial, target_ip):
    url = f"{BASE_URL}/devices/{device_serial}/liveTools/ping"
    headers = {
        'X-Cisco-Meraki-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'target': target_ip
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        response.raise_for_status()  # Raise an error for bad status codes
        if response.status_code == 201:
            return response.json()
        else:
            put_text(f"Unexpected status code: {response.status_code}")
    except requests.exceptions.HTTPError as http_err:
        put_text(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        put_text(f"Request error occurred: {req_err}")
    except ValueError:
        put_text(f"Invalid JSON response: {response.text}")

#Function to get Ping from Meraki Devices
def get_ping(device_serial, ping_id):
    url = f"{BASE_URL}/devices/{device_serial}/liveTools/ping/{ping_id}"
    headers = {
        'X-Cisco-Meraki-API-Key': api_key,
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)

    try:
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        put_text(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        put_text(f"Request error occurred: {req_err}")
    except ValueError:
        put_text(f"Invalid JSON response: {response.text}")

#Function for Ping Tool
def ping_tool():
    clear()
    put_markdown("## Ping Tool")

    # Fetch the list of devices in the organization
    response = get_organization_devices(api_key)
    if response.status_code == 200:
        devices = response.json()
        if not devices:
            put_error("No devices found in the organization.")
            put_buttons(["Back to Menu"], onclick=[main])
            return
    else:
        put_error(f"Failed to retrieve devices. Status code: {response.status_code}, Error: {response.text}")
        put_buttons(["Back to Menu"], onclick=[main])
        return

    # Filter devices based on productType
    valid_product_types = {'wireless', 'appliance', 'switch', 'camera', 'cellularGateway', 'wirelessController'}
    filtered_devices = [device for device in devices if device.get('productType') in valid_product_types]

    if not filtered_devices:
        put_error("No valid devices found with the specified product types.")
        put_buttons(["Back to Menu"], onclick=[main])
        return

    device_options = [{"label": f"{device['name']} ({device['serial']})", "value": device["serial"]} for device in filtered_devices if device.get("networkId")]
    selected_device_serial = radio("Select a device to run the ping from:", options=device_options)
    target_ip = input("Enter Target IP Address:", type="text", value="8.8.8.8")

    ping_response = create_ping(selected_device_serial, target_ip)
    if ping_response and 'pingId' in ping_response:
        ping_id = ping_response['pingId']
        put_text(f"Ping created with ID: {ping_id}")

        start_time = time.time()

        while True:
            ping_result = get_ping(selected_device_serial, ping_id)
            status = ping_result.get('status', 'Unknown')

            put_text(f"Ping Status: {status}")

            if status == 'complete':
                results = ping_result.get('results', {})

                if results:
                    put_table([
                        ['Metric', 'Value'],
                        ['Sent', results.get('sent', 'N/A')],
                        ['Received', results.get('received', 'N/A')],
                        ['Loss Percentage', results.get('loss', {}).get('percentage', 'N/A')],
                        ['Minimum Latency', results.get('latencies', {}).get('minimum', 'N/A')],
                        ['Average Latency', results.get('latencies', {}).get('average', 'N/A')],
                        ['Maximum Latency', results.get('latencies', {}).get('maximum', 'N/A')]
                    ])

                    replies = results.get('replies', [])
                    if replies:
                        put_text("Replies:")
                        for reply in replies:
                            put_text(f"Sequence ID: {reply.get('sequenceId', 'N/A')}, Size: {reply.get('size', 'N/A')}, Latency: {reply.get('latency', 'N/A')}")
                else:
                    put_text("No results available.")
                break
            elif status == 'failed' or time.time() - start_time > 20:
                put_text("Ping Live Tools timed out. Check the Meraki Device is online and connected to the Meraki Dashboard.")
                break
            else:
                time.sleep(3)  # Wait for 3 seconds before checking again
    else:
        put_text("Failed to create ping")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Function to handle the reboot device API
def reboot_device(api_key, serial):
    url = f"{BASE_URL}/devices/{serial}/reboot"
    headers = {
        "Content-Type": "application/json",
        "X-Cisco-Meraki-API-Key": api_key
    }
    response = requests.post(url, headers=headers)
    return response

#Function to Reboot a Meraki Device
def reboot_device_tool():
    clear()
    put_markdown("## Reboot Device")

    # Fetch the list of networks
    response = get_organization_networks(api_key)
    if response.status_code == 200:
        networks = response.json()
        network_options = [{"label": network["name"], "value": network["id"]} for network in networks]
        selected_network = select("Select a network:", options=network_options)
    else:
        put_error(f"Failed to retrieve networks. Status code: {response.status_code}, Error: {response.text}")
        put_buttons(["Back to Menu"], onclick=[main])
        return

    # Fetch the list of devices in the selected network
    response = get_organization_devices(api_key)
    if response.status_code == 200:
        devices = response.json()
        valid_product_types = {'wireless', 'appliance', 'switch', 'camera', 'cellularGateway', 'wirelessController'}
        filtered_devices = [device for device in devices if device.get('productType') in valid_product_types and device.get('networkId') == selected_network]
        device_options = [{"label": f"{device['name']} ({device['serial']})", "value": device["serial"]} for device in filtered_devices]
        selected_device_serial = select("Select a device to reboot:", options=device_options)
    else:
        put_error(f"Failed to retrieve devices. Status code: {response.status_code}, Error: {response.text}")
        put_buttons(["Back to Menu"], onclick=[main])
        return

    # Call the API to reboot the device
    response = reboot_device(api_key, selected_device_serial)
    if response.status_code == 202:
        put_text(f"Device with serial '{selected_device_serial}' is rebooting!")
    else:
        put_error(f"Failed to reboot device with serial '{selected_device_serial}'. Status code: {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

# Main menu functions
def main():
    clear()
    put_markdown("# Meraki Dashboard")
    put_markdown("<b> Live Tools </b>")
    put_buttons(["Blink LED's", "Ping Tool", "Reboot Device"], onclick=[blink_led, ping_tool, reboot_device_tool])

# Start the PyWebIO server
if __name__ == '__main__':
    start_server(main, port=8999, debug=True)
