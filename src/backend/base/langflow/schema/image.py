import base64

from PIL import Image as PILImage
from pydantic import BaseModel

IMAGE_ENDPOINT = "/files/images/"


def is_image_file(file_path):
    try:
        with PILImage.open(file_path) as img:
            img.verify()  # Verify that it is, in fact, an image
        return True
    except (IOError, SyntaxError):
        return False

class Image(BaseModel):
    path: str | None = None
    url: str | None = None

    def to_base64(self):
        if self.path:
            files = get_files([self.path], convert_to_base64=True)
            return files[0]
        raise ValueError("Image path is not set.")

    def to_content_dict(self):
        return {
            "type": "image_url",
            "image_url": self.to_base64(),
        }

    def get_url(self):
        return f"{IMAGE_ENDPOINT}{self.path}"
