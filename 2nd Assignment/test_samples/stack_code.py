import cv2
import numpy as np

debug = True


# Display image
def display(input_image, frame_name="OpenCV Image"):
    if not debug:
        return
    h, w = input_image.shape[0:2]
    new_w = 800
    new_h = int(new_w * (h / w))
    input_image = cv2.resize(input_image, (new_w, new_h))
    cv2.imshow(frame_name, input_image)
    cv2.waitKey(0)


# rotate the image with given theta value
def rotate(input_image, theta):
    """
    Rotate the image with given theta value
    :param input_image: the given image
    :param theta: calculated from the slope function
    :return: the rotated image
    """
    rows, cols = input_image.shape[0], input_image.shape[1]
    image_center = (cols / 2, rows / 2)

    M = cv2.getRotationMatrix2D(image_center, theta, 1)

    abs_cos = abs(M[0, 0])
    abs_sin = abs(M[0, 1])

    bound_w = int(rows * abs_sin + cols * abs_cos)
    bound_h = int(rows * abs_cos + cols * abs_sin)

    M[0, 2] += bound_w / 2 - image_center[0]
    M[1, 2] += bound_h / 2 - image_center[1]

    # rotate original image to show transformation
    rotated = cv2.warpAffine(input_image, M, (bound_w, bound_h), borderValue=(255, 255, 255))
    return rotated


def slope(x1, y1, x2, y2):
    """
    Calculate the slope of the line
    :param x1, y1, x2, y2: the coordinates of the line
    :return: theta: calculated from the slope
    """
    if x1 == x2:
        return 0
    slope = (y2 - y1) / (x2 - x1)
    theta = np.rad2deg(np.arctan(slope))
    return theta

def preprocess(input_image):
    """
    Preprocess the image to get the text regions
    :param input_image: the given image
    :return: connected_image the image with connected text regions
    bw_image: the binarized image
    """
    small = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    # find the gradient map
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    grad = cv2.morphologyEx(small, cv2.MORPH_GRADIENT, kernel)

    display(grad)

    # Binarize the gradient image
    _, bw_image = cv2.threshold(grad, 0.0, 255.0, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    display(bw_image)

    # connect horizontally oriented regions
    # kernel value (9,1) can be changed to improve the text detection
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
    connected_image = cv2.morphologyEx(bw_image, cv2.MORPH_CLOSE, kernel)
    display(connected_image)

    return connected_image, bw_image

def find_contours(connected_image, bw_image, textImg):
    """
    Find the contours in the image
    :param connected_image: the image with connected text regions
    :param bw_image: the binarized image
    :param textImg: the image with detected text regions
    :return: the contours
    """
    contours, hierarchy = cv2.findContours(connected_image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    mask = np.zeros(bw_image.shape, dtype=np.uint8)

    # cumulative theta value
    cummTheta = 0
    # number of detected text regions
    ct = 0
    for idx in range(len(contours)):
        x, y, w, h = cv2.boundingRect(contours[idx])
        mask[y:y + h, x:x + w] = 0
        # fill the contour
        cv2.drawContours(mask, contours, idx, (255, 255, 255), -1)
        # ratio of non-zero pixels in the filled region
        r = float(cv2.countNonZero(mask[y:y + h, x:x + w])) / (w * h)

        # assume at least 45% of the area is filled if it contains text
        if r > 0.45 and w > 8 and h > 8:
            # cv2.rectangle(textImg, (x1, y), (x+w-1, y+h-1), (0, 255, 0), 2)

            rect = cv2.minAreaRect(contours[idx])
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(textImg, [box], 0, (0, 0, 255), 2)

            # we can filter theta as outlier based on other theta values
            # this will help in excluding the rare text region with different orientation from usual value
            theta = slope(box[0][0], box[0][1], box[1][0], box[1][1])
            cummTheta += theta
            ct += 1
            # print("Theta", theta)
    # find the average of all cumulative theta value
    orientation = cummTheta / ct

    return orientation


if __name__ == "__main__":
    filePath = 'image.png'
    img = cv2.imread(filePath)
    textImg = img.copy()
    connected, bw = preprocess(img)

    orientation = find_contours(connected, bw, textImg)
    print("Image orientation in degrees: ", orientation)

    finalImage = rotate(img, orientation)
    display(textImg, "Detected Text minimum bounding box")
    display(finalImage, "Skewered Image")
