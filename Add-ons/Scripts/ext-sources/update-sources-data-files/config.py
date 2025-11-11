from enum import Enum
import argparse
import json
import os

# CONFIG

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('--wproject_root', const=1, type=str, nargs='?')
    arg_parser.add_argument('--wproject_file', const=1, type=str, nargs='?')
    arg_parser.add_argument('--parser_script_dir', const=1, type=str, nargs='?')
    arg_parser.add_argument('--voices_dir', const=1, type=str, nargs='?')
    arg_parser.add_argument('--soundbanks_dir', const=1, type=str, nargs='?')
    arg_parser.add_argument('--default_sources_json_file', const=1, type=str, nargs='?')
    arg_parser.add_argument('--wconsole_dir', const=1, type=str, nargs='?')
    arg_parser.add_argument('--conversion_setting', const=1, type=str, nargs='?')

    return arg_parser.parse_args()

# ENUMS AND CONSTANTS

class Codecs(Enum):
    PCM = 1
    ADPCM = 2
    XMA = 3
    VORBIS = 4
    AT9 = 12
    OPUS_WEM = 20

class Platforms(Enum):
    WINDOWS = 'Windows'
    MAC = 'Mac'
    LINUX = 'Linux'
    ANDROID = 'Android'

PLATFORM_CODECS = {
    Platforms.WINDOWS: Codecs.PCM,
    Platforms.MAC: Codecs.ADPCM,
    Platforms.LINUX: Codecs.VORBIS,
    Platforms.ANDROID: Codecs.VORBIS
}

WAAPI_ALLOW_EXCEPTIONS : bool = True
WAAPI_URL : str = "ws://127.0.0.1:8080/waapi"

IS_STREAMED: bool = True
USE_DEVICE_MEMORY: bool = True
MEMORY_ALIGNMENT: int = 0
PREFETCH_SIZE: int = 32768 # 32 KB

# JSON Config
class WSourcesJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        json_str = super().encode(obj)

        # Perform custom formatting.
        # Make sure each JSON object uses one line to optimize the file's spacing
        formatted_str = json_str.replace('}, {', '},\n  {')
        formatted_str = formatted_str.replace('[{', '[\n  {')
        formatted_str = formatted_str.replace('}]', '}\n]')

        return formatted_str

class WwiseSourcesPaths:
    def __init__(self):
        
        self._args = parse_arguments()

        self.WWISE_PROJ_DIR = self._args.wproject_root
        self.WWISE_PROJ_FILE = self._args.wproject_file
        self.PARSER_SCRIPT_DIR = self._args.parser_script_dir
        self.ORIGINAL_VOICES_DIR = self._args.voices_dir
        self.SOUND_BANKS_DIR = self._args.soundbanks_dir
        self.DEFAULT_SOURCES_INFO_FILE = os.path.join(self.SOUND_BANKS_DIR, self._args.default_sources_json_file)
        self.WWISE_CONSOLE_DIR = self._args.wconsole_dir
        self.CONVERSION_SETTING_NAME = self._args.conversion_setting
