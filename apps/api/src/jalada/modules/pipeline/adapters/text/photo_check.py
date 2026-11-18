"""Whether a photo is fit to read at all, before any model sees it.

Models asked to read a photo blurred past reading still give a likely amount, so the app does
not rely on them to say so: a photo that is far too small or too blurred is not sent, and the
person enters it by hand. The limits are kept loose, so only photos nobody could read are
stopped; anything in between goes to the model and to the person to check.
"""

import io

from PIL import Image, ImageFilter, ImageStat, UnidentifiedImageError

# Shorter side in pixels below which text cannot be made out.
MIN_SIDE = 200
# How much edge detail the photo has, measured at up to 1000 pixels across. A sharp receipt
# scores in the thousands, a slightly soft one in the hundreds; under this, nothing is legible.
MIN_SHARPNESS = 30.0


class PillowPhotoCheck:
    def problem(self, data: bytes) -> str | None:
        """Why the photo cannot be read, or None when it is worth trying."""
        try:
            image = Image.open(io.BytesIO(data))
            image.load()
        except (UnidentifiedImageError, OSError):
            return "unreadable file"
        if min(image.size) < MIN_SIDE:
            return "too small"
        gray = image.convert("L")
        gray.thumbnail((1000, 1000))
        edges = gray.filter(ImageFilter.FIND_EDGES)
        width, height = edges.size
        # The edge filter marks the photo's own border; it says nothing about the content.
        inside = edges.crop((4, 4, width - 4, height - 4))
        if ImageStat.Stat(inside).var[0] < MIN_SHARPNESS:
            return "too blurred"
        return None
