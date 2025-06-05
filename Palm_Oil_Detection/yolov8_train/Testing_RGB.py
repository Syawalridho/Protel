# Jika pakai OpenCV
import cv2
gray = cv2.imread("tree2_2_jpg.rf.c8030653bcc1768b2072e3a8d710ac87.jpg")
rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

cv2.imshow("Grayscale", gray)
cv2.imshow("Converted to RGB", rgb)

cv2.waitKey(0)
cv2.destroyAllWindows()