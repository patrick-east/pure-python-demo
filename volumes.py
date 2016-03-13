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

def list_all(array, pending):
    """ List all volumes the FlashArray passed to us.

    Args:
        array (FlashArray): The target FlashArray where we retrieve the volume information.
        pending (bool): Whether or not to list volumes that are pending eradication.

    Returns:
        None
    """
    return array.list_volumes(pending=pending)

def create(array, vol_name, size):
    """ Create a new volume on the FlashArray passed to us.

    Args:
        array (FlashArray): The target FlashArray where we will create the volume.
        vol_name (str): The name of the volume to be created.
        size (str or int): The size of the volume to be created,
                           can be in format like '1024', '1G', '1.2T', etc.

    Returns:
        dict: A dictionary representation of the newly created volume object on the FlashArray.
    """
    return array.create_volume(vol_name, size=size)

def destroy(array, vol_name):
    """ Destroy a volume on the FlashArray passed to us.

    Args:
        array (FlashArray): The target FlashArray where we will destroy the volume.
        vol_name (str): The name of the volume to be destroyed.

    Returns:
        None
    """
    array.destroy_volume(vol_name)

def eradicate(array, vol_name):
    """ Eradicate a volume on the FlashArray passed to us.

    Args:
        array (FlashArray): The target FlashArray where we will eradicate the volume.
        vol_name (str): The name of the volume to be eradicated.

    Returns:
        None
    """
    array.eradicate_volume(vol_name)

def smarter_delete(array, vol_name):
    """ Clean up and then delete a volume object.

    This will destroy and eradicate the volume object, but only after clearing host connections.
    Any errors will also we supressed when possible.

    Args:
        array (FlashArray): The target FlashArray where we will destroy the volume.
        vol_name (str): The name of the volume to be destroyed.

    Returns:
        None
    """
    # Lets start by clearing any host connections this volume might have
    connected_hosts = array.list_volume_private_connections(vol_name)

    for host_info in connected_hosts:
        host_name = host_info["host"]
        try:
            array.disconnect_host(host_name, vol_name)
        except purestorage.PureHTTPError as err:
            if err.code == 400 and 'is not connected' in err.text:
                # Ignore this HTTP 400 error, since we are trying to disconnect the host
                # if it fails with an error message saying 'is not connected' we can
                # treat that as a success (the volume and host are no longer connected...somehow)
                pass
    
    # Now we can try and delete our volume
    try:
        array.destroy_volume(vol_name)
        array.eradicate_volume(vol_name)
    except purestorage.PureHTTPError as err:
            if err.code == 400 and 'does not exist' in err.text or 'has been destroyed' in err.text:
                # Ignore this HTTP 400 error. If the volume is already destroyed our work here is done.
                pass


def main(args):
    # The FlashArray object is the main entry point for the Python Rest Client. All interaction
    # With the array is done through these objects.
    array = purestorage.FlashArray(args.target, username=args.username, password=args.password)

    print('')
    if args.action == 'list':
        vols = list_all(array, args.pending)

        # We will just iterate through the volumes and print their info.
        for vol in vols:
            volume_name = vol['name']
            print('Details for volume "{name}"'.format(name=volume_name))
            pprint.pprint(vol)
            print('')
    elif args.action == 'create':
        print('Creating volume {name} with size {size}..'.format(name=args.name, size=args.size))

        vol = create(array, args.name, args.size)
        print('New volume:')
        pprint.pprint(vol)

    elif args.action == 'destroy':
        print('Destroying volume {name}...'.format(name=args.name))
        destroy(array, args.name)

    elif args.action == 'eradicate':
        print('Eradicating volume {name}...'.format(name=args.name))
        eradicate(array, args.name)

    elif args.action == 'smarter_delete':
        print('Clearing host connections and then destroying/eradicating volume {name}...'.format(name=args.name))
        smarter_delete(array, args.name)

    print('Done!')
    print('')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Generic arguments to connect to the array
    parser.add_argument('-t', '--target', help='Target FlashArray management IP or hostname.', required=True)
    parser.add_argument('-u', '--username', help='username for management access to FlashArray', required=True)
    parser.add_argument('-p', '--password', help='Password for management access to FlashArray.', required=True)
    
    # Add an action for what we want to do with volumes
    parser.add_argument('action', help='The action to run',
                        choices=['create', 'destroy', 'eradicate', 'smarter_delete', 'list'])

    # Some more specific options
    parser.add_argument('-n', '--name', help='Name of the volume to be operated on or created.'
                                             ' Required for create, destroy, and eradicate.')
    parser.add_argument('-s', '--size', help='Size of the volume to be created.')
    parser.add_argument('--pending', help='List volumes pending eradication.', action='store_true')

    args = parser.parse_args()
    main(args)
