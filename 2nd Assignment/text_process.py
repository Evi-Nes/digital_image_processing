import cv2
import numpy as np
import pandas as pd

debug = True

# Display image
def display(input_image, frame_name):
    if not debug:
        return
    h, w = input_image.shape[0:2]
    new_w = 800
    new_h = int(new_w * (h / w))
    input_image = cv2.resize(input_image, (new_w, new_h))
    cv2.imshow(frame_name, input_image)
    cv2.waitKey(0)


def preprocessText(input_image):
    """
    Preprocess the image to make it easier to find the text
    :param input_image: the given image
    :return: the preprocessed image
    """
    grayscale = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
    binary_image = cv2.threshold(grayscale, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # define the kernel and invert the image
    kernel = np.ones((3, 3), np.uint8)
    inverted_image = cv2.bitwise_not(binary_image)

    # dilate the image
    dilated_image = cv2.dilate(inverted_image, kernel, iterations=1)

    # Remove the dilated image from the original image
    removed_image = cv2.subtract(grayscale, dilated_image)

    # Perform thinning of the result image
    inverted_image = cv2.bitwise_not(removed_image)
    eroded_image = cv2.erode(inverted_image, kernel, iterations=1)

    final_image = np.copy(eroded_image)
    display(final_image, "final_image")

    return final_image

def getContour(original_image, input_image):
    """
    Get the contours of the image and return coordinates of the outer and inner contours
    :param original_image: the original image
    :param input_image: the preprocessed image
    :return:
    """
    contours, hierarchy = cv2.findContours(input_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    coordinates = []

    # Get the coordinates of the outer and inner contours. If contour has no parent, it is outer contour.
    for i, contour in enumerate(contours):
        if hierarchy[0][i][3] == -1:
            coordinates.append((contour, 'outer'))
        else:
            coordinates.append((contour, 'inner'))

    # Display the outer and inner contours (if exist) in the original image
    if coordinates is not None:
        for i, coordinate in enumerate(coordinates):
            if coordinate[1] == 'outer':
                contoured_image = cv2.drawContours(original_image, contours, i, (0, 0, 255), 2)
            else:
                contoured_image = cv2.drawContours(original_image, contours, i, (255, 0, 0), 2)

    display(contoured_image, "contours")

    return coordinates


if __name__ == "__main__":
    image = cv2.imread("fff.png")
    rotated_image = np.copy(image)

    processed_image = preprocessText(rotated_image)
    contour_cells = getContour(rotated_image, processed_image)