import config

from enum import Enum
from waapi import WaapiClient, CannotConnectToWaapiException
from xml.etree.ElementTree import Element, ElementTree
import os
import pathlib
import subprocess

def get_media_info_json_file(platform: Enum, paths: config.WwiseSourcesPaths):
    """Gets the current platform's Media Info JSON file defined in the config.py file"""
    return os.path.join(paths.SOUND_BANKS_DIR, f'{platform.value}', f'ExtSources_MediaInfo_{platform.value}.json')

def get_ext_source_cookie_ids(paths: config.WwiseSourcesPaths, use_wwise_console_waapi_server: bool = True):
    """Gets the name and short ID (cookie) of all external sources inputs found in the Wwise project.
    If the project is not open, a waapi server is created through the Wwise console """
    wwise_console_process = None
    console_created = False

    if use_wwise_console_waapi_server:
        wwise_console_process = subprocess.Popen(f"{paths.WWISE_CONSOLE_DIR} waapi-server {paths.WWISE_PROJ_FILE}")
        if wwise_console_process is None:
            return None
        console_created = True

    try:
        # Waapi client connection
        with WaapiClient(config.WAAPI_URL, config.WAAPI_ALLOW_EXCEPTIONS) as client:
            ext_sources = client.call("ak.wwise.core.object.get",
                                      {"waql": f"$ from type Sound select descendants where type = \"ExternalSource\""},
                                      options={"return": ["name", "shortId"]})["return"]
            wwise_console_process.kill() if console_created else None
            return ext_sources

    except CannotConnectToWaapiException:
        print("Could not connect to waapi, Wwise editor or Wwise Console. Ensure Wwise is running and waapi is enabled.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_audio_asset_list(folder_path):
    """Gets all the .wav files full path in the provided folder path"""
    audio_file_list = pathlib.Path(folder_path)
    return list(audio_file_list.rglob("*.wav"))  # Ignore all extensions other than .wav

def get_relative_asset_path(asset_path: pathlib.Path, start_dir_index: int = -4):
    """Extract the relative path of an asset"""
    part_list = asset_path.parts[start_dir_index:]
    if part_list:
        return "/".join(part_list)
    return ""

def get_clean_wem_destination(asset_path: pathlib.Path, start_dir_index: int = -2):
    """Extract the relative path of a .wav asset and replace it with .wem"""
    part_list = asset_path.parts[start_dir_index:]
    if part_list:
        return "/"[0].join(part_list).replace(".wav", ".wem")
    return ""

def get_wsources_xml_tree_and_source_destinations(paths: config.WwiseSourcesPaths):
    """Finds the current platform's .wsources file defined in the config.py file.
    Updates the file with the latest changes and gets the list of destinations"""

    wem_file_destination_list = []

    # Creates a new XML structure
    root = Element('ExternalSourcesList')
    root.set('SchemaVersion', '1')
    root.set('Root', '')

    # Add Source elements
    audio_asset_list = get_audio_asset_list(paths.ORIGINAL_VOICES_DIR)

    for asset in audio_asset_list:
        wav_file_origin: str = get_relative_asset_path(asset)
        wem_file_destination = get_clean_wem_destination(asset)

        # Create Source element
        source_element = Element('Source')
        source_element.set('Path', wav_file_origin)
        source_element.set('Conversion', paths.CONVERSION_SETTING_NAME)
        source_element.set('Destination', wem_file_destination)
        source_element.set('AnalysisTypes', '2')

        root.append(source_element)
        wem_file_destination_list.append(wem_file_destination)

    return ElementTree(root), wem_file_destination_list