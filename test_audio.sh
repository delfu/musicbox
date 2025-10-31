#!/bin/bash
echo "Testing stereo audio output..."
echo "Left channel test (3 seconds)..."
speaker-test -t sine -f 440 -c 2 -s 1 -l 1
sleep 1
echo "Right channel test (3 seconds)..."
speaker-test -t sine -f 440 -c 2 -s 2 -l 1
sleep 1
echo "Both channels test (3 seconds)..."
speaker-test -t sine -f 440 -c 2 -l 1
echo "Audio test complete!"