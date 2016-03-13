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

def create(array, name, iqnlist, wwnlist):
    array.create_host(name, iqnlist=iqnlist, wwnlist=wwnlist)

def delete(array, name):
    array.delete_host(name)

def connect_host_with_volume(array, host_name, volume_name):
    array.connect_host(host_name, volume_name)

def list_with_connections(array):
    # Start by getting the list of hosts.
    all_hosts = array.list_hosts()

    # This call only returns hosts with volume connections.
    all_host_connections = array.list_hosts(all=True)

    # This list contains duplicate entries, one per volume connection,
    # so we need to compress this info a little bit.
    hosts = dict()

    for host in all_hosts:
        hostname = host['name']
        hosts[hostname] = host
        hosts[hostname]['connections'] = []
        hosts[hostname]['target_port'] = []

    for host in all_host_connections:
        hostname = host['name']
        hosts[hostname]['connections'].append({
            'vol': host['vol'],
            'lun': host['lun'],
            'host': host['name']
        })
        hosts[hostname]['target_port'] = host['target_port']

    return list(hosts.values())

def main(args):
    # The FlashArray object is the main entry point for the Python Rest Client. All interaction
    # With the array is done through these objects.
    array = purestorage.FlashArray(args.target, username=args.username, password=args.password)

    print('')
    if args.action == 'list':
        hosts = list_with_connections(array)

        # We will just iterate through the hosts and print their info.
        for host in hosts:
            host_name = host['name']
            print('Details for host "{name}"'.format(name=host_name))
            pprint.pprint(host)
            print('')
    elif args.action == 'create':
        iqnlist = [] if args.iqnlist is None else args.iqnlist
        wwnlist = [] if args.wwnlist is None else args.wwnlist
        print('Creating host {name} with iqnlist {iqnlist} and wwnlist {wwnlist}..'.format(name=args.name,
                                                                                            iqnlist=iqnlist,
                                                                                            wwnlist=wwnlist))
        host = create(array, args.name, iqnlist, wwnlist)
        print('New host:')
        pprint.pprint(host)

    elif args.action == 'delete':
        print('Deleting host {name}...'.format(name=args.name))
        delete(array, args.name)

    elif args.action == 'connect':
        print('Connecting host {name} to volume {vol}...'.format(name=args.name, vol=args.vol_name))
        connect_host_with_volume(array, args.name, args.vol_name)

    print('Done!')
    print('')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Generic arguments to connect to the array
    parser.add_argument('-t', '--target', help='Target FlashArray management IP or hostname.', required=True)
    parser.add_argument('-u', '--username', help='username for management access to FlashArray', required=True)
    parser.add_argument('-p', '--password', help='Password for management access to FlashArray.', required=True)

    # Add an action for what we want to do with hosts
    parser.add_argument('action', help='The action to run', choices=['create', 'delete', 'list', 'connect'])

    # Some more specific options
    parser.add_argument('-n', '--name', help='Name of the host to be operated on or created.')
    parser.add_argument('-i', '--iqnlist', nargs='*', help='iSCSI IQN to associate with the host being created.')
    parser.add_argument('-w', '--wwnlist', nargs='*', help='FC WWN to associate with the host being created.')
    parser.add_argument('-v', '--vol_name', help='Name of the volume to attach to the host.')

    args = parser.parse_args()
    main(args)
