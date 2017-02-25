import cv2
import numpy as np

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
    lower = np.array([220, 220, 220])
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
            cv2.circle(target, (int(translatedCenter[0]), int(translatedCenter[1])), 16, (0, 0, 255), 2)


def processImage(frame):
    global pockets

    if not pockets:
        pockets = findPockets(frame)
        if not pockets:
            print "Wrong number of pockets, skipping frame"
            return

    drawPockets(frame, pockets)

    cropped, matrix = cropByPockets(frame, pockets)
    # cv2.imshow('cropped', cropped)

    drawCueBall(cropped, frame, matrix)

# img = cv2.imread('pool2.png')

video = cv2.VideoCapture('../../example_sources/color.mp4')

while video.isOpened():
    ret, frame = video.read()

    processImage(frame)

    cv2.imshow('frame', frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

video.release()

k = cv2.waitKey(0)
if k == 27:
    cv2.destroyAllWindows()
