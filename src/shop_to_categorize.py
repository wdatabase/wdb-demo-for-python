from typing import List
from pydantic import BaseModel
from src.comm import *


class ShopCategorizeInfo(BaseModel):
    uuid: str
    name: str
    sort: int
    createTime: int
    updateTime: int
    
class ShopCategorizeInfoRsp(BaseModel):
    code: int = 200
    msg: str = ''
    info: ShopCategorizeInfo
    
class ShopCategorizeReq(BaseModel):
    o: str
    uuid: str
    name: str
    sort: int
    
class ShopCategorizeListReq(BaseModel):
    o: str
    offset: int
    limit: int
    order: str
    
class ShopCategorizeListInfo(BaseModel):
    uuid: str
    name: str
    sort: int

class ShopCategorizeListRsp(BaseModel):
    code: int = 200
    msg: str = ''
    total: int = 0
    list: List[ShopCategorizeListInfo]
        

class ShopToCategorize(Comm):
    async def shop_categorize_post(self, req: ShopCategorizeReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return await self.rsp_nologin()
            
        tm = await self.ctime()
        if req.uuid == '':
            cuuid = await self.uuid()
            info = ShopCategorizeInfo(
                uuid = cuuid,
                name = req.name,
                sort = req.sort,
                createTime = tm,
                updateTime = tm
            )
            createRsp = await WDB.CreateObj(cuuid, info.model_dump_json(), ["shop_categorize_" + uid])
            if createRsp['code'] != 200:
                logger.error(createRsp['msg'])
                return await self.rsp_err(createRsp['msg'])
            
            return await self.rsp_ok(cuuid)
        
        else:
            infoRsp = await WDB.GetObj(req.uuid)
            if infoRsp['code'] != 200:
                logger.error(infoRsp['msg'])
                return await self.rsp_err(infoRsp['msg'])
            
            info = ShopCategorizeInfo.model_validate_json(infoRsp['data'])
            info.name = req.name
            info.sort = req.sort
            info.updateTime = tm

            updateRsp = await WDB.UpdateObj(req.uuid, info.model_dump_json())
            if updateRsp['code'] != 200:
                logger.error(updateRsp['msg'])
                return await self.rsp_err(updateRsp['msg'])

            return await self.rsp_ok(info.uuid)

    async def shop_categorize_info(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return await self.rsp_nologin()
        
        infoRsp = await WDB.GetObj(uuid)
        if infoRsp['code'] != 200:
                logger.error(infoRsp['msg'])
                return await self.rsp_err(infoRsp['msg'])
        
        shopInfo = ShopCategorizeInfo.model_validate_json(infoRsp['data'])
        return ShopCategorizeInfoRsp(
            info = shopInfo
        )
        
    async def shop_categorize_list(self, req: ShopCategorizeListReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return  await self.rsp_nologin()
        
        category = "shop_categorize_" + uid
        listRsp = await WDB.ListObj(category, req.offset, req.limit, req.order)
        if listRsp['code'] != 200:
            logger.error(listRsp['msg'])
            return await self.rsp_err(listRsp['msg'])
            
        total = listRsp['total']
        infos = []
        for item in listRsp['list']:
            info = ShopCategorizeInfo.model_validate_json(item)
            infos.append(ShopCategorizeListInfo(
                uuid = info.uuid,
                name = info.name,
                sort = info.sort
            ))
            
        infos.sort(key = lambda x: x.sort)
            
        return ShopCategorizeListRsp(
                total = total,
                list = infos
            )

    async def shop_categorize_del(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return await self.rsp_nologin()
        
        delRsp = await WDB.DelObj(uuid)
        if delRsp['code'] != 200:
            logger.error(delRsp['msg'])
            return await self.rsp_err(delRsp['msg'])
        
        return await self.rsp_ok(uuid)
    