# -*- coding: UTF-8 -*-


class ZipUtilities:
    zip_file = None

    def __init__(self):
        self.zip_file = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)

    def toZip(self, file_or_folder, name):
        if os.path.isfile(file_or_folder):
            file = file_or_folder
            self.zip_file.write(file, arcname=os.path.basename(file))
        else:
            folder = file_or_folder
            self.addFolderToZip(folder, name)

    def addFolderToZip(self, folder, name):
        for file in os.listdir(folder):
            full_path = os.path.join(folder, file)
            if os.path.isfile(full_path):
                self.zip_file.write(full_path, arcname=os.path.join(name, os.path.basename(full_path)))
            elif os.path.isdir(full_path):
                self.addFolderToZip(full_path, os.path.join(name, os.path.basename(full_path)))

    def close(self):
        if self.zip_file:
            self.zip_file.close()

# use_zip_file2 = None
# if __name__ == "__main__" and use_zip_file2:

#     import zipfile
#     import os
#     import zipstream

#     utilities = ZipUtilities()
#     for file_obj in file_objs:
#        tmp_dl_path = os.path.join(path_to, filename)
#        utilities.toZip(tmp_dl_path, filename)
#     #utilities.close()
#     response = StreamingHttpResponse(utilities.zip_file, content_type='application/zip')
#     response['Content-Disposition'] = 'attachment;filename="{0}"'.format("download.zip")
#     return response

import zipfile
import os

##############################################################
def gen_zip_with_zipfile(path_to_zip, target_filename):
    # import StringIO

    # s = StringIO.StringIO()
    f = None
    try:
        f = zipfile.ZipFile(target_filename, 'w' ,zipfile.ZIP_DEFLATED)
        # f = zipfile.ZipFile(s, 'w' ,zipfile.ZIP_DEFLATED)
        for root,dirs,files in os.walk(path_to_zip):
            for filename in files:
                f.write(os.path.join(root,filename))
            if  len(files) == 0:
                zif=zipfile.ZipInfo((root+'\\'))
                f.writestr(zif,"")
    except IOError, message:
        print message
        sys.exit(1)
    except OSError, message:
        print message
        sys.exit(1)
    except zipfile.BadZipfile, message:    
        print message
        sys.exit(1)
    finally: 
        # f.close()
        pass

    if zipfile.is_zipfile(f.filename):
        print "Successfully packing to: "+os.getcwd()+"\\"+ target_filename
    else:
        print "Packing failed"

    return f


use_zip_file = False
if use_zip_file:
    import zipfile
    import os 

    tmpPath = ".\\document"
    f = gen_zip_with_zipfile(tmpPath,'abcd.zip')
    # print f.namelist()
    # print f.fp
    f.close()


use_zip_file_tmpFile = False
if use_zip_file_tmpFile:
    import tempfile
    temp = tempfile.TemporaryFile() 
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) 
    src = ".\\document"
    files = os.listdir(src) 
    for filename in files: 
        archive.write(src+'/'+ filename, filename) 
    archive.close() 
    # wrapper = FileWrapper(temp) 
    # response = HttpResponse(wrapper, content_type='application/zip') 
    # response['Content-Disposition'] = 'attachment; filename=test.zip' 
    # response['Content-Length'] = temp.tell() 
    # temp.seek(0) 
    # return response 

##############################################################
use_zipstream = None
if use_zipstream:
    import zipstream
    z = zipstream.ZipFile()
    z.write('static\\css\\inspection.css')

    with open('zipfile.zip', 'wb') as f:
        for data in z:
            f.write(data)

##############################################################
use_zipstream1 = None
if use_zipstream1:
    from zipstream1 import ZipStream
    zf = open('zipfile.zip', 'wb')
    for data in ZipStream('static\\css\\inspection.css'):
        zf.write(data)
    zf.close()            