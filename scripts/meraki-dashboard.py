from pywebio.input import *
from pywebio.output import *
from pywebio import start_server
from datetime import datetime, timedelta
import requests
import pytz
import os
import json
import time
from pyecharts import options as opts
from pyecharts.globals import ThemeType
from pyecharts.charts import Bar, Pie
from collections import defaultdict #TODO MOVE THESE UP

#######################################################
#Hard Coded Variables
#######################################################

BASE_URL = 'https://api.meraki.com/api/v1'
org_id = 12345678 # Paste your Org ID here
api_key = "12345678ABCDEFG12345678#!@" # Paste your API Key here
home_dir = os.path.expanduser('~') # Define the path to the baseline configuration file
baseline_file_path = os.path.join(home_dir, 'baseline_config.json') # Define the path to the baseline configuration file

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

#Function to get a list of wireless networks in the organization
def get_wireless_networks(api_key):
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    headers = {
        "X-Cisco-Meraki-API-Key": api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        networks = response.json()
        wireless_networks = [network for network in networks if "wireless" in network["productTypes"]]
        return wireless_networks
    else:
        return None

#Function to get a list of Organizations
def get_organizations(api_key):
    url = f"{BASE_URL}/organizations"
    headers = {
        "Content-Type": "application/json",
        "X-Cisco-Meraki-API-Key": api_key
    }
    response = requests.get(url, headers=headers)
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

#Function to create a new Meraki network
def create_meraki_network(api_key, network_name, network_types, notes=None, timeZone=None, copyFromNetworkId=None):
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    headers = {
        "Content-Type": "application/json",
        "X-Cisco-Meraki-API-Key": api_key
    }
    payload = {
        "name": network_name,
        "productTypes": network_types,
    }
    if notes:
        payload["notes"] = notes
    if timeZone:
        payload["timeZone"] = timeZone
    if copyFromNetworkId:
        payload["copyFromNetworkId"] = copyFromNetworkId

    response = requests.post(url, headers=headers, json=payload)
    return response

#Function to handle the "Create Network" process
def create_network():
    clear()
    put_markdown("## Create a New Meraki Network")

    #api_key = input("Enter your Meraki API Key:", type="password") #This line is commmented out as we source API Key as a varible in the start of the script
    network_name = input("Enter the name of the new network:")
    network_types = checkbox("Select the type(s) of the network:", options=["appliance", "switch", "wireless", "camera", "sensor", "cellularGateway"])
    notes = input("Enter notes for the network (optional):", required=False)
    timeZone = select("Select the time zone for the network (optional):", options=pytz.all_timezones, required=False)

    #Fetch the list of networks for the copyFromNetworkId dropdown
    response = get_organization_networks(api_key)
    if response.status_code == 200:
        networks = response.json()
        network_options = [{"label": "Select a Source  Network", "value": None}] + [{"label": network["name"], "value": network["id"]} for network in networks]
        put_markdown("**IMPORTANT: If you are using this Copy From Network Option, the New Network must not have extra ProductTypes that are different from the Source Network**")
        put_text("Leave as Select a Network to not copy a network")
        copyFromNetworkId = select("Select a network to copy from (optional):", options=network_options, required=False)
    else:
        put_error(f"Failed to retrieve networks for copy option. Status code: {response.status_code}, Error: {response.text}")
        copyFromNetworkId = None

    #If "Do not Copy" is selected, set copyFromNetworkId to None
    if copyFromNetworkId == "None":
        copyFromNetworkId = None

    response = create_meraki_network(api_key, network_name, network_types, notes, timeZone, copyFromNetworkId)

    if response.status_code == 201:
        put_text(f"Network '{network_name}' created successfully!")
    else:
        put_error(f"Failed to create network. Status code: {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Function to create a new Meraki dashboard admin
def create_meraki_admin(api_key, email, name, org_access):
    url = f"https://api.meraki.com/api/v1/organizations/{org_id}/admins"
    headers = {
        "Content-Type": "application/json",
        "X-Cisco-Meraki-API-Key": api_key
    }
    payload = {
        "email": email,
        "name": name,
        "orgAccess": org_access,
    }
    response = requests.post(url, headers=headers, json=payload)
    return response

#Function to handle the "Create Dashboard Admin" process
def create_dashboard_admin():
    clear()
    put_markdown("## Create a Dashboard Admin")

    email = input("Enter the new admin's email address:")
    name = input("Enter the new admin's name:")
    org_access = checkbox("Select the level of organization access:", options=["full", "read-only"])

    if len(org_access) == 0:
        put_error("You must select at least one level of access.")
        put_buttons(["Back to Menu"], onclick=[main])
        return

    response = create_meraki_admin(api_key, email, name, org_access[0])

    if response.status_code == 201:
        put_text(f"Admin '{name}' created successfully!")
    else:
        put_error(f"Failed to create admin. Status code: {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Function to handle the "Get Organizations" process
def list_organizations():
    clear()
    put_markdown("## List of Organizations")

    response = get_organizations(api_key)

    if response.status_code == 200:
        organizations = response.json()
        table_data = [["Organization Name", "Organization ID"]]
        for org in organizations:
            table_data.append([org["name"], org["id"]])
        put_table(table_data)
    else:
        put_error(f"Failed to retrieve Organizations. Status code: {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Function to handle the "Get Networks" process
def list_networks():
    clear()
    put_markdown("## List of Networks in Organization")

    response = get_organization_networks(api_key)

    if response.status_code == 200:
        networks = response.json()
        table_data = [["Network Name", "Network ID"]]
        for network in networks:
            table_data.append([network["name"], network["id"]])
        put_table(table_data)
    else:
        put_error(f"Failed to retrieve networks. Status code:  {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Function to delete a Meraki network
def delete_meraki_network(api_key, network_id):
    url = f"{BASE_URL}/networks/{network_id}"
    headers = {
        "X-Cisco-Meraki-API-Key": api_key
    }
    response = requests.delete(url, headers=headers)
    return response

#Function to handle the "Delete Network" process
def delete_network():
    clear()
    put_markdown("## Delete a Network")
    put_text('WARNING! This option will delete the selected networks without asking! Are you sure!').style('color: red; font-size: 20px')

    response = get_organization_networks(api_key)

    if response.status_code == 200:
        networks = response.json()
        network_options = [{"label": network["name"], "value": network["id"]} for network in networks]
        selected_networks = checkbox("Select the network(s) to delete:", options=network_options)

        if not selected_networks:
            put_error("You must select at least one network to delete.")
            put_buttons(["Back to Menu"], onclick=[main])
            return

        for network_id in selected_networks:
            response = delete_meraki_network(api_key, network_id)
            if response.status_code == 204:
                put_text(f"Network with ID '{network_id}' deleted successfully!")
            else:
                put_error(f"Failed to delete network with ID '{network_id}'. Status code: {response.status_code}, Error: {response.text}")

    else:
        put_error(f"Failed to retrieve networks. Status code: {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Function to get wireless connection stats
def get_network_wireless_connection_stats(api_key, network_id, t0, t1):
    url = f"{BASE_URL}/networks/{network_id}/wireless/connectionStats"
    headers = {
        "X-Cisco-Meraki-API-Key": api_key
    }
    params = {
        "t0": t0,
        "t1": t1
    }
    response = requests.get(url, headers=headers, params=params)
    return response

#Function to display wireless stats in a bar chart using pyecharts
def display_wireless_stats(stats):
    if "assoc" in stats and "auth" in stats and "dhcp" in stats and "dns" in stats and "success" in stats:
        data = {
            "assoc": stats["assoc"],
            "auth": stats["auth"],
            "dhcp": stats["dhcp"],
            "dns": stats["dns"],
            "success": stats["success"]
        }
        categories = list(data.keys())
        values = list(data.values())

        bar = (
            Bar()
            .add_xaxis(categories)
            .add_yaxis("Wireless Network Connection Stats", values, color='rgba(103,179,70,255)')
            .set_global_opts(title_opts=opts.TitleOpts(title="Wireless Network Connection Stats"))
        )
        put_html(bar.render_notebook())
    else:
        put_error("No connection stats available.")

#Function to handle the "Get Wireless Network Stats" process
def get_wireless_network_stats():
    clear()
    put_markdown("## Get Wireless Network Stats")

    #Fetch the list of wireless networks
    wireless_networks = get_wireless_networks(api_key)
    if not wireless_networks:
        put_error("Failed to retrieve wireless networks.")
        put_buttons(["Back to Menu"], onclick=[main])
        return

    network_options = [{"label": network["name"], "value": network["id"]} for network in wireless_networks]
    selected_network = select("Select a wireless network:", options=network_options)
    put_markdown("##### The time range is defaulted to the last 1 day")
    t0_str = input("Enter the start date and time (YYYY-MM-DD HH:MM:SS):", type=TEXT, value=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'))
    t1_str = input("Enter the end date and time (YYYY-MM-DD HH:MM:SS):", type=TEXT, value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    clear()
    put_markdown("## Get Wireless Network Stats")
    #Convert the date and time strings to Unix timestamps
    t0 = int(datetime.strptime(t0_str, '%Y-%m-%d %H:%M:%S').timestamp())
    t1 = int(datetime.strptime(t1_str, '%Y-%m-%d %H:%M:%S').timestamp())

    #Call the API to get wireless connection stats
    response = get_network_wireless_connection_stats(api_key, selected_network, t0, t1)
    if response.status_code == 200:
        stats = response.json()
        display_wireless_stats(stats)
    else:
        put_error(f"Failed to retrieve wireless network stats. Status code: {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Function to get wireless client connection stats
def get_network_wireless_client_connection_stats(api_key, network_id, t0, t1):
    url = f"{BASE_URL}/networks/{network_id}/wireless/clients/connectionStats"
    headers = {
        "X-Cisco-Meraki-API-Key": api_key
    }
    params = {
        "t0": t0,
        "t1": t1
    }
    response = requests.get(url, headers=headers, params=params)
    return response

#Function to display wireless client stats in a bar chart using pyecharts
def display_wireless_client_stats(stats):
    if stats:
        categories = []
        assoc_values = []
        auth_values = []
        dhcp_values = []
        dns_values = []
        success_values = []

        for client in stats:
            mac = client["mac"]
            connection_stats = client["connectionStats"]
            categories.append(mac)
            assoc_values.append(connection_stats["assoc"])
            auth_values.append(connection_stats["auth"])
            dhcp_values.append(connection_stats["dhcp"])
            dns_values.append(connection_stats["dns"])
            success_values.append(connection_stats["success"])

        bar = (
            Bar()
            .add_xaxis(categories)
            .add_yaxis("Assoc", assoc_values, color='rgba(75, 192, 192, 0.8)')
            .add_yaxis("Auth", auth_values, color='rgba(54, 162, 235, 0.8)')
            .add_yaxis("DHCP", dhcp_values, color='rgba(255, 206, 86, 0.8)')
            .add_yaxis("DNS", dns_values, color='rgba(255, 99, 132, 0.8)')
            .add_yaxis("Success", success_values, color='rgba(103,179,70,255)')
            .set_global_opts(
                title_opts=opts.TitleOpts(title="Stats"),
                xaxis_opts=opts.AxisOpts(name="Client MAC Address", axislabel_opts=opts.LabelOpts(rotate=45)),
                yaxis_opts=opts.AxisOpts(name="Count"),
                tooltip_opts=opts.TooltipOpts(is_show=True),
                datazoom_opts=[opts.DataZoomOpts(), opts.DataZoomOpts(type_="inside")]
            )
        )
        put_html(bar.render_notebook())
    else:
        put_error("No client connection stats available.")

#Function to handle the "Get Wireless Client Connection Stats" process
def get_wireless_client_connection_stats():
    clear()
    put_markdown("## Get Wireless Client Connection Stats")

    #Fetch the list of wireless networks
    wireless_networks = get_wireless_networks(api_key)
    if not wireless_networks:
        put_error("Failed to retrieve wireless networks.")
        put_buttons(["Back to Menu"], onclick=[main])
        return

    network_options = [{"label": network["name"], "value": network["id"]} for network in wireless_networks]
    selected_network = select("Select a wireless network:", options=network_options)

    put_markdown("##### The time range is defaulted to the last 1 day")
    t0_str = input("Enter the start date and time (YYYY-MM-DD HH:MM:SS):", type=TEXT, value=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'))
    t1_str = input("Enter the end date and time (YYYY-MM-DD HH:MM:SS):", type=TEXT, value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    clear()
    put_markdown("## Get Wireless Client Connection Stats")
    #Convert the date and time strings to Unix timestamps
    t0 = int(datetime.strptime(t0_str, '%Y-%m-%d %H:%M:%S').timestamp())
    t1 = int(datetime.strptime(t1_str, '%Y-%m-%d %H:%M:%S').timestamp())

    #Call the API to get wireless client connection stats
    response = get_network_wireless_client_connection_stats(api_key, selected_network, t0, t1)
    if response.status_code == 200:
        stats = response.json()
        display_wireless_client_stats(stats)
    else:
        put_error(f"Failed to retrieve wireless client connection stats. Status code: {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Functions to get the Layer 3 firewall rules for a network and store in the baseline file
def get_firewall_rules(network_id, api_key):
    url = f'{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules'
    headers = {
        'X-Cisco-Meraki-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def normalize_rules(rules):
    """Normalize the firewall rules for comparison."""
    if isinstance(rules, dict) and 'rules' in rules:
        rules = rules['rules']
    for rule in rules:
        rule.pop('createdAt', None)
        rule.pop('updatedAt', None)
    return sorted(rules, key=lambda x: json.dumps(x, sort_keys=True))

def get_baseline_configuration():
    """Get the baseline configuration and save it to a file."""
    clear()
    put_markdown("## Get Baseline Configuration")

    #Fetch the list of networks
    response = get_organization_networks(api_key)
    if response.status_code == 200:
        networks = response.json()
        mx_networks = [net for net in networks if 'appliance' in net['productTypes']]

        network_choices = {net['name']: net['id'] for net in mx_networks}
        selected_network = select("Select a network", options=network_choices.keys())
        network_id = network_choices[selected_network]

        firewall_rules = get_firewall_rules(network_id, api_key)
        normalized_rules = normalize_rules(firewall_rules)

        #Load existing baseline configurations
        if os.path.exists(baseline_file_path):
            with open(baseline_file_path, 'r') as f:
                baseline_configs = json.load(f)
        else:
            baseline_configs = {}

        #Update the baseline configuration for the selected network
        baseline_configs[network_id] = normalized_rules

        #Save the updated baseline configurations
        with open(baseline_file_path, 'w') as f:
            json.dump(baseline_configs, f)

        put_text("Baseline configuration saved.")
    else:
        put_error(f"Failed to retrieve networks. Status code: {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Function to Compare the Baseline Layer 3 Firewall Rules
def compare_baseline_configuration():
    """Compare the current configuration with the baseline configuration."""
    clear()
    put_markdown("## Compare Baseline Configuration")
    if not os.path.exists(baseline_file_path):
        put_text("Baseline configuration not found. Please create a baseline first.")
        return

    #Fetch the list of networks
    response = get_organization_networks(api_key)
    if response.status_code == 200:
        networks = response.json()
        mx_networks = [net for net in networks if 'appliance' in net['productTypes']]

        network_choices = {net['name']: net['id'] for net in mx_networks}
        selected_network = select("Select a network", options=network_choices.keys())
        network_id = network_choices[selected_network]

        current_rules = get_firewall_rules(network_id, api_key)
        normalized_current_rules = normalize_rules(current_rules)

    with open(baseline_file_path, 'r') as f:
        baseline_configs = json.load(f)

    if network_id not in baseline_configs:
        put_text("Baseline configuration for the selected network not found. Please create a baseline first.")
        return

    baseline_rules = baseline_configs[network_id]

    differences = [rule for rule in normalized_current_rules if rule not in baseline_rules] + \
                  [rule for rule in baseline_rules if rule not in normalized_current_rules]

    if differences:
        put_text("Differences found:")
        put_table([[json.dumps(diff, indent=2)] for diff in differences])
    else:
        put_text("No differences found.")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Function to Create L3 FW Baseline File
def create_baseline_file():
    """Create an empty baseline file in JSON format."""
    with open(baseline_file_path, 'w') as f:
        json.dump({}, f)
    put_text("Layer 3 Firewall Rule Baseline Database file created.")

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

#Function to get Pings from Meraki Devices
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

#Function to handle the get API requests Overview call
def get_api_requests_overview(api_key, org_id, t0, t1):
    url = f"{BASE_URL}/organizations/{org_id}/apiRequests/overview"
    headers = {
        "Content-Type": "application/json",
        "X-Cisco-Meraki-API-Key": api_key
    }
    params = {
        "t0": t0,
        "t1": t1
    }
    response = requests.get(url, headers=headers, params=params)
    return response

#Function to render the API Requests return data into a Pie Chart
def display_api_usage_pie_chart(data):
    if "responseCodeCounts" in data:
        response_code_counts = data["responseCodeCounts"]
        # Filter out response codes with a count of zero
        filtered_data = {code: count for code, count in response_code_counts.items() if count > 0}

        categories = list(filtered_data.keys())
        values = list(filtered_data.values())

        pie = (
            Pie()
            .add("", [list(z) for z in zip(categories, values)])
            .set_global_opts(title_opts=opts.TitleOpts(title="API Usage Overview"))
        )
        put_html(pie.render_notebook())
    else:
        put_error("No API usage data available.")

#Function to Get API Usage Overview then use Pyechart to create a Pie Chart
def api_usage_overview():
    clear()
    put_markdown("## API Usage Overview")
    put_markdown("##### The time range is defaulted to the last 30 days")
    t0_str = input("Enter the start date and time (YYYY-MM-DD HH:MM:SS):", type=TEXT, value=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'))
    t1_str = input("Enter the end date and time (YYYY-MM-DD HH:MM:SS):", type=TEXT, value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    clear()
    put_markdown("## API Usage Overview")
    # Convert the date and time strings to Unix timestamps
    t0 = int(datetime.strptime(t0_str, '%Y-%m-%d %H:%M:%S').timestamp())
    t1 = int(datetime.strptime(t1_str, '%Y-%m-%d %H:%M:%S').timestamp())

    # Call the API to get API requests overview
    response = get_api_requests_overview(api_key, org_id, t0, t1)
    if response.status_code == 200:
        data = response.json()
        display_api_usage_pie_chart(data)
    else:
        put_error(f"Failed to retrieve API usage overview. Status code: {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

#Function to get device events data
def get_device_events(api_key, org_id, t0, t1):
    url = f"{BASE_URL}/organizations/{org_id}/devices/availabilities/changeHistory"
    headers = {
        "Content-Type": "application/json",
        "X-Cisco-Meraki-API-Key": api_key
    }
    params = {
        "t0": t0,
        "t1": t1
    }
    response = requests.get(url, headers=headers, params=params)
    return response

#Function to create table out of device events data
def display_device_events(events):
    if events:
        table_data = [["Timestamp", "Device Serial", "Device Name", "Product Type", "Model", "Old Status", "New Status", "Network Name"]]
        for event in events:
            ts = event["ts"]
            device_serial = event["device"]["serial"]
            device_name = event["device"]["name"]
            product_type = event["device"]["productType"]
            model = event["device"]["model"]
            old_status = next((item["value"] for item in event["details"]["old"] if item["name"] == "status"), "N/A")
            new_status = next((item["value"] for item in event["details"]["new"] if item["name"] == "status"), "N/A")
            network_name = event["network"]["name"]
            table_data.append([ts, device_serial, device_name, product_type, model, old_status, new_status, network_name])

        put_table(table_data)
    else:
        put_error("No device events available.")

#Function to get Device events data
def device_events():
    clear()
    put_markdown("## Device Events")
    put_markdown("##### The time range is defaulted to the last 7 days")
    t0_str = input("Enter the start date and time (YYYY-MM-DD HH:MM:SS):", type=TEXT, value=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'))
    t1_str = input("Enter the end date and time (YYYY-MM-DD HH:MM:SS):", type=TEXT, value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    clear()
    put_markdown("## Device Events")
    # Convert the date and time strings to Unix timestamps
    t0 = int(datetime.strptime(t0_str, '%Y-%m-%d %H:%M:%S').timestamp())
    t1 = int(datetime.strptime(t1_str, '%Y-%m-%d %H:%M:%S').timestamp())

    # Call the API to get device events
    response = get_device_events(api_key, org_id, t0, t1)
    if response.status_code == 200:
        events = response.json()
        display_device_events(events)
    else:
        put_error(f"Failed to retrieve device events. Status code: {response.status_code}, Error: {response.text}")

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

#######################################################

#Function to GET Firmware Status
def get_firmware_status(api_key, org_id):
    url = f"{BASE_URL}/organizations/{org_id}/devices"
    headers = {
        "Content-Type": "application/json",
        "X-Cisco-Meraki-API-Key": api_key
    }
    response = requests.get(url, headers=headers)
    return response

#Function to render the firmware status data into a Pie Chart
def display_firmware_status_pie_chart(firmware_data):
    firmware_count = defaultdict(int)
    special_firmware_devices = []

    for device in firmware_data:
        if 'firmware' in device:
            firmware_version = device['firmware']
            firmware_count[firmware_version] += 1

            # Check for special firmware values
            if firmware_version in ["Not running configured version", "Firmware locked. Please contact support."]:
                special_firmware_devices.append(device)

    # Convert defaultdict to a regular dictionary
    firmware_count = dict(firmware_count)

    # Check if firmware_count is not empty
    if firmware_count:
        categories = list(firmware_count.keys())
        values = list(firmware_count.values())

        pie = (
            Pie()
            .add("", [list(z) for z in zip(categories, values)])
        )
        put_html(pie.render_notebook())
    else:
        put_error("No firmware data available.")

    # Display table for special firmware devices
    if special_firmware_devices:
        table_data = [["Name", "Serial", "Firmware", "Model", "Network ID"]]
        for device in special_firmware_devices:
            table_data.append([device.get('name', 'N/A'), device.get('serial', 'N/A'), device.get('firmware', 'N/A'), device.get('model', 'N/A'), device.get('networkId', 'N/A')])

        put_markdown("### Devices with Special Firmware Status")
        put_table(table_data)
    else:
        put_markdown("### No devices with special firmware status found.")

#Function to Get firmware Usage Overview then use Pyechart to create a Pie Chart
def firmware_status_overview():
    clear()
    put_markdown("## Firmware Status Overview")
    
    # Call the API to get firmware status overview
    response = get_firmware_status(api_key, org_id)
    if response.status_code == 200:
        firmware_data = response.json()
        display_firmware_status_pie_chart(firmware_data)
    else:
        put_error(f"Failed to retrieve firmare status overview. Status code: {response.status_code}, Error: {response.text}")

    put_buttons(["Back to Menu"], onclick=[main])

#######################################################

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
    put_markdown("<b> Create Functions </b>")
    put_buttons(["Create Network", "Create Dashboard Admin"], onclick=[create_network, create_dashboard_admin])
    put_markdown("<b> Get Functions </b>")
    put_buttons(["List Organizations", "List Networks", "Device Events"], onclick=[list_organizations, list_networks, device_events])
    put_markdown("<b> Delete Functions </b>")
    put_buttons(["Delete Network"], onclick=[delete_network])
    put_markdown("<b> Information Graph Functions </b>")
    put_buttons(["Get Wireless Network Stats", "Get Wireless Client Connection Stats", "API Usage Overview"], onclick=[get_wireless_network_stats, get_wireless_client_connection_stats, api_usage_overview])
    put_markdown("<b> Live Tools </b>")
    put_buttons(["Blink LED's", "Ping Tool", "Reboot Device"], onclick=[blink_led, ping_tool, reboot_device_tool])
    put_markdown("<b> Compare Tools </b>")
    put_buttons(["Get L3 FW Baseline", 'Compare Current L3 FW To Baseline', "Create Baseline DB File"], onclick=[get_baseline_configuration, compare_baseline_configuration, create_baseline_file])
    put_markdown("<b> Firmware </b>")
    put_buttons(["Device Firmware Status"], onclick=[firmware_status_overview])

# Start the PyWebIO server
if __name__ == '__main__':
    start_server(main, port=8999, debug=True)