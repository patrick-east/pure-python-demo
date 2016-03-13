#!/usr/bin/env python

# Copyright (c) 2016 Pure Storage, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# For demo purposes we just turn off the HTTPS warnings.
# With real usage setting up the certificates for secure
# requests is highly recommended.
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

import argparse
import pprint

# Import the python rest-client in the python 3.x style
from purestorage import purestorage

# Re-using our modules
import array_info
import hosts
import volumes

Gi = 1024 ** 3

def pformat_in_needed(obj, indent=4):
    """ Helper method to pformat things only if they pass a truthy check"""
    if obj:
        formatted_string = pprint.pformat(obj, indent)
        indented_string = ''
        for line in formatted_string.split('\n'):
            indented_string = indented_string + '\n' + (' ' * indent * 2) + line
        return "\n{}\n".format(indented_string)


def main(args):
    # The FlashArray object is the main entry point for the Python Rest Client. All interaction
    # With the array is done through these objects.
    array = purestorage.FlashArray(args.target, username=args.username, password=args.password)

    # Some basic info...
    basic_info = array_info.basic_info(array)
    space_info = array_info.space_info(array)
    total_capacity = float(space_info["capacity"]) / Gi
    physical_used = float(space_info["total"]) / Gi

    vols = volumes.list_all(array, True)
    total_allocated = sum(item["size"] for item in vols) / Gi
    
    # See if phone home is enabled
    phonehome_info = array.get_phonehome()

    # Lets check messages and alerts on the array next
    open_messages = array.list_messages(open=True)
    flagged_messages = array.list_messages(flagged=True)

    # Lets look at the host connections and see if we have any that are not connected safetly
    all_hosts = hosts.list_with_connections(array)

    # Some categories we will look for
    unused_hosts = []
    disconnected_hosts = []
    redundant_connection_hosts = []
    non_redundant_connection_hosts = []
    at_risk_vols = []

    for host in all_hosts:
        # target_ports is a list of the ports on the FlashArray the host is currently connected with
        # vols is a list of the volumes connected to the host object in Puriy.
        if not host['target_port']:
            if not host['connections']:
                unused_hosts.append(host)
            else:
                disconnected_hosts.append(host)

        if host['target_port']:
            # Make sure it has at least one connection to each controller.
            ct0_connected = False
            ct1_connected = False
            for port in host['target_port']:
                if 'CT0' in port:
                    ct0_connected = True
                if 'CT1' in port:
                    ct1_connected = True

            if not ct0_connected or not ct1_connected:
                non_redundant_connection_hosts.append(host)
                at_risk_vols = at_risk_vols + host['connections']

    # Time to print out a report of all the info we've found
    report_Summary = '''
*******************************************************************************
**  Simple FlashArray Health Report
***********************************
Array Name:     {array_name}
Array ID:       {array_id}
Purity Version: {purity_version}

Current Usage:
    Total Capacity (GB):         {total_capacity}
    Total Used (GB physical):  {physical_used}
    Total Provisioned (GB):      {total_allocated}
    Data Reduction Rate:    {data_reduction}
    Total Reduction Rate:   {total_reduction}

Hosts:
    Number of hosts:                        {host_count}
    Hosts with redundant connections:       {redundant_connection_hosts_count}
    Hosts with no volumes:                  {unused_hosts}
    Disconnected Hosts:                     {disconnected_hosts}
    Hosts with non-redundant connections:   {non_redundant_connection_hosts}
    Volumes connections at risk:            {at_risk_vols}

Messages/Alerts:
    Flagged Message count:  {flagged_messages_count}
    Open Messages:          {open_messages}
    Phone Home:             {phonehome}

*******************************************************************************
'''
    print(report_Summary.format(
        array_name=basic_info['array_name'],
        array_id=basic_info['id'],
        purity_version=basic_info['version'],
        total_capacity=total_capacity,
        physical_used=physical_used,
        total_allocated=total_allocated,
        data_reduction=space_info['data_reduction'],
        total_reduction=space_info['total_reduction'],
        host_count=len(all_hosts),
        redundant_connection_hosts_count=len(redundant_connection_hosts),
        unused_hosts=pformat_in_needed(unused_hosts),
        disconnected_hosts=pformat_in_needed(disconnected_hosts),
        non_redundant_connection_hosts=pformat_in_needed(non_redundant_connection_hosts),
        at_risk_vols=pformat_in_needed(at_risk_vols),
        flagged_messages_count=len(flagged_messages),
        open_messages=pformat_in_needed(open_messages),
        phonehome=phonehome_info['phonehome']
    ))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Generic arguments to connect to the array
    parser.add_argument('-t', '--target', help='Target FlashArray management IP or hostname.', required=True)
    parser.add_argument('-u', '--username', help='username for management access to FlashArray', required=True)
    parser.add_argument('-p', '--password', help='Password for management access to FlashArray.', required=True)

    args = parser.parse_args()
    main(args)
