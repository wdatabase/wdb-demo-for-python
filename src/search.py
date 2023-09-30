from typing import List
from pydantic import BaseModel
from src.comm import *


class SearchInfo(BaseModel):
    uuid: str
    title: str
    score: float
    content: str
    createTime: int
    updateTime: int

class SearchReq(BaseModel):
    o: str
    uuid: str
    title: str
    score: float
    content: str

class SearchListReq(BaseModel):
    o: str
    title: str
    score: str
    begin: str
    end: str
    offset: int
    limit: int
    order: str
    
class SearchRsp(BaseModel):
    code: int = 200
    msg: str = ''
    uuid: str = ''

class SearchInfoRsp(BaseModel):
    code: int = 200
    msg: str = ''
    info: SearchInfo

class SearchListInfo(BaseModel):
    uuid: str
    title: str
    score: float
    time: int

class SearchListRsp(BaseModel):
    code: int = 200
    msg: str = ''
    total: int = 0
    list: List[SearchListInfo] = []
        

class Search(Comm):
    async def search_post(self, req: SearchReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return await self.rsp_nologin()

        tm = await self.ctime()
        index_keys = ["my_search_index_" + uid]
        index_raw = [
            "title:str:=" + req.title,
            "score:num:=" + str(req.score),
            "updateTime:num:=" + str(tm)
        ]

        if req.uuid == '':
            cuuid = await self.uuid()
            info = SearchInfo(
                uuid = cuuid,
                title = req.title,
                score = req.score,
                content = req.content,
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
            
            return SearchRsp(
                uuid = cuuid
            )
        else:
            getRsp = await WDB.GetObj(req.uuid)
            if getRsp['code'] != 200:
                logger.error(getRsp['msg'])
                return await self.rsp_err(getRsp['msg'])
            
            info = SearchInfo.model_validate_json(getRsp['data'])
            info.title = req.title
            info.score = req.score
            info.content = req.content
            info.updateTime = tm

            updateRsp = await WDB.UpdateObj(req.uuid, info.model_dump_json())
            if updateRsp['code'] != 200:
                logger.error(updateRsp['msg'])
                return await self.rsp_err(updateRsp['msg'])
            
            idxRsp = await WDB.UpdateIndex(index_keys, index_keys, req.uuid, index_raw)
            if idxRsp['code'] != 200:
                logger.error(idxRsp['msg'])
                return await self.rsp_err(idxRsp['msg'])
            
            return SearchRsp(
                uuid = info.uuid
            )

    async def search_info(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return self.rsp_nologin()
        
        getRsp = await WDB.GetObj(uuid)
        if getRsp['code'] != 200:
            logger.error(getRsp['msg'])
            return await self.rsp_err(getRsp['msg'])
        
        info = SearchInfo.model_validate_json(getRsp['data'])
        return SearchInfoRsp(
            info = info
        )

    async def search_list(self, req: SearchListReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return await self.rsp_nologin()
        
        arr = []
        if req.title != '':
            arr.append("[\"title\",\"reg\",\"^%s.*$\"]"%(req.title))
            
        if req.score != '':
            arr.append("[\"score\",\">=\",%s]"%(req.score))
            
        if req.begin != '' and req.end != '':
            stimeArray = time.strptime(req.begin, "%Y-%m-%d %H:%M")
            st = int(time.mktime(stimeArray))
            etimeArray = time.strptime(req.end, "%Y-%m-%d %H:%M")
            et = int(time.mktime(etimeArray))
            arr.append("[\"updateTime\",\">=\",%d,\"<=\",%d]"%(st, et))

        condition = ""
        if len(arr) == 1:
            condition = arr[0]
        if len(arr) == 2:
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

        indexkey = "my_search_index_" + uid
        listRsp = await WDB.ListIndex(indexkey, condition, req.offset, req.limit, order)
        if listRsp['code'] != 200:
            logger.error(listRsp['msg'])
            return await self.rsp_err(listRsp['msg'])
        
        total = listRsp['total']
        infos = []
        for item in listRsp['list']:
            info = SearchInfo.model_validate_json(item)
            infos.append(SearchListInfo(
                uuid = info.uuid,
                title = info.title,
                score = info.score,
                time = info.createTime
            ))
        return SearchListRsp(
                total = total,
                list = infos
            )

    async def search_del(self, uuid: str, o: str):
        (is_login, uid) = await self.auth(o)
        if not is_login:
            return await self.rsp_nologin()
        
        delRsp = await WDB.DelObj(uuid)
        if delRsp['code'] != 200:
            logger.error(delRsp['msg'])
            return await self.rsp_err(delRsp['msg'])
        
        index_key = ["my_search_index_" + uid]
        idxRsp = await WDB.DelIndex(index_key, uuid)
        if idxRsp['code'] != 200:
            logger.error(idxRsp['msg'])
            return await self.rsp_err(idxRsp['msg'])
        
        return await self.rsp_ok(uuid)
    
