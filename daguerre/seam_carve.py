import numpy
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
        image = delete_seam(image, seam)
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
    new_cost = numpy.delete(cost, [x + cost.shape[1] * y
                                   for y, x in enumerate(seam)])
    new_cost = numpy.reshape(new_cost, (height, width))

    for y in range(0, height):
        # We start with one pixel left/right of the first deleted
        # pixel and go up in a cone.
        left = max((seam[0] - y - 1, 0))
        right = min((seam[0] + y, width))
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
    seam = [x]

    for y in range(height - 1, 0, -1):
        bestcost = numpy.inf
        for dx in (x - 1, x, x + 1):
            if dx >= 0 and dx < width:
                if cost[y, dx] < bestcost:
                    bestcost = cost[y, dx]
                    x = dx
        seam.append(x)

    seam.reverse()
    return seam


def delete_seam(image, seam):
    width, height = image.size
    new_width, new_height = width - 1, height
    new_image = Image.new(image.mode, (new_width, new_height))
    pixels = image.load()
    new_pixels = new_image.load()

    for y in range(0, height):
        for x in range(0, width - 1):
            if x < seam[y]:
                # left of the seam: copy
                new_pixels[x, y] = pixels[x, y]
            elif x >= seam[y]:
                # right of the seam: shift 1px.
                # Should maybe do some sort of composite?
                new_pixels[x, y] = pixels[x + 1, y]

    return new_image
