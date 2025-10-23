#============================================================================================================#
# Created by Horacio Valdivieso

# This script finds all selected objects, optionally including its descendants;
# then resets their voice volumes to 0 (unity), optionally compensating for the change with makeup gain.
# If compensation with makeup gain is applied, The final output volume should be identical to the state previous to this change
# It can only reset makeup gain as well.

# It requires these packages:

## py -m pip install waapi-client

# It's accessed by commands in this file:

## Add-ons/Commands/volume/volume-reset-voice-volume-cmds.json
#============================================================================================================#

from waapi import WaapiClient, CannotConnectToWaapiException
import argparse
import asyncio

# CONSTANTS

MAKEUP_GAIN_MIN : int = -96
MAKEUP_GAIN_MAX : int = 96

# CONFIG

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Reset Voice Volumes for selected objects, optionally compensating with make-up gain.'
    )
    parser.add_argument('--reset_makeup_gain_only', const=1, default=False, type=bool, nargs='?'
                        , help='If true, only make-up gain will reset')
    parser.add_argument('--compensate_with_gain', const=1, default=False, type=bool, nargs='?'
                        , help='If true, the volume change will be compensated with gain')
    parser.add_argument('--include_all_descendants', const=1, default=False, type=bool, nargs='?'
                        , help='If true, then all descendants of the selected objects will be included in the query')
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


# MAIN PROCESS

def main():

    handle_py_asyncio_event_loop()

    try:
        # Waapi client connection
        with WaapiClient() as client:

            config = parse_arguments()

            # Get objects selected in the authoring tool
            selected_objects = client.call("ak.wwise.ui.getSelectedObjects")["objects"]
            # Create a dictionary (map) to hold the modified objects
            compensated_objects = {"objects": []}
            # Makeup gain or Voice Volume
            property_to_check = "@MakeUpGain" if config.reset_makeup_gain_only else "@Volume"

            for obj in selected_objects:

                if config.include_all_descendants:
                    # Get all objects that have their voice volume or makeup gain different from zero
                    objects_to_compensate = client.call("ak.wwise.core.object.get",
                                                        {
                                                            "waql": f"$ \"{obj['id']}\" select descendants, this where {property_to_check} != 0"},
                                                        options={"return": ["id", "Volume", "type", "MakeUpGain"]})["return"]
                else:
                    # Get only selected objects
                    objects_to_compensate = client.call("ak.wwise.core.object.get",
                                                        {
                                                            "waql": f"$ \"{obj['id']}\" select this where {property_to_check} != 0"},
                                                        options={"return": ["id", "Volume", "type", "MakeUpGain"]})["return"]

                # Process each found object
                for obj_to_compensate in objects_to_compensate:

                    if config.reset_makeup_gain_only:
                        # Reset Makeup gain to 0
                        compensated_object = {"object": obj_to_compensate['id'], "@MakeUpGain": 0}

                    else:
                        if config.compensate_with_gain:
                            # Set their voice volume to 0 and add the difference on their makeup gain
                            volume_plus_gain = obj_to_compensate["MakeUpGain"] + obj_to_compensate["Volume"]
                            # Make sure the new makeup gain does not go out of range
                            new_make_up_gain = max(MAKEUP_GAIN_MIN, min(volume_plus_gain, MAKEUP_GAIN_MAX))
                            # Set the new makeup gain and reset the voice volume
                            compensated_object = {"object": obj_to_compensate['id'],
                                                  "@Volume": 0,
                                                  "@MakeUpGain": new_make_up_gain}
                        else:
                            # Only reset the voice volume
                            compensated_object = {"object": obj_to_compensate['id'], "@Volume": 0}

                    # Finally, add the new compensated object to the dictionary
                    compensated_objects["objects"].append(compensated_object)

            # Make sure to create and undo group before commiting
            client.call("ak.wwise.core.undo.beginGroup")
            client.call("ak.wwise.core.object.set", compensated_objects)
            client.call("ak.wwise.core.undo.endGroup", {'displayName': 'Compensate Voice Volumes'})


    except CannotConnectToWaapiException:
        print("Could not connect to waapi. Ensure Wwise is running and waapi is enabled.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
