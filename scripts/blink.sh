#!/bin/bash

# Helper script for launching content shell, grabbing the renderer pid, and launching another
# command with "RENDERERPID" replaced with the renderer pid
#
# Usage:
# blink.sh [content_shell_and_args] [command_to_run_with_renderer_pid]
#
# Example:
# ./scripts/blink.sh "/Users/pdr/Desktop/chromium/src/out/Release/Content\ Shell.app/Contents/MacOS/Content\ Shell --renderer-startup-dialog --run-layout-test a.html" "./record.py -f 'blink::LayoutSVGShape::layout()' -m 'libwebcore_shared.dylib' /Users/pdr/Desktop/chromium/src/out/Release/Content\ Shell.app/Contents/MacOS/Content\ Shell --pid=RENDERERPID > test.json"

echo "Starting blink renderer..."
echo "running [$1]"
eval $1 2>&1 | {
  while IFS= read -r line
  do
    echo "$line"

    # Match [19.....cc(131)] Renderer (1952) paused waiting for deb...
    if [[ $line =~ ^\[.+\][[:space:]]Renderer[[:space:]].([0-9]+).*$ ]] ; then
        pid="${BASH_REMATCH[1]}"
        command="${2/RENDERERPID/$pid}"
        echo "Found renderer pid ($pid). Running command [$command]"
        eval $command
    fi
  done
}