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
    cost = numpy.zeros(energy.shape)
    # initialize the bottom row.
    cost[0] = energy[0].copy()

    for y in range(1, height):
        for x in range(0, width):
            # Find the lowest-cost x value in the three pixels below this.
            bestcost = min([cost[y - 1, dx]
                            for dx in (x - 1, x, x + 1)
                            if dx >= 0 and dx < width])
            # Add that cost to the energy of the current position.
            cost[y, x] = bestcost + energy[y, x]
    return cost


def recalculate_cost(image, cost, seam):
    width, height = image.size
    # Recalculate the pieces of the cost that will have changed.
    im_arr = numpy.reshape(ImageOps.grayscale(image).getdata(),
                           (height, width))
    energy = generic_gradient_magnitude(im_arr, derivative=sobel)
    energy = energy.clip(0, 255)
    new_cost = delete_seam(cost, seam)
    new_cost = numpy.reshape(new_cost, (height, width))
    first_x = seam[0]

    for y in range(0, height):
        # We start with one pixel left/right of the first deleted
        # pixel and go up in a cone.
        left = max((first_x - y - 1, 0))
        right = min((first_x + y, width))
        for x in range(left, right):
            bestcost = min([new_cost[y - 1, dx]
                            for dx in (x - 1, x, x + 1)
                            if dx >= 0 and dx < width])
            new_cost[y, x] = bestcost + energy[y, x]
    return new_cost


def get_seam(cost):
    height, width = cost.shape
    mincost = numpy.inf
    x = 0
    for dx in range(0, width):
        if cost[-1, dx] < mincost:
            mincost = cost[-1, dx]
            x = dx
    seam = numpy.zeros(height, int)
    seam[height - 1] = x

    for y in range(height - 2, -1, -1):
        bestcost = numpy.inf
        for dx in (x - 1, x, x + 1):
            if dx >= 0 and dx < width:
                if cost[y, dx] < bestcost:
                    bestcost = cost[y, dx]
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
