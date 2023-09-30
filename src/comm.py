import uuid
import hashlib
import time
import logging
from WdbDrive import Wdb
from pydantic import BaseModel


WDB = Wdb("http://127.0.0.1:8000", "key")

logger = logging.getLogger(__name__)

class Comm:
    async def uuid(self):
        return str(uuid.uuid4())

    async def hash(self, text: str):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    async def sign(self, uid: str, tm: int):
        return await self.hash('wdb_dfgrDR43d_' + uid + '_' + str(tm))

    async def ctime(self):
        tm = int(time.time())
        return tm
    
    async def rsp_err(self, err: str):
        return InfoRsp(
            code = 500,
            msg = err
        )
        
    async def rsp_nologin(self):
        return InfoRsp(
            code = 403
        )
        
    async def rsp_ok(self, data: str):
        return InfoRsp(
            uuid = data
        )
        
    async def floatcmp(self, num1: float, num2: float):
        if num1-num2 > 0.000001:
            return 1
        elif num1-num2 < -0.000001:
            return -1
        else:
            return 0


    async def auth(self, o: str):
        arr = o.split('_')
        if len(arr) == 3:
            uid = arr[0]
            tm = int(arr[1])
            sg = arr[2]
            csg = await self.sign(uid, tm)
            ctm = await self.ctime()
            if ctm < tm or ctm - tm > 6000:
                return (False, '')
            elif csg == sg:
                return (True, uid)
            else:
                return (False, '')
        else:
            return (False, '')

class InfoRsp(BaseModel):
    code: int = 200
    msg: str = ''
    uuid: str = ''