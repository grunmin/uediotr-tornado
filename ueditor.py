class ueditor(ApiHandler):

    @run_on_executor
    def saveFile(self,fileobj,baseDir,fname=None,isImage=True):
        username = self.acl_current_user()['name']
        import datetime

        uploadPath =username+ '/'+ datetime.datetime.utcnow().strftime("%Y%m%d") +'/'

        if not os.path.exists(baseDir+uploadPath):
            os.makedirs(baseDir+uploadPath)

        if fname==None:
            fname =(''.join(random.choice(string.ascii_uppercase) for i in range(10)))

            fname += os.path.splitext(fileobj["filename"])[1]
            if not os.path.exists(baseDir+uploadPath+fname):
                fp = open(baseDir+uploadPath+fname,'wb')
                fp.write(fileobj["body"])
                fp.close()
                result = {
                      "state": "SUCCESS",
                      "url": uploadPath +fname,
                      "title": fname,
                      "original": fileobj["filename"] ,
                    }
                self.appendFile(fileobj["filename"], uploadPath +fname,isImage=isImage)
                self.write(result)
                self.finish()
            # else:
            #      self.saveFile(baseDir=baseDir,fileobj=fileobj,isImage=isImage)

    @gen.coroutine
    @lib.web.is_login
    def get(self):
        action = self.get_argument("action")

        if  action == "config":
            self.write(ueditor_config)
            return
        elif action==ueditor_config["imageManagerActionName"]:
            start=int(self.get_argument('start'))
            size=int(self.get_argument('size'))
            urls, total = self.getList(start,size,isImage=True)
            result = {
                "state": "SUCCESS",
                "list": urls,
                "start": start ,
                "total": total
            }
            self.write(result)
            self.finish()
            return
        elif action==ueditor_config["fileManagerActionName"]:
            start=int(self.get_argument('start'))
            size=int(self.get_argument('size'))
            urls, total = self.getList(start,size,isImage=False)
            result = {
                "state": "SUCCESS",
                "list": urls,
                "start": start ,
                "total": total
            }
            self.write(result)
            self.finish()
            return

        self.finish()

    executor = ThreadPoolExecutor(6)
    @gen.coroutine
    @lib.web.is_login
    def post(self):

        if self.get_argument("action") == ueditor_config["imageActionName"]:
            for keys in self.request.files:
                for fileobj in self.request.files[keys]:
                    yield self.saveFile(baseDir=ueditor_config["imagePathFormat"] ,fileobj= fileobj)

        elif self.get_argument("action") ==ueditor_config["fileActionName"]:
            for keys in self.request.files:
                for fileobj in self.request.files[keys]:
                    yield self.saveFile( baseDir=ueditor_config["filePathFormat"] ,fileobj= fileobj,isImage=False)

    @lib.web.is_login
    def delete(self):
        path = self.get_argument('path', '')
        stype = self.get_argument('type', '')
        if path and stype:
            uploadModel = models.help.help_upload()
            fileName = uploadModel.find().where('[path] = %s and [type] = %s', path, stype).query()
            if fileName:
                if stype == 'image':
                    os.remove(ueditor_config["imagePathFormat"]+path)
                else:
                    os.remove(ueditor_config["filePathFormat"]+path)
                uploadModel.delete('[id] = %s', fileName['id'])
                json = {
                    'error': 0,
                    'msg': "删除成功"
                }
                self.write(json)
                return
            else:
                json = {
                    'error': 1,
                    'msg': "找不到文件"
                }
                self.write(json)
                return


    def getList(self,start=0,count=20,isImage=True):
        user = self.acl_current_user()
        ret = []
        total = 0
        uploadModel = models.help.help_upload()
        if isImage:
            cache = uploadModel.find().where('[username] = %s and [type] = "image"', user['name']).limit(start,count).query()
            total = uploadModel.find().where('[username] = %s and [type] = "image"', user['name']).count()
        else:
            cache = uploadModel.find().where('[username] = %s and [type] = "file"', user['name']).limit(start,count).query()
            total = uploadModel.find().where('[username] = %s and [type] = "file"', user['name']).count()
        if isImage:
            for i in cache:
                ret.append({"url":i['path'], 'original':i['original']})
        else:
            for i in cache:
                ret.append({"url":i['path'], 'original':i['original']})

        return (ret, total)

    def appendFile(self, original, fileName,isImage=True):
        user = self.acl_current_user()
        uploadModel = models.help.help_upload()
        uploadModel.attr = {}
        uploadModel.attr['username'] = user['name']
        uploadModel.attr['nickname'] = user['nickname']
        uploadModel.attr['original'] = original
        uploadModel.attr['path'] = fileName
        uploadModel.attr['upload_time'] = datetime.datetime.now().strftime("%Y-%m-%d %X")
        if isImage:
            uploadModel.attr['type'] = "image"
        else:
            uploadModel.attr['type'] = "file"
        uploadModel.add()

ueditor_config = {
    "imageDelUrl":"/ueditor",
    "fileDelUrl":"/ueditor",
    "imageActionName": "uploadimage", 
    "imageFieldName": "upfile", 
    "imageMaxSize": 2048000, 
    "imageAllowFiles": [".png", ".jpg", ".jpeg", ".gif", ".bmp"], 
    "imageCompressEnable": True, 
    "imageCompressBorder": 1600, 
    "imageInsertAlign": "none", 
    "imageUrlPrefix": "/assets/main/upload/image/", 
    "imagePathFormat": "assets/main/upload/image/", 

    "fileActionName": "uploadfile", 
    "fileFieldName": "upfile", 
    "filePathFormat": "assets/main/upload/file/", 
    "fileUrlPrefix": "/assets/main/upload/file/", 
    "fileMaxSize": 51200000, 
    "fileAllowFiles": [
        ".png", ".jpg", ".jpeg", ".gif", ".bmp",
        ".flv", ".swf", ".mkv", ".avi", ".rm", ".rmvb", ".mpeg", ".mpg",
        ".ogg", ".ogv", ".mov", ".wmv", ".mp4", ".webm", ".mp3", ".wav", ".mid",
        ".rar", ".zip", ".tar", ".gz", ".7z", ".bz2", ".cab", ".iso",
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".txt", ".md", ".xml"
    ], 

    "imageManagerActionName": "listimage", 
    "imageManagerListPath": "assets/main/upload/image/", 
    "imageManagerListSize": 20, 
    "imageManagerUrlPrefix": "/assets/main//upload/image/", 
    "imageManagerInsertAlign": "none", 
    "imageManagerAllowFiles": [".png", ".jpg", ".jpeg", ".gif", ".bmp"], 

    "fileManagerActionName": "listfile", 
    "fileManagerListPath": "assets/main/upload/file/", 
    "fileManagerUrlPrefix": "/assets/main//upload/file/", 
    "fileManagerListSize": 20, 
    "fileManagerAllowFiles": [
        ".png", ".jpg", ".jpeg", ".gif", ".bmp",
        ".flv", ".swf", ".mkv", ".avi", ".rm", ".rmvb", ".mpeg", ".mpg",
        ".ogg", ".ogv", ".mov", ".wmv", ".mp4", ".webm", ".mp3", ".wav", ".mid",
        ".rar", ".zip", ".tar", ".gz", ".7z", ".bz2", ".cab", ".iso",
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".txt", ".md", ".xml"
    ] 

}
handlers = [
    (r'/ueditor',ueditor),
]
