from django.db.models.fields.files import ImageField, ImageFieldFile
from PIL import Image
import os

def _add_thumb(s):
    """
    Modifies a string (filename, URL) containing an image filename, to insert
    '.thumb'
    """
    parts = s.split(".")
    parts.insert(-1, "thumb")
    if parts[-1].lower() not in ['jpeg', 'jpg']:
        parts[-1] = 'jpg'
    new_path = ".".join(parts)
    # if not os.path.exists(new_path):
    #    new_path = None
    return new_path

class ThumbnailImageFieldFile(ImageFieldFile):

    create_additional_thumbnail = False

    def _get_thumb_path(self):
        return _add_thumb(self.path)
    thumb_path = property(_get_thumb_path)
    
    def _get_thumb_url(self):
        return _add_thumb(self.url)
    thumb_url = property(_get_thumb_url)

    def save(self, name, content, save=True):
        super(ThumbnailImageFieldFile, self).save(name, content, save)

        if self.create_additional_thumbnail:
            img = Image.open(self.path)
            img.thumbnail(
                (self.field.thumb_width, self.field.thumb_height),
                Image.ANTIALIAS
            )
            img.save(self.thumb_path, 'JPEG')

    def delete(self, save=True):
        if os.path.exists(self.thumb_path):
            os.remove(self.thumb_path)
        super(ThumbnailImageFieldFile, self).delete(save)


class ThumbnailImageFieldFile2(ThumbnailImageFieldFile):
    create_additional_thumbnail = True
    
class ThumbnailImageField(ImageField):
    """
    Behaves like a regular ImageField, but stores an extra (JPEG) thumbnail
    image, providing FIELD.thumb_url and FIELD.thumb_path.
    
    Accepts two additional, optional arguments: thumb_width and thumb_height,
    both defaulting to 128 (pixels). Resizing will preserve aspect ratio while
    staying inside the requested dimensions; see PIL's Image.thumbnail()
    method documentation for details.
    """
    attr_class = ThumbnailImageFieldFile

    def __init__(self, thumb_width=128, thumb_height=128, add_thumb=False, *args, **kwargs):
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height
        if add_thumb:
            # self.attr_class = ThumbnailImageFieldFile2
            self.attr_class.create_additional_thumbnail = True
        super(ThumbnailImageField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        "Returns field's value just before saving."
        file = super(ThumbnailImageField, self).pre_save(model_instance, add)  # it will call ImageFieldFile::save
        if file and not file._committed:
            # Commit the file to storage prior to saving the model
            file.save(file.name, file, save=False)
        return file