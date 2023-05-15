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
    vertical_projection = cv2.GaussianBlur(vertical_projection, (5, 5), 0)

    # Find the peaks in the vertical projection
    row_sum = np.sum(vertical_projection, axis=1)
    # row_sum = row_sum.astype(np.float32)

    peaks, _ = find_peaks(row_sum, height=100, distance=20)
    coordinates = {}

    # Draw the detected lines on the original image
    for i, peak in enumerate(peaks):
        coordinates[i] = peak
        line = display_image[peak - 15:peak + 15, 0:input_image.shape[1]]

        # Save the line image to a file
        # cv2.line(display_img, (0, peak), (input_image.shape[1], peak), (0, 0, 255), thickness=2)
        cv2.imwrite(f"lines/line{i + 1}.png", line)

    # # Display the image with detected lines
    # cv2.imshow('Detected Lines', display_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    return coordinates

def detectWords(input_coordinates, input_image, display_img):
    # display_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2GRAY)
    lcoordinates = {}
    for l in range(len(input_coordinates)):
        x, y, w, h = 0, input_coordinates[l]-15, input_image.shape[1], 30
        line = input_image[y:y + h, x:x + w]
        # line = cv2.blur(line, (3, 3))

        # Find the contours in the line image
        contours, hierarchy = cv2.findContours(line, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Sort the contours from left to right based on their x-coordinate values
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])
        coordinates = {}
        # Iterate through each contour and compute the bounding rectangle
        for j, contour in enumerate(contours):
            # Extract the bounding box coordinates for the contour
            x2, y2, w2, h2 = cv2.boundingRect(contour)
            coordinates[j] = (x2, y2, w2, h2)
            # Extract the word from the original image
            word = display_image[y + y2:y + y2 + h2, x + x2:x + x2 + w2]
            # display_image(word)
            # Save the word image to a file
            cv2.imwrite(f"words/line{l + 1}_word{j + 1}.png", word)
        lcoordinates[l] = coordinates

    return lcoordinates

def detectLetters(wcoordinates, lcoordinates, input_image, display_img):
    display(input_image, "input_image")
    # define the kernel
    kernel = np.ones((1, 1), np.uint8)
    # erode the image
    input_image = cv2.erode(input_image, kernel,
                        iterations=1)
    display(input_image, "input_image")


    for l in range(len(lcoordinates)):
        xl, yl, wl, hl = 0, lcoordinates[l] - 15, input_image.shape[1], 30
        line_image = input_image[yl:yl + hl, xl:xl + wl]

        for i in range(len(wcoordinates[l])):
            x, y, w, h = wcoordinates[l][i]
            word_image = line_image[y:y + h, x:x + w]
            # word_image = cv2.blur(word_image, (3, 3))
            # display(word_image, "word_image")

            # Find the contours in the word image
            contours, hierarchy = cv2.findContours(word_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Sort the contours from left to right based on their x-coordinate values
            contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])
            letcoords = {}

            # Iterate through each contour and compute the bounding rectangle
            for j, contour in enumerate(contours):
                # Extract the bounding box coordinates for the contour
                x2, y2, w2, h2 = cv2.boundingRect(contour)
                letcoords[i] = (x2, y2, w2, h2)
                # Extract the word from the original image
                letter = word_image[y2:y2 + h2, x2:x2 + w2]
                # display_image(letter)
                # Save the word image to a file
                cv2.imwrite(f"letters/line{l + 1}_word{i +1}_letter{j + 1}.png", letter)
            letcoordinates = letcoords

    return letcoordinates


if __name__ == "__main__":
    image = cv2.imread("text1_v2.png")
    display_image = np.copy(image)
    connected, thresh = preprocessImage(image)

    lines_coordinates = detectLines(thresh, display_image)
    words_coordinates = detectWords(lines_coordinates, thresh, display_image)
    proccessed_image = preprocessText(display_image)
    letters_coordinates = detectLetters(words_coordinates, lines_coordinates, thresh, display_image)