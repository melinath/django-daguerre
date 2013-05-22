from array import array
from itertools import chain, repeat, izip

import numpy
from scipy.misc import fromimage, toimage
from scipy.ndimage.filters import generic_gradient_magnitude, sobel

try:
    from PIL import Image
except ImportError:
    import Image


def seam_carve(image, new_width, new_height):
    image = carve_width(image, new_width)
    image = image.rotate(90)
    image = carve_width(image, new_height)
    return image.rotate(-90)


def carve_width(image, new_width):
    width, height = image.size
    cost = get_cost(image)

    while width > new_width:
        seam = get_seam(cost)
        image = toimage(delete_seam(fromimage(image), seam))
        cost = recalculate_cost(image, cost, seam)
        width, height = image.size
    return image


def get_cost(image):
    width, height = image.size
    energy = generic_gradient_magnitude(fromimage(image, flatten=True),
                                        derivative=sobel)
    # Clip the energy to color values.
    energy = energy.clip(0, 255)
    cost = []
    # initialize the bottom row.
    cost.append(array('B', energy[0]))

    # Localize min to save lookups.
    mi = min

    for y in range(1, height):
        # Perhaps use row, last_row to avoid row lookup?
        # row = [min([last_row[dx]...)]
        last_row = cost[y - 1]
        energy_row = array('B', energy[y])
        zipped = zip(xrange(width), energy_row)
        # iff x-1 wraps around, the first array will be empty.
        cost.append([mi(last_row[x - 1:x + 2] or
                        last_row[x:x + 2]) + val
                     for x, val in zipped])
    return cost


def recalculate_cost(image, cost, seam):
    width, height = image.size
    # Recalculate the pieces of the cost that will have changed.
    energy = generic_gradient_magnitude(fromimage(image, flatten=True),
                                        derivative=sobel)
    energy = energy.clip(0, 255)
    for y, x in seam:
        del cost[y][x]

    # Localize a few things to avoid lookups
    first_x = seam[0][1]
    mi = min

    # We start with one pixel left/right of the first deleted
    # pixel and go up in a cone.
    lefts = chain(xrange(first_x - 1, -1, -1), repeat(0))
    rights = chain(xrange(first_x, width), repeat(width - 1))
    ys = xrange(1, height)
    for y, left, right in izip(ys, lefts, rights):
        last_row = cost[y - 1]
        energy_row = array('B', energy[y, left:right])
        zipped = zip(xrange(left, right), energy_row)
        cost[y][left:right] = [mi(last_row[x - 1:x + 2] or
                                  last_row[x:x + 2]) + val
                               for x, val in zipped]
    return cost


def get_seam(cost):
    height = len(cost)
    width = len(cost[0])
    mincost = numpy.inf
    x = 0
    for dx, val in enumerate(cost[-1]):
        if val < mincost:
            mincost = val
            x = dx
    seam = [(height - 1, x)]

    for y in range(height - 2, -1, -1):
        bestcost = numpy.inf
        for dx in (x - 1, x, x + 1):
            if dx >= 0 and dx < width:
                new_cost = cost[y][dx]
                if new_cost < bestcost:
                    bestcost = new_cost
                    x = dx
        seam.append((y, x))

    seam.reverse()
    return seam


def delete_seam(arr, seam):
    mask = numpy.ones(arr.shape, dtype=numpy.bool)
    for y, x in seam:
        mask[y, x] = False
    return numpy.reshape(arr[mask],
                         (arr.shape[0], arr.shape[1] - 1) + arr.shape[2:])
