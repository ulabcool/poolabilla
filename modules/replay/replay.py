import cv2
import copy
import time

# print(cv2.getBuildInformation())
# print cv2.__version__
# print help(cv2)

class Video:
    def __init__(self, video_source, video_buffer):
        self.buffer = video_buffer
        self.stream = cv2.VideoCapture(video_source)

    def is_streaming(self):
        return self.stream.isOpened()

    def get_frame(self):
        return self.stream.read()

    def get_framesize(self):
        return (int(self.stream.get(3)), int(self.stream.get(4)))

    def get_video_writer(self):
        return cv2.VideoWriter(self.generate_dump_path(), cv2.VideoWriter_fourcc('F', 'M', 'P', '4'), 20.0,
                               self.get_framesize())

    def generate_dump_path(self):
        return "/tmp/ulab/buffer-{}.mp4".format(time.strftime('%Y%m%d-%H%M%S'))

    def save_frame(self):
        self.buffer.append(frame)

        if len(self.buffer) > 30 * 5:  # 30 frames per second
            self.buffer.pop(0)

    def dump_buffer(self):
        out = self.get_video_writer()
        temp_buffer = copy.deepcopy(self.buffer)

        for bframe in temp_buffer:
            out.write(bframe)

        out.release()
        print "Done!"


# video = Video(0, list())
video = Video('rtmp://192.168.0.137/pool/stream', list())

while video.is_streaming():
    ret, frame = video.get_frame()

    video.save_frame()
    cv2.imshow('livefeed', frame)

    if cv2.waitKey(1) & 0xFF == ord('d'):
        video.dump_buffer()
        continue

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

print 'shutting down capturing.'
video.stream.release()
cv2.destroyAllWindows()
