from typing import List
from pydantic import BaseModel
from src.comm import *
from src.shop_to_pro import *


class ShopCartInfo(BaseModel):
    uuid: str
    uid: str
    ids: List[str]
    nums: List[int]
    createTime: int
    updateTime: int

class ShopCartListInfo(BaseModel):
    proid: str
    title: str
    price: float
    inventory: int
    imgid: str
    num: int
 
class ShopCartListRsp(BaseModel):
    code: int = 200
    msg: str = ''
    total: float = 0.0
    listinfo: List[ShopCartListInfo]
    
class CartReq(BaseModel):
    o: str
    uuid: str
    num: int

class ShopCartInfoRsp(BaseModel):
    code: int = 200
    msg: str = ''
    info: ShopCartInfo
        

class ShopToCart(Comm):
    async def shop_cart_add(self, req: CartReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return await self.rsp_nologin()
            
        key = "shop_cart_" + uid
        tm = await self.ctime()
        
        infoRsp = await WDB.GetObj(key)
        if infoRsp['code'] != 200:
            if infoRsp['msg'] == "not found key":
                cuuid = await self.uuid()
                cartInfo = ShopCartInfo(
                    uuid = cuuid,
                    uid = uid,
                    ids = [req.uuid],
                    nums = [req.num],
                    createTime = tm,
                    updateTime = tm
                )
                
                createRsp = await WDB.CreateObj(key, cartInfo.model_dump_json(), [])
                if createRsp['code'] != 200:
                    logger.error(createRsp['msg'])
                    return await self.rsp_err(createRsp['msg'])
                return await self.rsp_ok(cuuid)
            else:
                logger.error(infoRsp['msg'])
                return await self.rsp_err(infoRsp['msg'])
            
        cartInfo = ShopCartInfo.model_validate_json(infoRsp['data'])
       
        if req.uuid in cartInfo.ids:
            idx = cartInfo.ids.index(req.uuid)
            cartInfo.nums[idx] = req.num
        else:
            cartInfo.ids.append(req.uuid)
            cartInfo.nums.append(req.num)
            
        updateCarInfo = await WDB.UpdateObj(key, cartInfo.model_dump_json())
        if updateCarInfo['code'] != 200:
            logger.error(updateCarInfo['msg'])
            return await self.rsp_err(updateCarInfo['msg'])
        
        return ShopCartInfoRsp(
            info = cartInfo
        )

    async def shop_cart_list(self, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return await self.rsp_nologin()
        
        key = "shop_cart_" + uid
        infoRsp = await WDB.GetObj(key)
        if infoRsp['code'] != 200:
            logger.error(infoRsp['msg'])
            return await self.rsp_err(infoRsp['msg'])
        
        cartInfo = ShopCartInfo.model_validate_json(infoRsp['data'])
        plist = []
        cidx = 0
        total = 0.0
        for proid in cartInfo.ids:
            cnum = cartInfo.nums[cidx]
            proRsp = await WDB.GetObj(proid)
            if proRsp['code'] != 200:
                logger.error(proRsp['msg'])
                return await self.rsp_err(proRsp['msg'])
            proInfo = ShopProInfo.model_validate_json(proRsp['data'])
            total += proInfo.price * float(cnum)
            plist.append(ShopCartListInfo(
                proid = proInfo.uuid,
                title = proInfo.title,
                price = proInfo.price,
                inventory = proInfo.inventory,
                imgid = proInfo.imgid,
                num = cnum
            ))
            cidx += 1
        
        return ShopCartListRsp(
            total = total,
            listinfo = plist
        )
        
    async def shop_cart_del(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return await self.rsp_nologin()
        
        key = "shop_cart_" + uid
        infoRsp = await WDB.GetObj(key)
        if infoRsp['code'] != 200:
            logger.error(infoRsp['msg'])
            return await self.rsp_err(infoRsp['msg'])
        cartInfo = ShopCartInfo.model_validate_json(infoRsp['data'])
        
        if uuid == 'all':
            cartInfo.ids = []
            cartInfo.nums = []
        else:
            idx = cartInfo.ids.index(uuid)
            del cartInfo.ids[idx]
            del cartInfo.nums[idx]
        
        updateRsp = await WDB.UpdateObj(key, cartInfo.model_dump_json())
        if updateRsp['code'] != 200:
            logger.error(updateRsp['msg'])
            return await self.rsp_err(updateRsp['msg'])
        
        return await self.rsp_ok(uuid)
    
        