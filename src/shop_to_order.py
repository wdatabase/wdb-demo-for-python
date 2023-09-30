from typing import List
from pydantic import BaseModel
from src.comm import *
from src.shop_to_info import *
from src.shop_to_pro import *
import copy


class ShopOrderInfo(BaseModel):
    uuid: str
    title: str
    imgid: str
    total: float
    ids: List[str]
    nums: List[int]
    prices: List[float]
    createTime: int
    updateTime: int
    
class ShopOrderItem(BaseModel):
    uuid: str
    title: str
    imgid: str
    price: float
    num: int
    createTime: int
    updateTime: int

class ShopOrderItemRsp(BaseModel):
    code: int = 200
    msg: str = ''
    list: List[ShopOrderItem] = []
    
class ShopOrderListRsp(BaseModel):
    code: int = 200
    msg: str = ''
    total: int = 0
    list: List[ShopOrderInfo] = []
    
class OrderReq(BaseModel):
    o: str
    total: float
    ids: List[str]
    nums: List[int]
    prices: List[float]

class ShopOrderListReq(BaseModel):
    o: str
    titlekey: str
    offset: int
    limit: int
    order: str
    
class ShopToOrder(Comm):
    async def shop_order_create(self, req: OrderReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return await self.rsp_nologin()

        tm = await self.ctime()
        req_ids = req.ids
        req_nums = req.nums
        req_prices = req.prices
        
        lock_ids = copy.deepcopy(req_ids)
        shop_info_key = "shop_info_" + uid
        lock_ids.append(shop_info_key)
        
        #开始事务
        tsBeginRsp = await WDB.TransBegin(lock_ids)
        tsid = ''
        if tsBeginRsp['code'] == 200:
            tsid = tsBeginRsp['data']
        else:
            logger.error(tsBeginRsp['msg'])
            return await self.rsp_err(tsBeginRsp['msg'])
        
        #校验余额
        shopInfoRsp = await WDB.TransGet(tsid, shop_info_key)
        if shopInfoRsp['code'] != 200:
            await WDB.TransRollBack(tsid)
            logger.error(shopInfoRsp['msg'])
            return await self.rsp_err(shopInfoRsp['msg'])
        shopInfo = ShopInfo.model_validate_json(shopInfoRsp['data'])
        
        dif = await self.floatcmp(shopInfo.balance, req.total)
        if dif == -1:
            await WDB.TransRollBack(tsid)
            logger.error("余额不足")
            return await self.rsp_err("余额不足")
        
        orderid = await self.uuid()
        imgid = ""
        title_list = []
        category_item = "shop_order_item_" + orderid
        
        #遍历购物车相关商品
        for idx in range(len(req_ids)):
            ckey = req_ids[idx]
            cnum = req_nums[idx]
            cprice = req_prices[idx]
            
            proRsp = await WDB.TransGet(tsid, ckey)
            if proRsp['code'] != 200:
                await WDB.TransRollBack(tsid)
                logger.error(proRsp['msg'])
                return await self.rsp_err(proRsp['msg'])
            proInfo = ShopProInfo.model_validate_json(proRsp['data'])
            
            #校验价格
            difp = await self.floatcmp(proInfo.price, cprice)
            if difp != 0:
                await WDB.TransRollBack(tsid)
                logger.error('商品价格变动，请重新确认。')
                return await self.rsp_err('商品价格变动，请重新确认。')
            
            #校验库存
            if cnum > proInfo.inventory:
                await WDB.TransRollBack(tsid)
                logger.error('库存不足。')
                return await self.rsp_err('库存不足。')
            
            title_list.append(proInfo.title)
            imgid = proInfo.imgid
            
            #保存订单产品详情
            itemid = await self.uuid()
            orderItem = ShopOrderItem(
                uuid = itemid,
                title = proInfo.title,
                imgid = proInfo.imgid,
                num = cnum,
                price = cprice,
                updateTime = tm,
                createTime = tm
            )
            itemRsp = await WDB.TransCreateObj(tsid, itemid, orderItem.model_dump_json(), [category_item])
            if itemRsp['code'] != 200:
                await WDB.TransRollBack(tsid)
                logger.error(itemRsp['msg'])
                return await self.rsp_err(itemRsp['msg'])
            
            #减库存
            proInfo.inventory = proInfo.inventory - cnum
            updateProInfo = await WDB.TransUpdateObj(tsid, proInfo.uuid, proInfo.model_dump_json())
            if updateProInfo['code'] != 200:
                await WDB.TransRollBack(tsid)
                logger.error(updateProInfo['msg'])
                return await self.rsp_err(updateProInfo['msg'])
            
        titles = "/".join(title_list)
        
        #保存订单信息
        orderInfo = ShopOrderInfo(
            uuid = orderid,
            title = titles,
            imgid = imgid,
            total = req.total,
            ids = req_ids,
            nums = req_nums,
            prices = req_prices,
            createTime = tm,
            updateTime = tm
        )
        orderRsp = await WDB.TransCreateObj(tsid, orderid, orderInfo.model_dump_json(), [])
        if orderRsp['code'] != 200:
            await WDB.TransRollBack(tsid)
            logger.error(orderRsp['msg'])
            return await self.rsp_err(orderRsp['msg'])
        
        #更新余额积分
        shopInfo.balance = shopInfo.balance - orderInfo.total
        shopInfo.point = shopInfo.point + orderInfo.total
        updateInfoRsp = await WDB.TransUpdateObj(tsid, shop_info_key, shopInfo.model_dump_json())
        if updateInfoRsp['code'] != 200:
            await WDB.TransRollBack(tsid)
            logger.error(updateInfoRsp['msg'])
            return await self.rsp_err(updateInfoRsp['msg'])
        
        #创建索引
        index_keys = ["shop_order_index_" + uid]
        index_raw = [
            "title:str:=" + orderInfo.title,
            "total:num:=" + str(orderInfo.total),
            "updateTime:num:=" + str(orderInfo.updateTime)
        ]
        idxRsp = await WDB.CreateIndex(index_keys, orderid, index_raw)
        if idxRsp['code'] != 200:
            await WDB.TransRollBack(tsid)
            logger.error(idxRsp['msg'])
            return await self.rsp_err(idxRsp['msg'])
        
        #提交事务
        commitRsp = await WDB.TransCommit(tsid)
        if commitRsp['code'] != 200:
            await WDB.TransRollBack(tsid)
            logger.error(commitRsp['msg'])
            return await self.rsp_err(commitRsp['msg'])
        
        return await self.rsp_ok(orderid)

    async def shop_order_info(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return await self.rsp_nologin()
        
        category = "shop_order_item_" + uuid
        listRsp = await WDB.ListObj(category, 0, 100, 'ASC')
        if listRsp['code'] != 200:
            logger.error(listRsp['msg'])
            return await self.rsp_err(listRsp['msg'])
        
        itemList = []
        for item in listRsp['list']:
            orderItem = ShopOrderItem.model_validate_json(item)
            itemList.append(orderItem)
        
        return ShopOrderItemRsp(
            list = itemList
        )
        
    async def shop_order_list(self, req: ShopOrderListReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return await self.rsp_nologin()
        
        arr = []
        if req.titlekey != '':
            arr.append("[\"title\",\"reg\",\"^.*%s.*$\"]"%(req.titlekey))

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
            order = "total ASC"
        elif req.order == "sdesc":
            order = "total DESC"

        indexkey = "shop_order_index_" + uid
        listRsp = await WDB.ListIndex(indexkey, condition, req.offset, req.limit, order)
        if listRsp['code'] != 200:
            logger.error(listRsp['msg'])
            return await self.rsp_err(listRsp['msg'])
        
        total = listRsp['total']
        infos = []
        for item in listRsp['list']:
            info = ShopOrderInfo.model_validate_json(item)
            infos.append(info)

        return ShopOrderListRsp(
                total = total,
                list = infos
            )
        
        