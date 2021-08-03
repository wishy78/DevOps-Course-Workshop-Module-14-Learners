# Canny edge detector implementation
# See https://towardsdatascience.com/canny-edge-detection-step-by-step-in-python-computer-vision-b49c3a2d8123

from utils.timeit import time_it
from scipy import ndimage
from scipy.ndimage.filters import convolve
import numpy as np

class CannyEdgeDetector:
    def __init__(
        self,
        sigma=1,
        kernel_size=5,
        weak_pixel=75,
        strong_pixel=255,
        lowthreshold=0.05,
        highthreshold=0.15,
    ):
        self.weak_pixel = weak_pixel
        self.strong_pixel = strong_pixel
        self.sigma = sigma
        self.kernel_size = kernel_size
        self.lowThreshold = lowthreshold
        self.highThreshold = highthreshold
        return

    @time_it
    def _rgb2grey(self, rgb):
        M, N, _ = rgb.shape
        grey = np.zeros((M, N), dtype=np.int32)

        for i in range(1, M - 1):
            for j in range(1, N - 1):
                r, g, b = rgb[i, j, 0], rgb[i, j, 1], rgb[i, j, 2]
                grey[i, j] = 0.2989 * r + 0.5870 * g + 0.1140 * b

        return grey

    @time_it
    def _gaussian_kernel(self, size, sigma=1):
        size = int(size) // 2
        x, y = np.mgrid[-size : size + 1, -size : size + 1]
        normal = 1 / (2.0 * np.pi * sigma ** 2)
        g = np.exp(-((x ** 2 + y ** 2) / (2.0 * sigma ** 2))) * normal
        return g

    @time_it
    def _sobel_filters(self, img):
        Kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], np.float32)
        Ky = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], np.float32)

        Ix = ndimage.filters.convolve(img, Kx)
        Iy = ndimage.filters.convolve(img, Ky)

        G = np.hypot(Ix, Iy)
        G = G / G.max() * 255
        theta = np.arctan2(Iy, Ix)
        return (G, theta)

    @time_it
    def _non_max_suppression(self, img, D):
        M, N = img.shape
        Z = np.zeros((M, N), dtype=np.int32)
        angle = D * 180.0 / np.pi
        angle[angle < 0] += 180

        for i in range(1, M - 1):
            for j in range(1, N - 1):
                try:
                    q = 255
                    r = 255

                    # angle 0
                    if (0 <= angle[i, j] < 22.5) or (157.5 <= angle[i, j] <= 180):
                        q = img[i, j + 1]
                        r = img[i, j - 1]
                    # angle 45
                    elif 22.5 <= angle[i, j] < 67.5:
                        q = img[i + 1, j - 1]
                        r = img[i - 1, j + 1]
                    # angle 90
                    elif 67.5 <= angle[i, j] < 112.5:
                        q = img[i + 1, j]
                        r = img[i - 1, j]
                    # angle 135
                    elif 112.5 <= angle[i, j] < 157.5:
                        q = img[i - 1, j - 1]
                        r = img[i + 1, j + 1]

                    if (img[i, j] >= q) and (img[i, j] >= r):
                        Z[i, j] = img[i, j]
                    else:
                        Z[i, j] = 0

                except IndexError as e:
                    pass

        return Z

    @time_it
    def _threshold(self, img):

        highThreshold = img.max() * self.highThreshold
        lowThreshold = highThreshold * self.lowThreshold

        M, N = img.shape
        res = np.zeros((M, N), dtype=np.int32)

        weak = np.int32(self.weak_pixel)
        strong = np.int32(self.strong_pixel)

        strong_i, strong_j = np.where(img >= highThreshold)

        weak_i, weak_j = np.where((img <= highThreshold) & (img >= lowThreshold))

        res[strong_i, strong_j] = strong
        res[weak_i, weak_j] = weak

        return res

    @time_it
    def _hysteresis(self, img):

        M, N = img.shape
        weak = self.weak_pixel
        strong = self.strong_pixel

        for i in range(1, M - 1):
            for j in range(1, N - 1):
                if img[i, j] == weak:
                    try:
                        if (
                            (img[i + 1, j - 1] == strong)
                            or (img[i + 1, j] == strong)
                            or (img[i + 1, j + 1] == strong)
                            or (img[i, j - 1] == strong)
                            or (img[i, j + 1] == strong)
                            or (img[i - 1, j - 1] == strong)
                            or (img[i - 1, j] == strong)
                            or (img[i - 1, j + 1] == strong)
                        ):
                            img[i, j] = strong
                        else:
                            img[i, j] = 0
                    except IndexError as e:
                        pass

        return img

    @time_it
    def detect(self, img: np.ndarray) -> np.ndarray:
        greyscale = self._rgb2grey(img)
        img_smoothed = convolve(greyscale, self._gaussian_kernel(self.kernel_size, self.sigma))
        gradientMat, thetaMat = self._sobel_filters(img_smoothed)
        nonMaxImg = self._non_max_suppression(gradientMat, thetaMat)
        thresholdImg = self._threshold(nonMaxImg)
        img_final = self._hysteresis(thresholdImg)
        return img_final
