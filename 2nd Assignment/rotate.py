import cv2
import numpy as np

debug = True

# Display image
def display(input_image, frame_name):
    """
    Function that displays the given image with the given frame name. If debug = False, will not display anything.
    :param input_image: the given image
    :param frame_name: the given name for the frame
    :return:
    """
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

    # Find the gradient map
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    grad = cv2.morphologyEx(grayscale, cv2.MORPH_GRADIENT, kernel)
    # display(grad, "gradient")

    # Binarize the gradient image
    _, bw_image = cv2.threshold(grad, 0.0, 255.0, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # display(bw_image, "binarized")

    # Connect horizontally oriented regions
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
    connected_image = cv2.morphologyEx(bw_image, cv2.MORPH_CLOSE, kernel)
    # display(connected_image, "connected")

    return connected_image, bw_image

def findRotationAngle(input_image, disp_image):
    """
    Find the angle of rotation of the image using DFT and magnitude spectrum
    :param disp_image: copy of the original image
    :param input_image: the preprocessed image
    :return: the calculated angle for rotation
    """
    height, width = input_image.shape[:2]

    # Calculate the DFT of the image and shift the zero-freq component to the center of the spectrum
    f = np.fft.fft2(input_image)
    fshift = np.fft.fftshift(f)

    # Calculate the magnitude spectrum of the DFT
    magnitude_spectrum = 20 * np.log(np.abs(fshift))
    mret, mthresh = cv2.threshold(magnitude_spectrum, 235, 255, cv2.THRESH_BINARY)
    # display(mthresh, "magnitude spectrum")
    src = mthresh
    src = np.array(src, dtype=np.int16)
    dst = np.zeros((height, width), dtype=np.int16)

    # Apply Canny edge detection and HoughLines function
    edges = cv2.Canny(src, dst, 200, 235, 3, False)
    # display(edges, "edges")

    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 5, np.array([]), minLineLength=20, maxLineGap=2)
    lines = lines.squeeze()

    slope = np.array([])
    center = (width // 2, height // 2)
    radius = 180

    # Calculate the slope of each line and draw the lines on the image
    for line in lines:
        x1, y1, x2, y2 = line

        if (y1 < (center[1] - radius)) | (y2 < (center[1] - radius)) | (y1 > (center[1] + radius)) | (y2 > (center[1] + radius)):
            if x1 == x2:
                x1 = x1 + 1

            slope = np.append(slope, ((y2 - y1) / (x2 - x1)))
            cv2.line(disp_image, (x1, y1), (x2, y2), (255, 64, 64), 3)

        else:
            continue

    display(disp_image, "lines")

    slope = np.mean(slope)
    temp = np.degrees(np.arctan(slope))

    if temp == 0:
        angle_degrees = 0
    elif temp > 0:
        angle_degrees = -(90 - temp)
    else:
        angle_degrees = (90 + temp)

    print("DFT angle", angle_degrees)

    return angle_degrees

def serialSearch(input_image, angle_degrees):
    """
    Through a serial search, find the desired angle of rotation of the image
    :param input_image: the given image
    :param angle_degrees: the angle of rotation calculated by findRotationAngle
    :return: the angle of rotation after the serial search
    """
    range_degrees = np.arange(np.int32(angle_degrees-10), np.int32(angle_degrees+10), 1)
    variance_normalized_f = np.array([])

    for possible_angle in range_degrees:
        rotated_img = rotateImage(input_image, possible_angle)

        # Calculate the DFT of the image and shift the zero-freq component to the center of the spectrum
        f = np.fft.fft2(rotated_img)
        fshift = np.fft.fftshift(f)

        # Calculate the magnitude spectrum of the DFT
        magnitude_spectrum = 20 * np.log(np.abs(fshift))
        mret, mthresh = cv2.threshold(magnitude_spectrum, 235, 255, cv2.THRESH_BINARY)
        vertical_projection = np.sum(mthresh, axis=1)

        # Compute the first derivative of the vertical projection and the variance of the first derivative
        d_vertical_projection = np.diff(vertical_projection)
        variance_normalized_f = np.append(variance_normalized_f, np.var(d_vertical_projection))

    # Normalize the variance/sign_changes to the range [0, 1]
    variance_normalized = variance_normalized_f / np.max(variance_normalized_f)

    index = np.argmax(variance_normalized)
    calculated_angle = range_degrees[index]
    print("serial angle", calculated_angle)

    final_angle = np.int32((calculated_angle*0.5 + angle_degrees*0.1)/0.6)
    print("final angle", final_angle)

    return final_angle

def rotateImage(input_image, rotation_angle):
    """
    Rotate the image by the given angle
    :param input_image: the given image
    :param rotation_angle: the angle of rotation in degrees
    :return: the rotated image
    """
    rows, cols = input_image.shape[:2]
    M = cv2.getRotationMatrix2D((cols // 2, rows // 2), rotation_angle, 1)

    # Calculate new image dimensions
    cos_theta = abs(M[0, 0])
    sin_theta = abs(M[0, 1])
    new_width = int((rows * sin_theta) + (cols * cos_theta))
    new_height = int((rows * cos_theta) + (cols * sin_theta))

    # Adjust the rotation matrix to take into account translation
    M[0, 2] += (new_width / 2) - cols // 2
    M[1, 2] += (new_height / 2) - rows // 2
    rotated_img = cv2.warpAffine(input_image, M, (new_width, new_height))

    return rotated_img


if __name__ == "__main__":
    image = cv2.imread("image222.png")
    display_image = np.copy(image)
    connected, thresh = preprocessImage(image)

    angle = findRotationAngle(connected, display_image)
    serial_angle = serialSearch(connected, angle)

    rotated_image = rotateImage(image, serial_angle)
    cv2.imwrite("rotated_image.jpg", rotated_image)

