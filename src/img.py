from typing import List
from pydantic import BaseModel
import base64
from src.comm import *
from fastapi import UploadFile, Response


class ImgInfo(BaseModel):
    uuid: str
    name: str
    fileName: str
    contentType: str
    size: int
    fileUuid: str
    createTime: int
    updateTime: int

class ImgRsp(BaseModel):
    code: int = 200
    msg: str = ''
    uuid: str = ''

class ImgInfoRsp(BaseModel):
    code: int = 200
    msg: str = ''
    info: ImgInfo

class ImgListInfo(BaseModel):
    uuid: str
    name: str
    fileName: str
    contentType: str
    size: int
    fileUuid: str
    time: int

class ImgListRsp(BaseModel):
    code: int = 200
    msg: str = ''
    total: int = 0
    list: List[ImgListInfo] = []


class ImgRaw(BaseModel):
    raw: str

class Img(Comm):
    async def img_post(self, img: UploadFile, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return  await self.rsp_nologin()
        
        tm = await self.ctime()
        fileUuid = await self.uuid()
        name = 'img'
        fileName = img.filename
        contentType = img.content_type
        body = await img.read()
        size = len(body)
        data = base64.b64encode(body).decode('utf-8')
        img_raw = ImgRaw(raw = data)
        fileRsp = await WDB.CreateObj(fileUuid, img_raw.model_dump_json(), [])
        if fileRsp['code'] != 200:
            logger.error(fileRsp['msg'])
            return await self.rsp_err(fileRsp['msg'])
        
        if uuid == '':
            cuuid = await self.uuid()
            info = ImgInfo(
                uuid = cuuid,
                name = name,
                fileName = fileName,
                contentType = contentType,
                size = size,
                fileUuid = fileUuid,
                createTime = tm,
                updateTime = tm
            )
            
            createRsp = await WDB.CreateObj(cuuid, info.model_dump_json(), ["my_img_" + uid])
            if createRsp['code'] != 200:
                logger.error(createRsp['msg'])
                return await self.rsp_err(createRsp['msg'])
            
            return await self.rsp_ok(cuuid)
        
        else:
            getInfoRsp = await WDB.GetObj(uuid)
            if getInfoRsp['code'] != 200:
                logger.error(getInfoRsp['msg'])
                return await self.rsp_err(getInfoRsp['msg'])
            
            info = ImgInfo.model_validate_json(getInfoRsp['data'])
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

    async def img_info(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return self.rsp_nologin()
        
        infoRsp = await WDB.GetObj(uuid)
        if infoRsp['code'] != 200:
            logger.error(infoRsp['msg'])
            return await self.rsp_err(infoRsp['msg'])
        
        info = ImgInfo.model_validate_json(infoRsp['data'])
        return ImgInfoRsp(
            info = info
        )

    async def img_data(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return self.rsp_nologin()
        
        getInfoRsp = await WDB.GetObj(uuid)
        if getInfoRsp['code'] != 200:
            logger.error(getInfoRsp['msg'])
            return await self.rsp_err(getInfoRsp['msg'])
        
        info = ImgInfo.model_validate_json(getInfoRsp['data'])
        
        fileRsp = await WDB.GetObj(info.fileUuid)
        if fileRsp['code'] != 200:
            logger.error(fileRsp['msg'])
            return await self.rsp_err(fileRsp['msg'])
        
        img_raw = ImgRaw.model_validate_json(fileRsp['data'])
        raw = base64.b64decode(img_raw.raw)
        return Response(
            content = raw, 
            media_type = info.contentType
        )

    async def img_list(self, offset: int, limit: int, order: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return  await self.rsp_nologin()
        
        category = "my_img_" + uid
        listRsp = await WDB.ListObj(category, offset, limit, order)
        if listRsp['code'] != 200:
            logger.error(listRsp['msg'])
            return await self.rsp_err(listRsp['msg'])
        
        total = listRsp['total']
        infos = []
        for item in listRsp['list']:
            info = ImgInfo.model_validate_json(item)
            infos.append(ImgListInfo(
                uuid = info.uuid,
                name = info.name,
                fileName = info.fileName,
                contentType = info.contentType,
                size = info.size,
                fileUuid = info.fileUuid,
                time = info.createTime
            ))
        return ImgListRsp(
                total = total,
                list = infos
            )

    async def img_del(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return  await self.rsp_nologin()
        
        delRsp = await WDB.DelObj(uuid)
        if delRsp['code'] != 200:
            logger.error(delRsp['msg'])
            return await self.rsp_err(delRsp['msg'])
        
        return await self.rsp_ok(uuid)
    
