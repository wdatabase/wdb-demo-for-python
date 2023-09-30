from pydantic import BaseModel
from src.comm import *


class ShopInfo(BaseModel):
    uuid: str
    uid: str
    balance: float
    point: float
    createTime: int
    updateTime: int
    
class ShopBalanceLog(BaseModel):
    uuid: str
    uid: str
    balance: float
    op: str
    createTime: int
    updateTime: int

class BalanceReq(BaseModel):
    o: str
    balance: float

class ShopInfoRsp(BaseModel):
    code: int = 200
    msg: str = ''
    info: ShopInfo
        

class ShopToInfo(Comm):
    async def shop_balance(self, req: BalanceReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return await self.rsp_nologin()
            
        key = "shop_info_" + uid
        tm = await self.ctime()
        
        tsBeginRsp = await WDB.TransBegin([key])
        tsid = ''
        if tsBeginRsp['code'] == 200:
            tsid = tsBeginRsp['data']
        else:
            logger.error(tsBeginRsp['msg'])
            return await self.rsp_err(tsBeginRsp['msg'])
        
        logid = await self.uuid()
        balancelog = ShopBalanceLog(
            uuid = logid,
            uid = uid,
            balance = req.balance,
            op = "in",
            createTime = tm,
            updateTime = tm
        )
        logRsp = await WDB.TransCreateObj(tsid, logid, balancelog.model_dump_json(), ["shop_balance_log_" + uid])
        if logRsp['code'] != 200:
            await WDB.TransRollBack(tsid)
            logger.error(logRsp['msg'])
            return await self.rsp_err(logRsp['msg'])
        
        shopInfoRsp = await WDB.TransGet(tsid, key)
        if shopInfoRsp['code'] != 200:
            await WDB.TransRollBack(tsid)
            logger.error(shopInfoRsp['msg'])
            return await self.rsp_err(shopInfoRsp['msg'])
        shopInfo = ShopInfo.model_validate_json(shopInfoRsp['data'])
        
        shopInfo.balance = shopInfo.balance + req.balance
        shopInfo.updateTime = tm
        updateInfoRsp = await WDB.TransUpdateObj(tsid, key, shopInfo.model_dump_json())
        if updateInfoRsp['code'] != 200:
            await WDB.TransRollBack(tsid)
            logger.error(updateInfoRsp['msg'])
            return await self.rsp_err(updateInfoRsp['msg'])
        
        commitRsp = await WDB.TransCommit(tsid)
        if commitRsp['code'] != 200:
            await WDB.TransRollBack(tsid)
            logger.error(commitRsp['msg'])
            return await self.rsp_err(commitRsp['msg'])
        
        return await self.rsp_ok(shopInfo.uuid)

    async def shop_info(self, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return await self.rsp_nologin()
        
        key = "shop_info_" + uid
        infoRsp = await WDB.GetObj(key)
        if infoRsp['code'] != 200:
            if infoRsp['msg'] == "not found key":
                cuuid = await self.uuid()
                tm = await self.ctime()
                
                shopInfo = ShopInfo(
                    uuid = cuuid,
                    uid = uid,
                    balance = 0.0,
                    point = 0.0,
                    createTime = tm,
                    updateTime = tm
                )
                createRsp = await WDB.CreateObj(key, shopInfo.model_dump_json(), [])
                if createRsp['code'] != 200:
                    logger.error(createRsp['msg'])
                    return await self.rsp_err(createRsp['msg'])
                return ShopInfoRsp(
                    info = shopInfo
                )
            else:
                logger.error(infoRsp['msg'])
                return await self.rsp_err(infoRsp['msg'])
        
        shopInfo = ShopInfo.model_validate_json(infoRsp['data'])
        return ShopInfoRsp(
            info = shopInfo
        )
        