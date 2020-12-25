import qrcode
import os

def gen_qrcode(link, path_out):    
    qr=qrcode.QRCode(
         version = 2,
         error_correction = qrcode.constants.ERROR_CORRECT_L,
         box_size=10,
         border=10,)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image()
    #img.show()

    photopath = os.path.join(path_out) # settings.MEDIA_ROOT, "inspection"
    if not os.path.exists(photopath):
        os.makedirs(photopath)
    path = os.path.join(photopath, 'create.jpg')
    img.save(path)
    return path
