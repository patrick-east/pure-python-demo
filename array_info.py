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


def basic_info(array):
    """ Get basic information about the FlashArray

    Args:
        array (FlashArray): The target FlashArray where we retrieve the information.

    Returns:
        dict: Basic information about the array including name, id, Purity version, and more.
    """
    return array.get()

def space_info(array):
    """ Get space and capacity information about the FlashArray

    Args:
        array (FlashArray): The target FlashArray where we retrieve the information.

    Returns:
        dict: Space information about the array showing serveral different metrics.
    """
    return array.get(space=True)

def main(args):
    # The FlashArray object is the main entry point for the Python Rest Client. All interaction
    # With the array is done through these objects.
    array = purestorage.FlashArray(args.target, username=args.username, password=args.password)

    # Run through all of our modules methods
    basic_info = basic_info(array)
    space_info = space_info(array)

    print('')
    print('Basic info (raw):')
    pprint.pprint(basic_info)
    print('')
    print('Space info (raw):')
    pprint.pprint(space_info)
    print('')
    print('Done!')
    print('')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Generic arguments to connect to the array
    parser.add_argument('-t', '--target', help='Target FlashArray management IP or hostname.', required=True)
    parser.add_argument('-u', '--username', help='username for management access to FlashArray', required=True)
    parser.add_argument('-p', '--password', help='Password for management access to FlashArray.', required=True)

    args = parser.parse_args()
    main(args)
