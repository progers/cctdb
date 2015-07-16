#!/bin/bash

# Helper script for launching content shell, grabbing the renderer pid, and launching another
# command with -p [renderer pid]
#
# Usage:
# blink.sh [content_shell_and_args] [command_to_run_with_renderer_pid]
#
# Example:
# sudo scripts/blink.sh "/Users/pdr/Desktop/chromium/src/out/Debug/Content\ Shell.app/Contents/MacOS/Content\ Shell --renderer-startup-dialog --dump-render-tree about://blank" "./record.py -f 'blink::FrameView::layout()' -m 'libwebcore_shared.dylib' -o test.json"

echo "Starting blink renderer..."
echo "running [$1]"
eval $1 2>&1 | {
  while IFS= read -r line
  do
    echo "$line"

    # Match [19.....cc(131)] Renderer (1952) paused waiting for deb...
    if [[ $line =~ ^\[.+\][[:space:]]Renderer[[:space:]].([0-9]+).*$ ]] ; then
        pid="${BASH_REMATCH[1]}"
        command="$2 -p $pid &"
        echo "Found renderer pid ($pid). Running command [$command]"
        eval $command

        command="sleep 0.3 && kill -SIGUSR1 $pid"
        echo "Unpausing renderer by sending SIGUSR1 with command [$command]"
        eval $command

        wait
    fi
  done
}