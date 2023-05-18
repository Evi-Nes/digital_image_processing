import cv2
import numpy as np
from scipy.signal import find_peaks

debug = True


def display(input_image, frame_name="OpenCV Image"):
    if not debug:
        return
    h, w = input_image.shape[0:2]
    new_w = 800
    new_h = int(new_w * (h / w))
    input_image = cv2.resize(input_image, (new_w, new_h))
    cv2.imshow(frame_name, input_image)
    cv2.waitKey(0)


def preprocessImage(input_image):
    """
    Preprocess the image to get the text regions
    :param input_image: the given image
    :return: connected_image the image with connected text regions
    bw_image: the binarized image
    """
    grayscale = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    # find the gradient map
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    grad = cv2.morphologyEx(grayscale, cv2.MORPH_GRADIENT, kernel)

    # display(grad)

    # Binarize the gradient image
    _, bw_image = cv2.threshold(grad, 0.0, 255.0, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # display(bw_image)

    # connect horizontally oriented regions
    # kernel value (9,1) can be changed to improve the text detection
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
    connected_image = cv2.morphologyEx(bw_image, cv2.MORPH_CLOSE, kernel)
    # display(connected_image)

    return connected_image, bw_image


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
    # display(final_image, "final_image")

    return final_image

def detectLines(input_image, display_img):
    # Compute the vertical projection of brightness
    vertical_projection = cv2.reduce(input_image, 1, cv2.REDUCE_SUM, dtype=cv2.CV_32F)

    # Smooth the vertical projection with a Gaussian filter
    vertical_projection = cv2.GaussianBlur(vertical_projection, (3, 3), 0)

    # Find the peaks in the vertical projection
    row_sum = np.sum(vertical_projection, axis=1)

    peaks, _ = find_peaks(row_sum, height=100, distance=20)
    coordinates = {}

    # Draw the detected lines on the original image
    for i, peak in enumerate(peaks):
        if i % 2 == 1:
            coordinates[i] = peak + 10
            line = display_image[peak - 20:peak + 35, 0:input_image.shape[1]]

            # Save the line image to a file
            # cv2.line(display_img, (0, peak + 10), (input_image.shape[1], peak + 10), (0, 0, 255), thickness=2)
            # cv2.imwrite(f"lines/line{i}.png", line)
        else:
            continue

    # # Display the image with detected lines
    # cv2.imshow('Detected Lines', display_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    normal_coordinates = [coordinates[k] for k in range(1, len(coordinates), 2)]
    return normal_coordinates

def detectWords(input_coordinates, input_image, display_img):
    display_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2GRAY)
    coords = []

    for i in range(len(input_coordinates)):
        # if i % 2 == 0:
        #     continue
        x, y, w, h = 15, input_coordinates[i] - 35, input_image.shape[1]-20, 60
        line = display_img[y:y + h, x:x + w]
        lineb = cv2.blur(line, (25, 25))

        # Compute the horizontal projection of brightness
        horizontal_projection = cv2.reduce(lineb, 0, cv2.REDUCE_SUM, dtype=cv2.CV_32F)

        # Smooth the horizontal projection with a Gaussian filter
        horizontal_projection = cv2.GaussianBlur(horizontal_projection, (5, 5), 0)
        col_sum = np.sum(horizontal_projection, axis=0)

        # Find the peaks in the horizontal projection
        peaks, _ = find_peaks(col_sum, height=15000, distance=60)
        coordinates = []

        # Draw the detected lines on the original image
        for j, peak in enumerate(peaks):
            coordinates.append(peak)

            if j == 0:
                word = line[0:line.shape[0], 15:peak]
            elif j == len(input_coordinates)-1:
                word = line[0:line.shape[0], peak:line.shape[1]-15]
            else:
                word = line[0:line.shape[0], coordinates[j-1]:peak]
                # Save the line image to a file (x,y)
                # cv2.line(line, (peak, 0), (peak, line.shape[0]), (0, 0, 255), thickness=2)
            # cv2.imwrite(f"words/line{i}_word{j + 1}.png", word)

        coords.append(coordinates)

        # cv2.imshow('Detected Lines', line)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    return coords

def detectLetters(input_coordinates, display_img):
    display_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2GRAY)
    coords = []

    for i in range(len(input_coordinates)):
        # Calculate the coordinates of each line
        x, y, w, h = 15, input_coordinates[i] - 35, display_img.shape[1]-20, 70
        line = display_img[y:y + h, x:x + w]

        # Compute and smooth the horizontal projection of brightness
        horizontal_projection = cv2.reduce(line, 0, cv2.REDUCE_SUM, dtype=cv2.CV_32F)
        horizontal_projection = cv2.GaussianBlur(horizontal_projection, (3, 3), 0)
        col_sum = np.sum(horizontal_projection, axis=0)

        # Find the peaks in the horizontal projection
        peaks, _ = find_peaks(col_sum, height=200, distance=30)
        coordinates = []
        lcoordinates = []

        # Unpack the coordinates of each letter
        for j, peak in enumerate(peaks):
            coordinates.append(peak)

            if j == 0:
                # letter = line[0:line.shape[0], 15:peak]
                lcoords = (x, y, x + peak, y + h)
            elif j == len(peaks)-1:
                continue
            else:
                # letter = line[0:line.shape[0], coordinates[j-1]:peak]
                lcoords = (x + coordinates[j-1], y, x + peak, y + h)

            # Save each letter to a file
            # cv2.imwrite(f"letters/line{i+1}_word{j + 1}.png", letter)

            lcoordinates.append(lcoords)
        coords.append(lcoordinates)

    return coords


if __name__ == "__main__":
    image = cv2.imread("text1_v2.png")
    display_image = np.copy(image)
    connected, thresh = preprocessImage(image)

    lines_coordinates = detectLines(thresh, display_image)
    # words_coordinates = detectWords(lines_coordinates, thresh, display_image)
    letter_coordinates = detectLetters(lines_coordinates, display_image)
    proccessed_image = preprocessText(display_image)
