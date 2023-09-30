from pydantic import BaseModel
from src.comm import *

class BigReq(BaseModel):
    o: str
    key: str
    path: str
        

class BigFile(Comm):
    async def big_upload(self, req: BigReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return await self.rsp_nologin()
            
        uploadRsp = await WDB.UploadByPath(req.path, req.key, [])
        if uploadRsp['code'] != 200:
            logger.error(uploadRsp['msg'])
            return await self.rsp_err(uploadRsp['msg'])
        
        return await self.rsp_ok("")
    
    async def big_down(self, req: BigReq):
        (is_login, uid) = await self.auth(req.o)
        if not is_login:
            return await self.rsp_nologin()
            
        downRsp = await WDB.DownToPath(req.path, req.key)
        if downRsp['code'] != 200:
            logger.error(downRsp['msg'])
            return await self.rsp_err(downRsp['msg'])
        
        return await self.rsp_ok("")
