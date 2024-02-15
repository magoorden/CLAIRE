#!/usr/bin/env bash

# Define file names.
waterLevelFile="WaterLevel_in_mm.txt"
rainfallNowcastFileLocal="RainfallNowcast.txt"
pathSSHKey=""

while [ true ] ; do inotifywait -e modify file.txt && scp -i $pathSSHKey $waterLevelFile ubuntu@:~/ ; done