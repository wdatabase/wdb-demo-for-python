from typing import List
from pydantic import BaseModel
from src.comm import *


class TextInfo(BaseModel):
    uuid: str
    title: str
    content: str
    createTime: int
    updateTime: int

class TextReq(BaseModel):
    o: str
    uuid: str
    title: str
    content: str

class InfoRsp(BaseModel):
    code: int = 200
    msg: str = ''
    uuid: str = ''

class TextInfoRsp(BaseModel):
    code: int = 200
    msg: str = ''
    info: TextInfo

class TextListInfo(BaseModel):
    uuid: str
    title: str
    time: int

class TextListRsp(BaseModel):
    code: int = 200
    msg: str = ''
    total: int = 0
    list: List[TextListInfo] = []
        

class Text(Comm):
    async def text_post(self, req: TextReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return await self.rsp_nologin()
        
        tm = await self.ctime()
        if req.uuid == '':
            cuuid = await self.uuid()
            info = TextInfo(
                uuid = cuuid,
                title = req.title,
                content = req.content,
                createTime = tm,
                updateTime = tm
            )
            createRsp = await WDB.CreateObj(cuuid, info.model_dump_json(), ["my_text_" + uid])
            if createRsp['code'] != 200:
                logger.error(createRsp['msg'])
                return await self.rsp_err(createRsp['msg'])
            
            return await self.rsp_ok(cuuid)
        
        else:
            getInfoRsp = await WDB.GetObj(req.uuid)
            if getInfoRsp['code'] != 200:
                logger.error(getInfoRsp['msg'])
                return await self.rsp_err(getInfoRsp['msg'])
            
            info = TextInfo.model_validate_json(getInfoRsp['data'])
            info.title = req.title
            info.content = req.content
            info.updateTime = tm

            updateRsp = await WDB.UpdateObj(req.uuid, info.model_dump_json())
            if updateRsp['code'] != 200:
                logger.error(updateRsp['msg'])
                return await self.rsp_err(updateRsp['msg'])
            
            return await self.rsp_ok(info.uuid)

    async def text_info(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return self.rsp_nologin()
        
        infoRsp = await WDB.GetObj(uuid)
        if infoRsp['code'] != 200:
            logger.error(infoRsp['msg'])
            return await self.rsp_err(infoRsp['msg'])
        
        info = TextInfo.model_validate_json(infoRsp['data'])
        return TextInfoRsp(
            info = info
        )

    async def text_list(self, offset: int, limit: int, order: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return await self.rsp_nologin()
        
        category = "my_text_" + uid
        listRsp = await WDB.ListObj(category, offset, limit, order)
        if listRsp['code'] != 200:
            logger.error(listRsp['msg'])
            return await self.rsp_err(listRsp['msg'])
        
        total = listRsp['total']
        infos = []
        for item in listRsp['list']:
            info = TextInfo.model_validate_json(item)
            infos.append(TextListInfo(
                uuid = info.uuid,
                title = info.title,
                time = info.createTime
            ))
        return TextListRsp(
                total = total,
                list = infos
            )

    async def text_del(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return await self.rsp_nologin()
        
        delRsp = await WDB.DelObj(uuid)
        if delRsp['code'] != 200:
            logger.error(delRsp['msg'])
            return await self.rsp_err(delRsp['msg'])
        
        return await self.rsp_ok(uuid)
    
