import numpy as np
import cv2

image1 = cv2.imread('im1.png')
image2 = cv2.imread('im2.png')

# Initiate SIFT detector
# sift = cv2.SIFT_create()
img1 = np.load('img1.npy', allow_pickle=True).item()
keypoint1, descriptors1 = img1["corners"], img1["descriptor"]
img2 = np.load('img2.npy', allow_pickle=True).item()
keypoint2, descriptors2 = img2["corners"], img2["descriptor"]

descriptors1 = np.array(descriptors1, dtype=np.float32)
descriptors2 = np.array(descriptors2, dtype=np.float32)
keypoints1_updated = []
keypoints2_updated = []

for x, y in keypoint1:
    keypoint = cv2.KeyPoint(x, y, 1)
    keypoints1_updated.append(keypoint)

for x, y in keypoint2:
    keypoint = cv2.KeyPoint(x, y, 1)
    keypoints2_updated.append(keypoint)

# finding the nearest match with KNN algorithm
index_params = dict(algorithm=0, trees=20)
search_params = dict(checks=150)  # or pass empty dictionary

# Initialize the FlannBasedMatcher
flann = cv2.FlannBasedMatcher(index_params, search_params)

Matches = flann.knnMatch(descriptors1, descriptors2, k=2)

# Need to draw only good matches, so create a mask
good_matches = [[0, 0] for i in range(len(Matches))]

# Ratio Test
for i, (m, n) in enumerate(Matches):
    if m.distance < 0.05 * n.distance:
        good_matches[i] = [1, 0]

# Draw the matches using drawMatchesKnn()
Matched = cv2.drawMatchesKnn(image1, keypoints1_updated, image2, keypoints2_updated, Matches, outImg=None,
                             matchColor=(0, 155, 0), singlePointColor=(0, 255, 255), matchesMask=good_matches, flags=0)

# Displaying the image
cv2.imwrite('Match.jpg', Matched)

# Draw lines between the matched keypoints
for match, list in enumerate(good_matches):
    if list == [0, 0]:
        continue
    kp1 = keypoints1_updated[Matches[match][0].queryIdx]
    kp2 = keypoints2_updated[Matches[match][0].trainIdx]

    # Get the keypoints for this match
    # kp1 = keypoints1_updated[match[0].queryIdx]
    # kp2 = keypoints2_updated[match[0].trainIdx]

    # Get the coordinates of the keypoints
    pt1 = (int(kp1.pt[0]), int(kp1.pt[1]))
    pt2 = (int(kp2.pt[0]), int(kp2.pt[1]))

    # Draw a line between the keypoints
    cv2.line(Matched, pt1, pt2, (0, 255, 0), 1)

cv2.imwrite('Matched_lines.jpg', Matched)
