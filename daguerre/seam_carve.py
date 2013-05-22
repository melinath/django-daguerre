import numpy
from scipy.misc import fromimage, toimage
from scipy.ndimage.filters import generic_gradient_magnitude, sobel

try:
    from PIL import Image, ImageOps
except ImportError:
    import Image
    import ImageOps


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
    im_arr = numpy.reshape(ImageOps.grayscale(image).getdata(),
                           (height, width))
    energy = generic_gradient_magnitude(im_arr, derivative=sobel)
    # Clip the energy to color values.
    energy = energy.clip(0, 255)
    cost = []
    # initialize the bottom row.
    cost.append(list(energy[0]))

    for y in range(1, height):
        # Perhaps use row, last_row to avoid row lookup?
        # row = [min([last_row[dx]...)]
        last_row = cost[y - 1]
        # iff x-1 wraps around, the first array will be empty.
        cost.append([min(last_row[x - 1:x + 1] or
                         last_row[x:x + 1]) + energy[y, x]
                     for x in xrange(width)])
    return cost


def recalculate_cost(image, cost, seam):
    width, height = image.size
    # Recalculate the pieces of the cost that will have changed.
    im_arr = numpy.reshape(ImageOps.grayscale(image).getdata(),
                           (height, width))
    energy = generic_gradient_magnitude(im_arr, derivative=sobel)
    energy = energy.clip(0, 255)
    for y, x in enumerate(seam):
        del cost[y][x]

    # Localize a few things to avoid lookups
    first_x = seam[0]

    for y in range(1, height):
        # We start with one pixel left/right of the first deleted
        # pixel and go up in a cone.
        left = max((first_x - y - 1, 0))
        right = min((first_x + y, width))
        last_row = cost[y - 1]
        cost[y][left:right] = [min(last_row[x - 1:x + 1] or
                                   last_row[x:x + 1]) + energy[y, x]
                               for x in xrange(left, right)]
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
    seam = numpy.zeros(height, int)
    seam[height - 1] = x

    for y in range(height - 2, -1, -1):
        bestcost = numpy.inf
        for dx in (x - 1, x, x + 1):
            if dx >= 0 and dx < width:
                new_cost = cost[y][dx]
                if new_cost < bestcost:
                    bestcost = new_cost
                    x = dx
        seam[y] = x

    return numpy.flipud(seam)


def delete_seam(arr, seam):
    mask = numpy.fromfunction(lambda y, x, *args: seam[y] == x,
                              arr.shape,
                              dtype=int)
    masked = numpy.ma.array(arr, mask=mask)
    resized = masked.compressed()
    return numpy.reshape(resized,
                         (arr.shape[0], arr.shape[1] - 1) + arr.shape[2:])
