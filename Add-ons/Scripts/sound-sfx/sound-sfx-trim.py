#============================================================================================================#
# Modified and adapted by Horacio Valdivieso

# This script is based on a Bernard Rodrigue waapi Script: https://github.com/ak-brodrigue/waapi-python-tools
# It batch processes Sound SFX objects by trimming their heads and tails based on an amplitude threshold value
# Very useful for audio files imported with a lot of silence at the beginning and end

# It requires these packages:

## py -m pip install waapi-client
## py -m pip install scipy

# It's accessed by commands in this file:

## Add-ons/Commands/sound-sfx/sound-sfx-trim-cmds.json

#============================================================================================================#

from dataclasses import dataclass
from scipy.io import wavfile
from waapi import WaapiClient, CannotConnectToWaapiException
import argparse
import asyncio
import numpy as np

# CONSTANTS

MAX_INT32 = 2147483647
MAX_INT16 = 32767
DECIBEL_TO_LINEAR_MULTIPLIER = 0.05
DEFAULT_FADE_DURATION = 0.004
DEFAULT_THRESHOLD_DB = -54

# CONFIG

@dataclass
class ProcessingConfig:
    """Configuration for audio file processing."""
    reset_preprocess: bool
    reset_all: bool
    threshold_begin_linear: float
    threshold_end_linear: float
    no_trim_begin: bool
    no_trim_end: bool
    fade_begin: float
    fade_end: float
    initial_delay: bool

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Automatically trim Audio File Sources inside a selected Wwise object.'
    )
    parser.add_argument('--reset_preprocess', const=1, default=False, type=bool, nargs='?',
                        help='Reset all the trim and fade properties before processing the audio files')
    parser.add_argument('--reset_all', const=1, default=False, type=bool, nargs='?',
                        help='Reset all the trim and fade properties on the selected objects\' audio files')
    parser.add_argument('--threshold_begin', const=1, default=DEFAULT_THRESHOLD_DB, type=int, nargs='?',
                        help='Threshold in decibels under which the begin is trimmed.')
    parser.add_argument('--threshold_end', const=1, default=DEFAULT_THRESHOLD_DB, type=int, nargs='?',
                        help='Threshold in decibels under which the end is trimmed.')
    parser.add_argument('--no_trim_begin', const=1, default=False, type=bool, nargs='?',
                        help='Trim the begin of the sources')
    parser.add_argument('--no_trim_end', const=1, default=False, type=bool, nargs='?',
                        help='Trim the end of the sources')
    parser.add_argument('--fade_begin', const=0, default=DEFAULT_FADE_DURATION, type=float, nargs='?',
                        help='Fade duration when trimming begin')
    parser.add_argument('--fade_end', const=0, default=DEFAULT_FADE_DURATION, type=float, nargs='?',
                        help='Fade duration when trimming end')
    parser.add_argument('--initial_delay', const=1, default=False, type=bool, nargs='?',
                        help='Trimming applied on the begin with be compensated by initial delay')
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

# Convert the threshold value from decibels to linear
# dB to linear = 10^(db/20) or 10^(db*(1/20)) or 10^(db*0.05)
get_threshold_value_linear = lambda db: pow(10, db * DECIBEL_TO_LINEAR_MULTIPLIER)

def convert_sample_value_to_float(sample, data_type_name : str) -> float:
    """Convert the raw data to a single float value.
    A multichannel file will have an array of sample values, if this is the case, the highest value is selected"""
    conversion_map = {
        "int16" : MAX_INT16,
        "int32" : MAX_INT32,
        "float32" : 1,
    }

    divisor : int = conversion_map[data_type_name]
    sample_array = np.asarray(sample)

    if sample_array.ndim == 0 or sample_array.shape[0] == 1:
        # Mono: Single-element array
        return float(sample_array) / divisor
    else:
        # Multi-channel: return max value
        return sample_array.max() / divisor


def find_trim_sample(audio_data: np.ndarray, start_index: int,
                     end_index: int, threshold_linear: float, reverse: bool = False) -> int:
    """Traverse the audio data from the start index to the end index and find the first sample above the DB threshold."""

    last_sample_value = 0
    last_zero_crossing_sample = start_index

    for i in range(start_index, end_index, -1 if reverse else 1):  # Find the trim begin sample
        current_sample_value = convert_sample_value_to_float(audio_data[i], audio_data.dtype.name)

        # Store zero crossing sample
        if (current_sample_value > 0 >= last_sample_value) or (
                current_sample_value < 0 <= last_sample_value):
            last_zero_crossing_sample = i

        # Detect volume threshold
        if abs(current_sample_value) > threshold_linear:
            break

        last_sample_value = current_sample_value

    return last_zero_crossing_sample


