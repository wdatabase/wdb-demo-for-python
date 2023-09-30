from typing import List
from pydantic import BaseModel
import datetime
from src.comm import *
from fastapi import UploadFile, Response, Header


class FileInfo(BaseModel):
    uuid: str
    name: str
    fileName: str
    contentType: str
    size: int
    fileUuid: str
    createTime: int
    updateTime: int

class FileRsp(BaseModel):
    code: int = 200
    msg: str = ''
    uuid: str = ''

class FileInfoRsp(BaseModel):
    code: int = 200
    msg: str = ''
    info: FileInfo

class FileListInfo(BaseModel):
    uuid: str
    name: str
    fileName: str
    contentType: str
    size: int
    fileUuid: str
    time: int

class FileListRsp(BaseModel):
    code: int = 200
    msg: str = ''
    total: int = 0
    list: List[FileListInfo] = []


class File(Comm):
    async def file_post(self, file: UploadFile, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return  await self.rsp_nologin()
        
        tm = await self.ctime()
        fileUuid = await self.uuid()
        name = 'file'
        fileName = file.filename
        contentType = file.content_type
        body = await file.read()
        size = len(body)
        fileRsp = await WDB.CreateRawData(fileUuid, body, [])
        if fileRsp['code'] != 200:
            logger.error(fileRsp['msg'])
            return await self.rsp_err(fileRsp['msg'])
        
        if uuid == '':
            cuuid = await self.uuid()
            info = FileInfo(
                uuid = cuuid,
                name = name,
                fileName = fileName,
                contentType = contentType,
                size = size,
                fileUuid = fileUuid,
                createTime = tm,
                updateTime = tm
            )
            
            createRsp = await WDB.CreateObj(cuuid, info.model_dump_json(), ["my_file_" + uid])
            if createRsp['code'] != 200:
                logger.error(createRsp['msg'])
                return await self.rsp_err(createRsp['msg'])
            
            return await self.rsp_ok(cuuid)
        
        else:
            getInfoRsp = await WDB.GetObj(uuid)
            if getInfoRsp['code'] != 200:
                logger.error(getInfoRsp['msg'])
                return await self.rsp_err(getInfoRsp['msg'])
            
            info = FileInfo.model_validate_json(getInfoRsp['data'])
            info.name = name
            info.fileName = fileName
            info.contentType = contentType
            info.size = size
            info.fileUuid = fileUuid

            updateRsp = await WDB.UpdateObj(uuid, info.model_dump_json())
            if updateRsp['code'] != 200:
                logger.error(updateRsp['msg'])
                return await self.rsp_err(updateRsp['msg'])
            
            return await self.rsp_ok(info.uuid)

    async def file_info(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return self.rsp_nologin()
        
        infoRsp = await WDB.GetObj(uuid)
        if infoRsp['code'] != 200:
            logger.error(infoRsp['msg'])
            return await self.rsp_err(infoRsp['msg'])
        
        info = FileInfo.model_validate_json(infoRsp['data'])
        return FileInfoRsp(
            info = info
        )

    async def file_data(self, range: str = Header(None), uuid: str = '', o: str = ''):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return self.rsp_nologin()
        
        getInfoRsp = await WDB.GetObj(uuid)
        if getInfoRsp['code'] != 200:
            logger.error(getInfoRsp['msg'])
            return await self.rsp_err(getInfoRsp['msg'])
        
        info = FileInfo.model_validate_json(getInfoRsp['data'])

        headers = {}
        data = ''
        code = 200
        if range != None:
            code = 206
            arr = range[6:].split('-')
            start = int(arr[0])
            end = 0
            if arr[1] != '':
                end = int(arr[1])
            if end == 0:
                end = start + 1024 * 1024
            getRangeRsp = await WDB.GetRangeData(info.fileUuid, start, end - start)
            if getRangeRsp['code'] != 200:
                logger.error(getRangeRsp['msg'])
                return await self.rsp_err(getRangeRsp['msg'])
            
            size = getRangeRsp['all_size']
            if end > size:
                end = size - 1
            data = getRangeRsp['raw']
            headers['Content-Range'] = "bytes %d-%d/%d"%(start, end, size)
        else:
            getRawRsp = await WDB.GetRawData(info.fileUuid)
            if getRawRsp['code'] != 200:
                logger.error(getRawRsp['msg'])
                return await self.rsp_err(getRawRsp['msg'])
            
            data = getRawRsp['raw']
            headers['Accept-Range'] = "bytes"
            
        headers['Last-Modified'] = "%s"%(datetime.datetime.utcfromtimestamp(info.updateTime))
        headers['Etag'] = info.uuid

        headers['Content-Type'] = "application/octet-stream"
        headers['Content-Disposition'] = "attachment;filename=" + info.fileName

        return Response(
            headers = headers,
            content = data,
            status_code = code
        )

    async def file_list(self, offset: int, limit: int, order: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return  await self.rsp_nologin()
        
        category = "my_file_" + uid
        listRsp = await WDB.ListObj(category, offset, limit, order)
        if listRsp['code'] != 200:
            logger.error(listRsp['msg'])
            return await self.rsp_err(listRsp['msg'])
        
        total = listRsp['total']
        infos = []
        for item in listRsp['list']:
            info = FileInfo.model_validate_json(item)
            infos.append(FileListInfo(
                uuid = info.uuid,
                name = info.name,
                fileName = info.fileName,
                contentType = info.contentType,
                size = info.size,
                fileUuid = info.fileUuid,
                time = info.createTime
            ))
        return FileListRsp(
                total = total,
                list = infos
            )

    async def file_del(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return  await self.rsp_nologin()
        
        delRsp = await WDB.DelObj(uuid)
        if delRsp['code'] != 200:
            logger.error(delRsp['msg'])
            return await self.rsp_err(delRsp['msg'])
        
        return await self.rsp_ok(uuid)
    
