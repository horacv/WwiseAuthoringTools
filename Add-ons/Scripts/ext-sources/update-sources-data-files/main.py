#============================================================================================================#
# Created by Horacio Valdivieso

# A Python utility for automating the generation of Wwise external sources configuration files.
# This utility also generates JSON configuration files compatible with the Unreal Engine - Wwise simple external source manager

# It requires these packages:

## py -m pip install waapi-client

# It's accessed by commands in this file:

## Add-ons/Commands/ext-sources/update-sources-data-files-commands.json
#============================================================================================================#

import config
import wwise_sources_parser as wparser

from xml.etree.ElementTree import indent
import asyncio
import json
import os

# HELPERS

def handle_py_asyncio_event_loop() -> asyncio.AbstractEventLoop:
    """Handle the asyncio event loop for Python versions 3.10 and below."""

    try: # For Python Pre 3.10
        loop = asyncio.get_event_loop()
    except RuntimeError: # For Python 3.10+
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

def create_ext_source_entry(index: int, ext_source: dict) -> dict:
    """Creates a formatted wwise external source entry for JSON serialization."""
    return {
        "Name": index + 1,
        "ExternalSourceCookie": ext_source["shortId"],
        "ExternalSourceName": ext_source["name"],
        "MediaInfoID": 1,
        "MediaName": ""
    }

def update_default_sources_info_json_file(paths: config.WwiseSourcesPaths):

    ext_source_info_list = []
    ext_source_info = wparser.get_ext_source_cookie_ids(paths)

    if ext_source_info is None:
        return

    for index, ext_source in enumerate(ext_source_info):
        ext_source_entry = create_ext_source_entry(index, ext_source)
        ext_source_info_list.append(ext_source_entry)

    formatted_json = json.dumps(ext_source_info_list, cls=config.WSourcesJSONEncoder)

    os.makedirs(os.path.dirname(paths.DEFAULT_SOURCES_INFO_FILE), exist_ok=True)
    with open(paths.DEFAULT_SOURCES_INFO_FILE, "w") as ext_source_info_json_file:
        ext_source_info_json_file.write(formatted_json)

def create_media_info_entry(index: int, destination: str, _platform: config.Platforms,
                             is_streamed: bool, use_device_memory: bool,
                             memory_alignment: int, prefetch_size: int) -> dict:
    """Create a media info entry dictionary for a .wav file destination."""
    return {
        "Name": index + 1,
        "ExternalSourceMediaInfoId": index + 1,
        "MediaName": destination,
        "CodecID": config.PLATFORM_CODECS[_platform].value,
        "bIsStreamed": is_streamed,
        "bUseDeviceMemory": use_device_memory,
        "MemoryAlignment": memory_alignment,
        "PrefetchSize": prefetch_size
    }

def update_ext_sources_data_files(paths: config.WwiseSourcesPaths, platform: config.Platforms,
                                  is_streamed: bool, use_device_memory: bool, memory_alignment: int, prefetch_size: int):
    """
    Updates Wwise external source data files for a specific platform.
    
    Generates two files:
    1. Platform-specific .wsources XML file containing source audio files
    2. Platform-specific media info JSON file containing metadata for each converted audio file
    
    The .wsources file is used by Wwise to convert .wav files to .wem format, while the media info
    JSON provides runtime configuration (codec, streaming settings, memory alignment, etc.) for the
    external sources in the game engine.
    """

    media_info_list = []
    xml_tree, destinations = wparser.get_wsources_xml_tree_and_source_destinations(paths)

    wsources_xml_file = os.path.join(paths.SOUND_BANKS_DIR, platform.value, f"ExternalSources_{platform.value}.wsources")
    os.makedirs(os.path.dirname(wsources_xml_file), exist_ok=True)

    with open(wsources_xml_file, 'w'):
        indent(xml_tree, space="    ")
        xml_tree.write(wsources_xml_file, encoding='UTF-8', xml_declaration=True)

    if destinations is None:
        return

    for index, destination in enumerate(destinations):
        media_info_entry = create_media_info_entry(index, destination, platform, is_streamed,
                                                   use_device_memory, memory_alignment, prefetch_size)
        media_info_list.append(media_info_entry)

    formatted_json = json.dumps(media_info_list, cls=config.WSourcesJSONEncoder)
    
    with open(wparser.get_media_info_json_file(platform, paths), "w") as media_info_json_file:
        media_info_json_file.write(formatted_json)


## MAIN PROCESS ##

if __name__ == "__main__":

    handle_py_asyncio_event_loop()
    
    config_paths = config.WwiseSourcesPaths()
    
    update_default_sources_info_json_file(config_paths)

    for config_platform in config.Platforms:
        update_ext_sources_data_files(config_paths, config_platform, config.IS_STREAMED,
                                      config.USE_DEVICE_MEMORY, config.MEMORY_ALIGNMENT, config.PREFETCH_SIZE)