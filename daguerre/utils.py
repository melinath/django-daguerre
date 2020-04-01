import struct
import zlib

from hashlib import sha1

from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.files.temp import NamedTemporaryFile
from django.utils.encoding import smart_bytes
import six
try:
    from PIL import Image, ImageFile, ExifTags
except ImportError:
    import Image
    import ImageFile
    import ExifTags

#: Formats that we trust to be able to handle gracefully.
KEEP_FORMATS = ('PNG', 'JPEG', 'GIF')
#: Default format to convert other file types to.
DEFAULT_FORMAT = 'PNG'
#: Map Exif orientation data to corresponding PIL image transpose values
ORIENTATION_TO_TRANSPOSE = {
    1: None,
    2: (Image.FLIP_LEFT_RIGHT,),
    3: (Image.ROTATE_180,),
    4: (Image.ROTATE_180, Image.FLIP_LEFT_RIGHT,),
    5: (Image.ROTATE_270, Image.FLIP_LEFT_RIGHT,),
    6: (Image.ROTATE_270,),
    7: (Image.ROTATE_90, Image.FLIP_LEFT_RIGHT,),
    8: (Image.ROTATE_90,),
}
#: Which Exif orientation tags correspond to a 90deg or 270deg rotation.
ROTATION_TAGS = (5, 6, 7, 8)
#: Map human-readable Exif tag names to their markers.
EXIF_TAGS = dict((y, x) for (x, y) in six.iteritems(ExifTags.TAGS))


def make_hash(*args, **kwargs):
    start = kwargs.get('start', None)
    stop = kwargs.get('stop', None)
    step = kwargs.get('step', None)
    return sha1(smart_bytes(u''.join([
        six.text_type(arg) for arg in args])
    )).hexdigest()[start:stop:step]


def get_exif_orientation(image):
    # Extract the orientation tag
    try:
        exif_data = image.getexif()
    except AttributeError:
        # No Exif data, return None
        return None
    if exif_data is not None and EXIF_TAGS['Orientation'] in exif_data:
        orientation = exif_data[EXIF_TAGS['Orientation']]
        return orientation
    # No Exif orientation tag, return None
    return None


def apply_exif_orientation(image):
    """
    Reads an image Exif data for orientation information. Applies the
    appropriate rotation with PIL transposition. Use before performing a PIL
    .resize() in order to retain correct image rotation. (.resize() discards
    Exif tags.)

    Accepts a PIL image and returns a PIL image.

    """
    orientation = get_exif_orientation(image)
    if orientation is not None:
        # Apply corresponding transpositions
        transpositions = ORIENTATION_TO_TRANSPOSE[orientation]
        if transpositions:
            for t in transpositions:
                image = image.transpose(t)
    return image


def exif_aware_size(image):
    """
    Intelligently get an image size, flipping width and height if the Exif
    orientation tag includes a 90deg or 270deg rotation.

    :param image: A PIL Image.

    :returns: A 2-tuple (width, height).

    """
    # For .png images, don't try to make exif modifications.
    if image.format != 'PNG':
        # Extract the orientation tag
        orientation = get_exif_orientation(image)
        if orientation in ROTATION_TAGS:
            # Exif data indicates image should be rotated. Flip dimensions.
            return image.size[::-1]
    return image.size


def exif_aware_resize(image, *args, **kwargs):
    """
    Intelligently resize an image, taking Exif orientation into account. Takes
    the same arguments as the PIL Image ``.resize()`` method.

    :param image: A PIL Image.

    :returns: An PIL Image object.

    """

    image = apply_exif_orientation(image)
    return image.resize(*args, **kwargs)


def get_image_dimensions(file_or_path, close=False):
    """
    A modified version of ``django.core.files.images.get_image_dimensions``
    which accounts for Exif orientation.

    """

    p = ImageFile.Parser()
    if hasattr(file_or_path, 'read'):
        file = file_or_path
        file_pos = file.tell()
        file.seek(0)
    else:
        file = open(file_or_path, 'rb')
        close = True
    try:
        # Most of the time Pillow only needs a small chunk to parse the image
        # and get the dimensions, but with some TIFF files Pillow needs to
        # parse the whole file.
        chunk_size = 1024
        while 1:
            data = file.read(chunk_size)
            if not data:
                break
            try:
                p.feed(data)
            except zlib.error as e:
                # ignore zlib complaining on truncated stream, just feed more
                # data to parser (ticket #19457).
                if e.args[0].startswith("Error -5"):
                    pass
                else:
                    raise
            except struct.error:
                # Ignore PIL failing on a too short buffer when reads return
                # less bytes than expected. Skip and feed more data to the
                # parser (ticket #24544).
                pass
            except RuntimeError:
                # e.g. "RuntimeError: could not create decoder object" for
                # WebP files. A different chunk_size may work.
                pass
            if p.image:
                return exif_aware_size(p.image)
            chunk_size *= 2
        return (None, None)
    finally:
        if close:
            file.close()
        else:
            file.seek(file_pos)


def save_image(
        image,
        storage_path,
        format=DEFAULT_FORMAT,
        storage=default_storage):
    """
    Saves a PIL image file to the given storage_path using the given storage.
    Returns the final storage path of the saved file.

    """
    if format not in KEEP_FORMATS:
        format = DEFAULT_FORMAT

    with NamedTemporaryFile() as temp:
        image.save(temp, format=format)
        return storage.save(storage_path, File(temp))