# MAIN PROCESS

def main():

    handle_py_asyncio_event_loop()

    try:
        # Waapi client connection
        with (WaapiClient() as client):

            command_args = parse_arguments()
            config = ProcessingConfig(
                reset_preprocess=command_args.reset_preprocess,
                reset_all=command_args.reset_all,
                threshold_begin_linear=get_threshold_value_linear(command_args.threshold_begin),
                threshold_end_linear=get_threshold_value_linear(command_args.threshold_end),
                no_trim_begin=command_args.no_trim_begin,
                no_trim_end=command_args.no_trim_end,
                fade_begin=command_args.fade_begin,
                fade_end=command_args.fade_end,
                initial_delay=command_args.initial_delay
            )

            # Get objects selected in the authoring tool
            selected_objects = client.call("ak.wwise.ui.getSelectedObjects")["objects"]

            # To hold all changed files
            processed_objects = {"objects": []}

            for objects in selected_objects:

                # Use waql to get all the child audio sources under the selected objects
                audio_files = client.call("ak.wwise.core.object.get",
                                          {
                                              "waql": f"$ \"{objects['id']}\" select descendants where type = \"AudioFileSource\""},
                                          options={"return": ["originalWavFilePath", "type", "id", "parent.id"]}
                                          )["return"]

                for audio_file in audio_files:

                    # Get a pointer to the objects to process
                    audio_file_source = {"object": audio_file['id']}
                    parent_sound_object = {"object": audio_file['parent.id']}

                    # Open the WAV file using the scipy library and read its data
                    sample_rate, audio_data = wavfile.read(audio_file['originalWavFilePath'])

                    # Set initial data before processing the file
                    # If data.shape[1] is valid, it means that it is at least a two-channel file, if not Mono
                    num_samples: int = audio_data.shape[0]
                    begin_sample: int = 0
                    end_sample: int = num_samples - 1
                    duration_in_seconds: float = num_samples / sample_rate

                    # Reset first if a reset argument was provided!
                    # Wwise Object Reference:
                    # https://www.audiokinetic.com/en/public-library/2024.1.9_8920/?source=SDK&id=wwiseobject_audiofilesource.html
                    if config.reset_preprocess or config.reset_all:
                        audio_file_source["@TrimBegin"] = 0
                        audio_file_source["@TrimEnd"] = duration_in_seconds
                        audio_file_source["@FadeInDuration"] = 0
                        audio_file_source["@FadeOutDuration"] = 0
                        audio_file_source["@LoopBegin"] = -0.001
                        audio_file_source["@LoopEnd"] = -0.001
                        parent_sound_object["@InitialDelay"] = 0

                    if not config.reset_all:

                        trim_begin_sample: int = find_trim_sample(audio_data, begin_sample, end_sample, config.threshold_begin_linear)
                        trim_end_sample: int = find_trim_sample(audio_data, end_sample, begin_sample, config.threshold_end_linear, reverse=True)

                        # Set the trim and fade properties in the source object
                        if (not config.no_trim_begin) and trim_begin_sample > begin_sample:
                            audio_file_source["@TrimBegin"] = trim_begin_sample / sample_rate

                        if (not config.no_trim_end) and trim_end_sample < end_sample:
                            audio_file_source["@TrimEnd"] = trim_end_sample / sample_rate

                        audio_file_source["@FadeInDuration"] = config.fade_begin
                        audio_file_source["@FadeOutDuration"] = config.fade_end

                        if config.initial_delay:
                            parent_sound_object["@InitialDelay"] = trim_begin_sample / sample_rate

                    # Store changes
                    processed_objects["objects"].append(audio_file_source)
                    processed_objects["objects"].append(parent_sound_object)

            # Make sure to create and Undo Group before commiting
            client.call("ak.wwise.core.undo.beginGroup")
            client.call("ak.wwise.core.object.set", processed_objects)
            client.call("ak.wwise.core.undo.endGroup", {'displayName': 'Trim Audio File Sources'})


    except CannotConnectToWaapiException:
        print("Could not connect to waapi. Ensure Wwise is running and waapi is enabled.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()