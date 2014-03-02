from hashlib import sha1

from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.files.temp import NamedTemporaryFile
from django.utils.encoding import smart_bytes
import six
try:
    from PIL import Image, ExifTags
except ImportError:
    import Image, ExifTags

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
#: Map human-readable Exif tag names to their markers.
EXIF_TAGS = dict((v,k) for k, v in ExifTags.TAGS.items())


def make_hash(*args, **kwargs):
    start = kwargs.get('start', None)
    stop = kwargs.get('stop', None)
    step = kwargs.get('step', None)
    return sha1(smart_bytes(u''.join([
        six.text_type(arg) for arg in args])
    )).hexdigest()[start:stop:step]


def apply_exif_orientation(image):
    """
    Reads an image Exif data for orientation information. Applies the
    appropriate rotation with PIL transposition. Use before performing a PIL
    .resize() in order to retain correct image rotation. (.resize() discards
    Exif tags.)

    Accepts a PIL image and returns a PIL image.

    """
    # Extract the orientation tag
    try:
       exif_data = image._getexif() # should be careful with that _method
    except AttributeError:
        # No exif data, return original image
        return image
    if exif_data is not None and EXIF_TAGS['Orientation'] in exif_data: 
        orientation = exif_data[EXIF_TAGS['Orientation']]
        # Apply the corresponding tranpositions
        transpositions = ORIENTATION_TO_TRANSPOSE[orientation]
        if transpositions:
            for t in transpositions:
                image = image.transpose(t)
    return image


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
