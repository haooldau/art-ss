from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import time
import logging
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # 数据库连接配置
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:74R6z2n891KemMJrjQ3OcT5uwkYE0HgV@hkg1.clusters.zeabur.com:32710/zeabur")
    
    logger.info(f"尝试连接数据库: {DATABASE_URL}")
    
    # 创建数据库引擎
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=True  # 启用SQL语句日志
    )
    
    # 测试连接
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        logger.info("数据库连接测试成功")
    
except Exception as e:
    logger.error(f"数据库配置失败: {str(e)}")
    logger.exception(e)
    raise

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基本映射类
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = None
    try:
        db = SessionLocal()
        # 测试连接
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        logger.error(f"获取数据库会话失败: {str(e)}")
        logger.exception(e)
        if db:
            db.close()
        raise
    finally:
        if db:
            db.close() 