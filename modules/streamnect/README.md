# Streamnect

Takes a connected Kinect and streams it to a server via RTMP.

## Improvements

- De-hardcode the stream destination
- Use FFMPEG library instead of piping to the command line

## Building / Running

```
mkdir build
cd build
cmake ..
make
./streamnect
```
