from typing import Union
from fastapi import FastAPI, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from src import *
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
fh = logging.FileHandler(filename='./server.log')
formatter = logging.Formatter(
    "%(asctime)s - %(module)s - %(funcName)s - line:%(lineno)d - %(levelname)s - %(message)s"
)
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh) 

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

USER = User()
@app.get("/")
async def index():
    return await User.index()
@app.post("/api/reg")
async def reg(req: RegReq):
    return await USER.reg(req)
@app.post("/api/login")
async def login(req: LoginReq):
    return await USER.login(req)

TEXT = Text()
@app.post("/text/post")
async def text_post(req: TextReq):
    return await TEXT.text_post(req)
@app.get("/text/info")
async def text_info(uuid: str, o: str):
    return await TEXT.text_info(uuid, o)
@app.get("/text/list")
async def text_list(offset: int, limit: int, order: str, o: str):
    return await TEXT.text_list(offset, limit, order, o)
@app.delete("/text/del")
async def text_del(uuid: str, o: str):
    return await TEXT.text_del(uuid, o)

SEARCH = Search()
@app.post("/search/post")
async def search_post(req: SearchReq):
    return await SEARCH.search_post(req)
@app.get("/search/info")
async def search_info(uuid: str, o: str):
    return await SEARCH.search_info(uuid, o)
@app.post("/search/list")
async def search_list(req: SearchListReq):
    return await SEARCH.search_list(req)
@app.delete("/search/del")
async def search_del(uuid: str, o: str):
    return await SEARCH.search_del(uuid, o)

IMG = Img()
@app.post("/img/post")
async def img_post(img: UploadFile, uuid: str, o: str):
    return await IMG.img_post(img, uuid, o)
@app.get("/img/info")
async def img_info(uuid: str, o: str):
    return await IMG.img_info(uuid, o)
@app.get("/img/data")
async def img_data(uuid: str, o: str):
    return await IMG.img_data(uuid, o)
@app.get("/img/list")
async def img_list(offset: int, limit: int, order: str, o: str):
    return await IMG.img_list(offset, limit, order, o)
@app.delete("/img/del")
async def img_del(uuid: str, o: str):
    return await IMG.img_del(uuid, o)

VIDEO = Video()
@app.post("/video/post")
async def video_post(video: UploadFile, uuid: str, o: str):
    return await VIDEO.video_post(video, uuid, o)
@app.get("/video/info")
async def video_info(uuid: str, o: str):
    return await VIDEO.video_info(uuid, o)
@app.get("/video/data")
async def video_data(range: str = Header(None), uuid: str = '', o: str = ''):
    return await VIDEO.video_data(range, uuid, o)
@app.get("/video/list")
async def video_list(offset: int, limit: int, order: str, o: str):
    return await VIDEO.video_list(offset, limit, order, o)
@app.delete("/video/del")
async def video_del(uuid: str, o: str):
    return await VIDEO.video_del(uuid, o)

FILE = File()
@app.post("/file/post")
async def file_post(file: UploadFile, uuid: str, o: str):
    return await FILE.file_post(file, uuid, o)
@app.get("/file/info")
async def file_info(uuid: str, o: str):
    return await FILE.file_info(uuid, o)
@app.get("/file/data")
async def file_data(range: str = Header(None), uuid: str = '', o: str = ''):
    return await FILE.file_data(range, uuid, o)
@app.get("/file/list")
async def file_list(offset: int, limit: int, order: str, o: str):
    return await FILE.file_list(offset, limit, order, o)
@app.delete("/file/del")
async def file_del(uuid: str, o: str):
    return await FILE.file_del(uuid, o)

SHOPINFO = ShopToInfo()
@app.post("/shop/balance")
async def shop_balance(req: BalanceReq):
    return await SHOPINFO.shop_balance(req)
@app.get("/shop/info")
async def shop_info(o: str):
    return await SHOPINFO.shop_info(o)

SHOPCATEGORIZE = ShopToCategorize()
@app.post("/shop/categorize/post")
async def shop_categorize_post(req: ShopCategorizeReq):
    return await SHOPCATEGORIZE.shop_categorize_post(req)
@app.post("/shop/categorize/list")
async def shop_categorize_list(req: ShopCategorizeListReq):
    return await SHOPCATEGORIZE.shop_categorize_list(req)
@app.get("/shop/categorize/info")
async def shop_categorize_info(uuid: str, o: str):
    return await SHOPCATEGORIZE.shop_categorize_info(uuid, o)
@app.delete("/shop/categorize/del")
async def shop_categorize_del(uuid: str, o: str):
    return await SHOPCATEGORIZE.shop_categorize_del(uuid, o)

SHOPPRO = ShopToPro()
@app.post("/shop/pro/post")
async def shop_pro_post(req: ShopProReq):
    return await SHOPPRO.shop_pro_post(req)
@app.get("/shop/pro/info")
async def shop_pro_info(uuid: str, o: str):
    return await SHOPPRO.shop_pro_info(uuid, o)
@app.post("/shop/pro/list")
async def shop_pro_list(req: ShopProListReq):
    return await SHOPPRO.shop_pro_list(req)
@app.delete("/shop/pro/del")
async def shop_pro_del(uuid: str, o: str):
    return await SHOPPRO.shop_pro_del(uuid, o)
@app.post("/shop/pro/img/post")
async def shop_pro_img_post(img: UploadFile, o: str):
    return await SHOPPRO.shop_pro_img_post(img, o)
@app.get("/shop/pro/img/data")
async def shop_pro_img_data(uuid: str, o: str):
    return await SHOPPRO.shop_pro_img_data(uuid, o)

SHOPCART = ShopToCart()
@app.post("/shop/cart/add")
async def shop_cart_add(req: CartReq):
    return await SHOPCART.shop_cart_add(req)
@app.get("/shop/cart/list")
async def shop_cart_list( o: str):
    return await SHOPCART.shop_cart_list(o)
@app.delete("/shop/cart/del")
async def shop_cart_del(uuid: str, o: str):
    return await SHOPCART.shop_cart_del(uuid, o)

SHOPORDER = ShopToOrder()
@app.post("/shop/order/create")
async def shop_order_create(req: OrderReq):
    return await SHOPORDER.shop_order_create(req)
@app.get("/shop/order/info")
async def shop_order_info(uuid: str, o: str):
    return await SHOPORDER.shop_order_info(uuid, o)
@app.post("/shop/order/list")
async def shop_order_list(req: ShopOrderListReq):
    return await SHOPORDER.shop_order_list(req)

BIGFILE = BigFile()
@app.post("/big/file/upload")
async def big_upload(req: BigReq):
    return await BIGFILE.big_upload(req)
@app.post("/big/file/down")
async def big_down(req: BigReq):
    return await BIGFILE.big_down(req)
