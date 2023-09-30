from typing import List
from pydantic import BaseModel
from src.comm import *
from src.img import *
import base64
from fastapi import UploadFile, Response


class ShopProInfo(BaseModel):
    uuid: str
    title: str
    price: float
    weight: float
    inventory: int
    tps: List[str]
    imgid: str
    createTime: int
    updateTime: int
    
class ShopProInfoRsp(BaseModel):
    code: int = 200
    msg: str = ''
    info: ShopProInfo
    
class ShopProReq(BaseModel):
    o: str
    uuid: str
    title: str
    price: float
    weight: float
    inventory: int
    tps: List[str]
    imgid: str
    
class ShopProListReq(BaseModel):
    o: str
    indexkey: str
    titlekey: str
    begin: str
    end: str
    offset: int
    limit: int
    order: str

class ShopProListRsp(BaseModel):
    code: int = 200
    msg: str = ''
    total: int = 0
    list: List[ShopProInfo]
        

class ShopToPro(Comm):
    async def shop_pro_post(self, req: ShopProReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return await self.rsp_nologin()
            
        tm = await self.ctime()
        index_keys = []
        for ctp in req.tps:
            index_keys.append("shop_pro_tp_" + ctp)
        index_keys.append("all_shop_pro_tp_" + uid)
        index_raw = [
            "title:str:=" + req.title,
            "price:num:=" + str(req.price),
            "weight:num:=" + str(req.weight),
            "updateTime:num:=" + str(tm)
        ]
        
        if req.uuid == '':
            cuuid = await self.uuid()
            info = ShopProInfo(
                uuid = cuuid,
                title = req.title,
                price = req.price,
                weight = req.weight,
                inventory = req.inventory,
                tps = req.tps,
                imgid = req.imgid,
                createTime = tm,
                updateTime = tm
            )
            createRsp = await WDB.CreateObj(cuuid, info.model_dump_json(), [])
            if createRsp['code'] != 200:
                logger.error(createRsp['msg'])
                return await self.rsp_err(createRsp['msg'])
            
            idxRsp = await WDB.CreateIndex(index_keys, cuuid, index_raw)
            if idxRsp['code'] != 200:
                logger.error(idxRsp['msg'])
                return await self.rsp_err(idxRsp['msg'])
            
            return await self.rsp_ok(cuuid)
        
        else:
            infoRsp = await WDB.GetObj(req.uuid)
            if infoRsp['code'] != 200:
                logger.error(infoRsp['msg'])
                return await self.rsp_err(infoRsp['msg'])
            
            info = ShopProInfo.model_validate_json(infoRsp['data'])
            info.title = req.title
            info.price = req.price
            info.weight = req.weight
            info.inventory = req.inventory
            info.tps = req.tps
            info.imgid = req.imgid
            info.updateTime = tm

            updateRsp = await WDB.UpdateObj(req.uuid, info.model_dump_json())
            if updateRsp['code'] != 200:
                logger.error(updateRsp['msg'])
                return await self.rsp_err(updateRsp['msg'])
            
            updateIdxRsp = await WDB.UpdateIndex(index_keys, index_keys, req.uuid, index_raw)
            if updateIdxRsp['code'] != 200:
                logger.error(updateIdxRsp['msg'])
                return await self.rsp_err(updateIdxRsp['msg'])

            return await self.rsp_ok(info.uuid)

    async def shop_pro_info(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return await self.rsp_nologin()
        
        infoRsp = await WDB.GetObj(uuid)
        if infoRsp['code'] != 200:
                logger.error(infoRsp['msg'])
                return await self.rsp_err(infoRsp['msg'])
        
        shopInfo = ShopProInfo.model_validate_json(infoRsp['data'])
        return ShopProInfoRsp(
            info = shopInfo
        )
        
    async def shop_pro_list(self, req: ShopProListReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return  await self.rsp_nologin()
        
        indexkey = req.indexkey
        if indexkey == 'all':
            indexkey = "all_shop_pro_tp_" + uid
        else:
            indexkey = "shop_pro_tp_" + indexkey
        
        arr = []
        if req.titlekey != '':
            arr.append("[\"title\",\"reg\",\"^.*%s.*$\"]"%(req.titlekey))
        if req.begin != '' and req.end == '':
            arr.append("[\"updateTime\",\">=\",%s]"%(req.begin))
        if req.begin == '' and req.end != '':
            arr.append("[\"updateTime\",\"<=\",%s]"%(req.end))
        if req.begin != '' and req.end != '':
            arr.append("[\"updateTime\",\">=\",%s,\"<=\",%s]"%(req.begin, req.end))

        condition = ""
        if len(arr) == 1:
            condition = arr[0]
        if len(arr) > 1:
            condition = "{\"and\":[%s]}"%(",".join(arr))             
            
        order = "updateTime DESC"
        if req.order == "tasc":
            order = "updateTime ASC"
        elif req.order == "tdesc":
            order = "updateTime DESC"
        elif req.order == "sasc":
            order = "score ASC"
        elif req.order == "sdesc":
            order = "score DESC"

        listRsp = await WDB.ListIndex(indexkey, condition, req.offset, req.limit, order)
        if listRsp['code'] != 200:
            logger.error(listRsp['msg'])
            return await self.rsp_err(listRsp['msg'])
        
        total = listRsp['total']
        infos = []
        for item in listRsp['list']:
            info = ShopProInfo.model_validate_json(item)
            infos.append(info)

        return ShopProListRsp(
                total = total,
                list = infos
            )

    async def shop_pro_del(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return await self.rsp_nologin()
        
        delRsp = await WDB.DelObj(uuid)
        if delRsp['code'] != 200:
            logger.error(delRsp['msg'])
            return await self.rsp_err(delRsp['msg'])
        
        return await self.rsp_ok(uuid)
    
    async def shop_pro_img_post(self, img: UploadFile, o: str):
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
        
        infoRsp = await WDB.CreateObj(cuuid, info.model_dump_json(), [])
        if infoRsp['code'] != 200:
            logger.error(infoRsp['msg'])
            return await self.rsp_err(infoRsp['msg'])
        
        return await self.rsp_ok(cuuid)
    
    async def shop_pro_img_data(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return self.rsp_nologin()
        
        infoRsp = await WDB.GetObj(uuid)
        if infoRsp['code'] != 200:
            logger.error(infoRsp['msg'])
            return await self.rsp_err(infoRsp['msg'])
        
        info = ImgInfo.model_validate_json(infoRsp['data'])
        rawRsp = await WDB.GetObj(info.fileUuid)
        if rawRsp['code'] != 200:
            logger.error(rawRsp['msg'])
            return await self.rsp_err(rawRsp['msg'])
        
        img_raw = ImgRaw.model_validate_json(rawRsp['data'])
        raw = base64.b64decode(img_raw.raw)
        return Response(
            content = raw, 
            media_type = info.contentType
        )
