#============================================================================================================#
# Created by Horacio Valdivieso

# This script opens the list view and searches the name of the selected object by using a waql query.
# It shows all the selected object descendants of a specific type.
# The type to find is defined as an argument on the calling command

# It requires these packages:

## py -m pip install waapi-client

# It's accessed by commands in this file:

## Add-ons/Commands/list-view/list-view-show-descendants-of-type.json
#============================================================================================================#

from waapi import WaapiClient, CannotConnectToWaapiException
import argparse
import asyncio

# CONSTANTS

WAAPI_ALLOW_EXCEPTIONS : bool = True
WAAPI_URL : str = "ws://127.0.0.1:8080/waapi"

# CONFIG

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Show descendants of type in the list view.')
    parser.add_argument('--type', const=1, default='Sound', type=str, nargs='?'
                        , help='Show descendants of type in the list view ex. --type Sound, --type ActorMixer')
    parser.add_argument('--additional-option', const=1, default='', type=str, nargs='?'
                        , help='')
    parser.add_argument('--additional-option-value', const=1, default='0', type=str, nargs='?'
                        , help='')
    return parser.parse_args()

# HELPERS

def handle_py_asyncio_event_loop() -> asyncio.AbstractEventLoop:
    """Handle the asyncio event loop for Python versions 3.10 and below."""

    try: # For Python Pre 3.10
        loop = asyncio.get_event_loop()
    except RuntimeError: # For Python 3.10+
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

def main():

    handle_py_asyncio_event_loop()

    try:
        # Waapi client connection
        with WaapiClient(WAAPI_URL, WAAPI_ALLOW_EXCEPTIONS) as client:

            config = parse_arguments()

            # Get objects selected in the authoring tool. Only selects the first element
            selected_object = client.call("ak.wwise.ui.getSelectedObjects",
                                          options={"return": ["path"]})["objects"][0]

            if selected_object:
                waql_query = (f"$ \"{selected_object["path"]}\" select descendants where type = \"{config.type}\""
                              if config.additional_option == '' else
                              f"$ \"{selected_object["path"]}\" select descendants where type = \"{config.type}\" where {config.additional_option} = {config.additional_option_value}")
                client.call("ak.wwise.ui.commands.execute",
                            {"command": "ShowListView", "value": waql_query})

    except CannotConnectToWaapiException:
        print("Could not connect to waapi. Ensure Wwise is running and waapi is enabled.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()