#include <iostream>
#include <fstream>
#include <cstdlib>
#include <libfreenect2/libfreenect2.hpp>
#include <libfreenect2/frame_listener_impl.h>
#include <libfreenect2/registration.h>
#include <libfreenect2/packet_pipeline.h>
#include <libfreenect2/logger.h>
#include <zconf.h>

class MyFileLogger: public libfreenect2::Logger
{
private:
    std::ofstream logfile_;
public:
    MyFileLogger(const char *filename)
    {
        if (filename)
            logfile_.open(filename);
        level_ = Debug;
    }
    bool good()
    {
        return logfile_.is_open() && logfile_.good();
    }
    virtual void log(Level level, const std::string &message)
    {
        logfile_ << "[" << libfreenect2::Logger::level2str(level) << "] " << message << std::endl;
    }
};

int childPipe() {
    int fd[2];

    if(pipe(fd) == -1) {
        std::cout << "ERROR!" << std::endl;
        return -1;
    }

    pid_t pid = fork();

    if(pid < 0) {
        std::cout << "FORK ERROR!" << std::endl;
        return -1;
    }

    if(pid == 0) {
        close(0);
        dup2(fd[0], 0);
        close(fd[1]);
        execlp("/usr/local/bin/ffmpeg", "ffmpeg", "-f", "rawvideo", "-vcodec", "rawvideo", "-framerate", "29","-s", "1920x1080", "-pix_fmt", "bgra", "-i", "-", "-s", "1280x720","-vf", "vflip", "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-f", "flv", "-preset", "ultrafast", "rtmp://192.168.0.137/pool/stream", NULL);
        return 0;
    }

    std::cout << pid << std::endl;

    close(fd[0]);
    return fd[1];
}

int main() {
    MyFileLogger *filelogger = new MyFileLogger("streamnect.log");
    if(filelogger->good()) {
        libfreenect2::setGlobalLogger(filelogger);
    } else {
        delete filelogger;
    }

    int fd = childPipe();

    libfreenect2::Freenect2 freenect2;
    libfreenect2::Freenect2Device *dev = 0;
    libfreenect2::PacketPipeline *pipeline = 0;

    if(freenect2.enumerateDevices() == 0)
    {
        std::cout << "no device connected!" << std::endl;
        return -1;
    }

    std::string serial = freenect2.getDefaultDeviceSerialNumber();

    pipeline = new libfreenect2::OpenGLPacketPipeline();

    dev = freenect2.openDevice(serial, pipeline);

    int types = libfreenect2::Frame::Color;
    libfreenect2::SyncMultiFrameListener listener(types);
    libfreenect2::FrameMap frames;

    dev->setColorFrameListener(&listener);
    dev->setIrAndDepthFrameListener(&listener);

    if(!dev->startStreams(true, false)) return -1;

    std::cout << "device serial: " << dev->getSerialNumber() << std::endl;
    std::cout << "device firmware: " << dev->getFirmwareVersion() << std::endl;

    while(true) {
        if (!listener.waitForNewFrame(frames, 10*1000)) {
            std::cout << "timeout!" << std::endl;
            return -1;
        }

        libfreenect2::Frame *rgb = frames[libfreenect2::Frame::Color];

        write(fd, rgb->data, rgb->bytes_per_pixel * rgb->width * rgb->height);

        listener.release(frames);
    }

    dev->stop();
    dev->close();

    return 0;
}
