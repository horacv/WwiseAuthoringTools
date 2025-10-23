#!/bin/bash
echo "Installing Python packages..."

py -m pip install waapi-client
py -m pip install scipy

echo "All packages installed successfully!"