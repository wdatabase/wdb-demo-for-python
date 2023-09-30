from pydantic import BaseModel
from src.comm import *


class RegReq(BaseModel):
    user: str
    pwd: str
    mail: str

class LoginReq(BaseModel):
    user: str
    pwd: str

class UserInfo(BaseModel):
    uuid: str
    user: str
    pwd: str
    mail: str
    createTime: int
    updateTime: int

class UserRsp(BaseModel):
    code: int
    uid: str
    time: int
    sign: str
    msg: str



class User(Comm):
    async def index():
        return {"ok": "run"}

    async def reg(self, req: RegReq):
        cuuid = await self.uuid()
        tm = await self.ctime()
        pwd =await self.hash(req.user + '_' + req.pwd)

        info = UserInfo(
            uuid = cuuid,
            user = req.user,
            pwd = pwd,
            mail = req.mail,
            createTime = tm,
            updateTime = tm
        )

        key = 'user_' + req.user
        createRsp = await WDB.CreateObj(key, info.model_dump_json(), ['user_list'])
        if createRsp['code'] == 200:
            return UserRsp(
                code = 200, 
                uid = cuuid, 
                time = 0, 
                sign = '', 
                msg = ''
                )
        else:
            return UserRsp(
                code = 400, 
                uid = cuuid, 
                time = 0, 
                sign = '', 
                msg = ''
            )

    async def login(self, req: LoginReq):
        pwd =await self.hash("%s_%s"%(req.user, req.pwd))
        key = "user_%s"%(req.user) 
        getRsp = await WDB.GetObj(key)
        if getRsp['code'] == 200:
            info = UserInfo.model_validate_json(getRsp['data'])
            if pwd == info.pwd:
                tm = await self.ctime()
                sg = await self.sign(info.uuid, tm)
                return UserRsp(
                    code = 200, 
                    uid = info.uuid, 
                    time = tm, 
                    sign = sg, 
                    msg = ''
                    )
            else:
                return UserRsp(
                    code = 400, 
                    uid = '', 
                    time = 0, 
                    sign = '', 
                    msg = 'pwd fail'
                    )
        else:
            return UserRsp(
                    code = 400, 
                    uid = '', 
                    time = 0, 
                    sign = '', 
                    msg = 'api err'
                    )