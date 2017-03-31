import cv2
import sys
import time
import numpy as np
import librtmp
import scipy
import subprocess as sp

from pylibfreenect2 import Freenect2, SyncMultiFrameListener
from pylibfreenect2 import FrameType, Registration, Frame
from pylibfreenect2 import OpenCLPacketPipeline


#####################################################

pockets = False

def findPockets(img):
    img = img.copy()

    #  Get Black Parts
    lower = np.array([0, 0, 0])
    upper = np.array([25, 25, 25])
    shapeMask = cv2.inRange(img, lower, upper)

    # find the contours in the mask
    (contours, _) = cv2.findContours(shapeMask.copy(), cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_SIMPLE)

    pockets = []
    for c in contours:
        # draw the contour and show only when larger than 15
        # cv2.drawContours(img, [c], -1, (0, 255, 0), 2)
        (x, y), radius = cv2.minEnclosingCircle(c)
        center = (int(x), int(y))
        radius = int(radius)

        if radius > 25:
            pockets.append(center)

    print "Found {0} pockets".format(len(pockets))

    if len(pockets) != 6:
        return False

    return pockets


def calculateTableMatrix(img, pockets):
    points = calculateTableCoordinates(img, pockets)
    height, width, channels = img.shape
    dimensions = np.float32([[0, 0], [0, height], [width, 0], [width, height]])

    return cv2.getPerspectiveTransform(points, dimensions)


def calculateTableCoordinates(img, pockets):
    offset = 0
    max_x = max([x for (x, y) in pockets]) + offset
    max_y = max([y for (x, y) in pockets]) + offset
    min_x = min([x for (x, y) in pockets]) - offset
    min_y = min([y for (x, y) in pockets]) - offset

    return np.float32([[min_x, min_y], [min_x, max_y], [max_x, min_y], [max_x, max_y]])


def cropByPockets(img, pockets):
    matrix = calculateTableMatrix(img, pockets)

    return cv2.warpPerspective(img, matrix, (img.shape[1], img.shape[0])), matrix


def drawPockets(img, pockets):
    for pocket in pockets:
        cv2.circle(img, pocket, 30, (0, 255, 0), 2)


def drawCueBall(img, target, matrix):
    inv = cv2.invert(matrix)
    matrixInverted = np.asarray(inv[1][:,:])

    # get White
    lower = np.array([210, 210, 210])
    upper = np.array([255, 255, 255])
    shapeMask = cv2.inRange(img, lower, upper)

    # find the contours in the mask
    (cnts, _) = cv2.findContours(shapeMask.copy(), cv2.RETR_EXTERNAL,
                                 cv2.CHAIN_APPROX_SIMPLE)

    # loop over the contours
    for c in cnts:
        # draw the contour and show only when larger than 15
        # cv2.drawContours(img, [c], -1, (0, 255, 0), 2)
        (x, y), radius = cv2.minEnclosingCircle(c)
        center = np.array([int(x), int(y), 1])
        radius = int(radius)
        if 22 < radius < 25:
            translatedCenter = matrixInverted.dot(center)
            cv2.circle(target, (int(translatedCenter[0]), int(translatedCenter[1])), radius, (0, 0, 255), 2)


def processImage(frame):
    global pockets

    if not pockets:
        pockets = findPockets(frame)
        if not pockets:
            print "Wrong number of pockets, skipping frame"
            return

    drawPockets(frame, pockets)

    cropped, matrix = cropByPockets(frame, pockets)

    drawCueBall(cropped, frame, matrix)

# img = cv2.imread('pool2.png')


#####################################################


# fourcc = cv2.cv.CV_FOURCC(*'FLV1')
# outColor = cv2.VideoWriter('color.flv', fourcc, 15.0, (1920,1080))
# outDepth = cv2.VideoWriter('depth.flv', fourcc, 15.0, (512,424))
FFMPEG_BIN = "/usr/local/bin/ffmpeg"

RTMP_DEST = "rtmp://a.rtmp.youtube.com/live2"
STREAM_KEY = "wje8-swcd-srx0-22x3"

WIDTH = int(1920 / 1.5)
HEIGHT = int(1080 / 1.5)

command = [ FFMPEG_BIN,
        '-f', 'rawvideo',
        '-vcodec','rawvideo',
        '-s', '{}x{}'.format(WIDTH, HEIGHT), # size of one frame
        '-pix_fmt', 'bgr24',
        '-i', '-', # The input comes from a pipe
        '-f', 'lavfi',
        '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-vcodec', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'ultrafast',
        '-f', 'flv',
        RTMP_DEST + "/" + STREAM_KEY ]

#pipe = sp.Popen( command, stdin=sp.PIPE, stderr=sys.stderr, stdout=sys.stdout)

pipeline = OpenCLPacketPipeline()
fn = Freenect2()
num_devices = fn.enumerateDevices()
if num_devices == 0:
    print("No device connected!")
    sys.exit(1)
serial = fn.getDeviceSerialNumber(0)
device = fn.openDevice(serial, pipeline=pipeline)

types = FrameType.Color
listener = SyncMultiFrameListener(types)

device.setColorFrameListener(listener)
device.setIrAndDepthFrameListener(listener)

device.start()

# undistorted = Frame(512, 424, 4)
# registered = Frame(512, 424, 4)

start = time.time()

withDetection = False

# while time.time() < (start+5):
while True:
    frames = listener.waitForNewFrame()
    while listener.hasNewFrame():
        frames = listener.waitForNewFrame()

    color = frames["color"]
    depth = frames["depth"]


    colors = color.asarray()
    colors = cv2.cvtColor(colors, cv2.COLOR_RGBA2RGB)

    if withDetection:
        processImage(colors)

    colors = cv2.resize(colors, (WIDTH, HEIGHT))
    colors = cv2.flip(colors, 0)

    # depth8bit = ((numpy.clip(depth.asarray(), 1800, 2200)-1800)/400*256).astype("uint8")
    # outColor.write(colors)
    # outDepth.write(cv2.cvtColor(depth8bit, cv2.COLOR_GRAY2RGB))

    # colors = cv2.resize(colors, (1920/2, 1080/2))

    # pipe.stdin.write(colors.tostring())

    cv2.imshow("colors", colors)
    listener.release(frames)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    if key == ord('f'):
        withDetection = not withDetection

    if key == ord('p'):
        pockets = False


# pipe.stdin.close()
# pipe.kill()

# outColor.release()
# outDepth.release()
device.stop()
# device.close()



sys.exit(0)
