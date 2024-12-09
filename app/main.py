from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from typing import List
from pydantic import BaseModel

from .crawler.showstart_spider import ShowstartSpider
from .services.upload_service import UploadService
from .config.database import get_db, engine, Base
from .models.show import Show

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UpdateRequest(BaseModel):
    artists: List[str]

@app.post("/crawler/update")
async def update_shows(request: UpdateRequest, db: Session = Depends(get_db)):
    artists = request.artists
    """更新艺人演出信息"""
    try:
        spider = ShowstartSpider()
        results = []
        
        for artist in artists:
            try:
                logger.info(f"开始处理艺人: {artist}")
                # 获取演出数据
                shows = spider.search_artist(artist)
                
                if not shows:
                    logger.warning(f"未找到艺人 {artist} 的演出信息")
                    results.append({
                        "artist": artist,
                        "success": False,
                        "message": "未找到演出信息"
                    })
                    continue
                
                logger.info(f"获取到演出数据: {shows}")
                
                # 上传到数据库
                try:
                    success = UploadService.upload_shows(db, shows, artist)
                    logger.info(f"数据上传{'成功' if success else '失败'}")
                    results.append({
                        "artist": artist,
                        "success": success,
                        "message": "更新成功" if success else "更新失败"
                    })
                except Exception as upload_error:
                    error_msg = f"上传数据时出错: {str(upload_error)}"
                    logger.error(error_msg)
                    logger.exception(upload_error)
                    results.append({
                        "artist": artist,
                        "success": False,
                        "message": error_msg
                    })
                
            except Exception as e:
                error_msg = f"处理艺人 {artist} 数据失败: {str(e)}"
                logger.error(error_msg)
                logger.exception(e)
                results.append({
                    "artist": artist,
                    "success": False,
                    "message": error_msg
                })
        
        return {
            "success": True,
            "data": results
        }
        
    except Exception as e:
        error_msg = f"更新请求处理失败: {str(e)}"
        logger.error(error_msg)
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

@app.get("/test/{artist_name}")
async def test_crawler(artist_name: str):
    """测试爬虫功能"""
    try:
        logger.info(f"开始测试爬取艺人: {artist_name}")
        spider = ShowstartSpider()
        
        # 获取演出数据
        shows = spider.search_artist(artist_name)
        
        if not shows:
            return {
                "success": False,
                "message": "未找到演出信息",
                "data": None
            }
            
        logger.info(f"找到 {len(shows)} 条演出信息:")
        for show in shows:
            logger.info(f"演出: {show['name']}")
            logger.info(f"时间: {show['date']}")
            logger.info(f"地点: {show['city']} - {show['venue']}")
            logger.info(f"价格: {show['price']}")
            logger.info("------------------------")
            
        return {
            "success": True,
            "message": f"成功获取 {len(shows)} 条演出信息",
            "data": shows
        }
        
    except Exception as e:
        logger.error(f"测试爬虫失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/shows/{artist_name}")
async def get_artist_shows(artist_name: str, db: Session = Depends(get_db)):
    """获取艺人演出信息"""
    try:
        shows = db.query(Show).filter(Show.artist == artist_name).all()
        
        if not shows:
            return {
                "success": False,
                "message": "未找到演出信息",
                "data": None
            }
            
        return {
            "success": True,
            "message": f"找到 {len(shows)} 条演出信息",
            "data": [
                {
                    "id": show.id,
                    "name": show.name,
                    "artist": show.artist,
                    "date": show.date.strftime("%Y/%m/%d"),
                    "city": show.city,
                    "venue": show.venue,
                    "price": show.price,
                    "lineup": show.lineup,
                    "detail_url": show.detail_url,
                    "poster": show.poster
                }
                for show in shows
            ]
        }
        
    except Exception as e:
        logger.error(f"获取演出信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 

@app.get("/test-db")
async def test_database(db: Session = Depends(get_db)):
    """测试数据库连接"""
    try:
        logger.info("开始测试数据库连接")
        
        # 测试基本连接
        result = db.execute(text("SELECT 1")).scalar()
        logger.info(f"基本查询测试成功: {result}")
        
        # 检查数据库版本
        version = db.execute(text("SELECT VERSION()")).scalar()
        logger.info(f"数据库版本: {version}")
        
        # 检查shows表是否存在
        tables = db.execute(text("SHOW TABLES")).fetchall()
        logger.info(f"数据库中的表: {tables}")
        
        # 如果shows表存在，检查其结构
        columns = None
        if any('shows' in table for table in tables):
            columns = db.execute(text("DESCRIBE shows")).fetchall()
            logger.info(f"shows表结构: {columns}")
        
        return {
            "success": True,
            "message": "数据库连接正常",
            "version": version,
            "result": result,
            "tables": [table[0] for table in tables],
            "shows_columns": [
                {"name": col[0], "type": col[1]} 
                for col in (columns or [])
            ]
        }
    except Exception as e:
        error_msg = f"数据库测试失败: {str(e)}"
        logger.error(error_msg)
        logger.exception(e)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        ) 