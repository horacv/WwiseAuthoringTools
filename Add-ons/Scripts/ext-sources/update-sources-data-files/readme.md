# Wwise External Sources Parser

A Python utility for automating the generation of Wwise external sources configuration files.\
This utility also generates JSON configuration files compatible with the Unreal Engine - Wwise simple external source manager:

https://www.audiokinetic.com/en/public-library/2024.1.9_8920/?source=UE4&id=using_features_simpleexternalsourcemanager.html

This tool scans audio files, creates platform-specific `.wsources` XML files for Wwise conversion, and media info JSON files for runtime configuration.

The main purpose of using external sources in your game is to handle localized VO lines that can be loaded dynamically at runtime.
I understand that each project VO pipeline and workflow is different, so this tool is designed to be extensible and customizable. 

## Overview

This utility automates the workflow of managing external sources in Wwise by:
- Scanning a directory for `.wav` audio files (`Original/Voices` by default)
- Generating `.wsources` XML files for each platform (Windows, Mac, Linux, Android, etc...) with the correct formatting
- Creating platform-specific media info JSON files with codec and streaming settings
- Extracting external source cookie IDs from the Wwise project via WAAPI

## Usage

- Edit `config.py` to customize settings
- Click on `Wwise Tools > External Sources > Update Sources Data Files (XML-JSON)` in the Wwise menu bar
- It's accessed by a command in this file:
`Add-ons/Commands/ext-sources/update-sources-data-files-commands.json`

## Command Line Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `--wproject_root` | Root directory of the Wwise project | Yes |
| `--wproject_file` | Full path to the `.wproj` file | Yes |
| `--parser_script_dir` | Directory containing the parser scripts | Yes |
| `--voices_dir` | Directory containing source `.wav` files | Yes |
| `--soundbanks_dir` | Output directory for generated sound banks | Yes |
| `--default_sources_json_file` | Name of the default sources JSON file | Yes |
| `--wconsole_dir` | Full path to `WwiseConsole.exe` | Yes |
| `--conversion_setting` | Name of the Wwise conversion setting to use | Yes |

## Known Limitations

The parser can't process arguments that have whitespace in them. For instance:

Use: `MyWwiseProject.wproj` ✅
instead of: `My Wwise Project.wproj` ❌



