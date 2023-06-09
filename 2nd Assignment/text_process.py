import cv2
import numpy as np

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
    # display(final_image, "final_image")

    return final_image

def getContour(original_image, input_image):
    """
    Get the contours of the image and return coordinates of the outer and inner contours
    :param original_image: the original image
    :param input_image: the preprocessed image
    :return:
    """
    contours, hierarchy = cv2.findContours(input_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Store the outer and inner contours in separate arrays
    outer_contours = []
    inner_contours = []
    outer_complex = []
    inner_complex = []
    all_coordinates = []
    inner = False

    for i, cnt in enumerate(contours):
        if hierarchy[0][i][3] == -1:  # if contour has no parent, it is outer contour
            outer_contours.append(cnt)
            outer_coordinates = cnt.reshape(-1, 2)

            for x, y in outer_coordinates:
                outer_complex.append(complex(x, y))

            outer_complex_array = np.array(outer_complex)

            # print('outer coordinates', outer_coordinates)
            # print('outer_complex_array', outer_complex_array)

        else:  # if contour has parent, it is inner contour
            inner = True
            inner_contours.append(cnt)
            inner_coordinates = cnt.reshape(-1, 2)

            for x, y in inner_coordinates:
                inner_complex.append(complex(x, y))

            inner_complex_array = np.array(inner_complex)

    if len(outer_contours) > 0:
        contoured_image = cv2.drawContours(original_image, outer_contours, -1, (255, 0, 0), 2)
    if len(inner_contours) > 0:
        contoured_image = cv2.drawContours(original_image, inner_contours, -1, (0, 0, 255), 2)
    # display(contoured_image, "contours")

    if inner == True:
        all_coordinates = outer_complex_array, inner_complex_array
        return all_coordinates
    else:
        all_coordinates = outer_complex_array
        return all_coordinates

def getDFT(input_array):
    """
    Get the DFT of the input array
    :param input_array: the input array
    :return: the DFT of the input array
    """
    if len(input_array) != 2:
        dft = np.fft.fft(input_array)
        description = np.abs(dft[1::])
    else:
        print(input_array[0])
        dft_outer = np.fft.fft(input_array[0])
        description_outer = np.abs(dft_outer[1::])

        dft_inner = np.fft.fft(input_array[1])
        description_inner = np.abs(dft_inner[1::])

        description = np.concatenate((description_outer, description_inner), axis=0)

    return description

def compareDFT(original, test):
    for i in range(len(test)):
        if np.allclose(original, test[i], rtol=1, atol=1):
            print("The letter is: ", i+1)
    return i


if __name__ == "__main__":
    image = cv2.imread("1.png")
    rotated_image = np.copy(image)

    processed_image = preprocessText(rotated_image)
    contour_cells = getContour(rotated_image, processed_image)
    result = getDFT(contour_cells)

    results_test = []
    letters = [1, 2, 3, 4]
    results_test_array = np.empty((4,), dtype=object)

    for i in letters:
        filename = str(i) + ".png"
        image_test = cv2.imread(filename)
        rotated_image_test = np.copy(image_test)

        processed_image_test = preprocessText(rotated_image_test)
        contour_cells_test = getContour(rotated_image_test, processed_image_test)
        result_test = getDFT(contour_cells_test)

        results_test_array[i-1] = np.array(result_test[:])

    final = compareDFT(result, results_test_array)

