from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.show import Show

logger = logging.getLogger(__name__)

class UploadService:
    @staticmethod
    def parse_date(date_str: str) -> datetime:
        """解析日期字符串"""
        try:
            # 移除时间字符串中的空格
            date_str = date_str.strip()
            
            # 尝试不同的日期格式
            formats = [
                '%Y/%m/%d %H:%M',  # 2024/12/20 20:00
                '%Y/%m/%d',        # 2024/12/20
                '%Y-%m-%d %H:%M',  # 2024-12-20 20:00
                '%Y-%m-%d'         # 2024-12-20
            ]
            
            for date_format in formats:
                try:
                    return datetime.strptime(date_str, date_format)
                except ValueError:
                    continue
                
            raise ValueError(f"无法解析日期字符串: {date_str}")
            
        except Exception as e:
            logger.error(f"解析日期失败: {str(e)}, 日期字符串: {date_str}")
            raise

    @staticmethod
    def is_duplicate(db: Session, show_data: dict, artist: str) -> bool:
        """检查是否存在重复数据"""
        try:
            show_date = UploadService.parse_date(show_data['date'])
            existing_show = db.query(Show).filter(
                and_(
                    Show.artist == artist,
                    Show.date == show_date.date(),
                    Show.city == show_data['city'],
                    Show.venue == show_data['venue']
                )
            ).first()
            
            # 如果存在重复数据,检查来源
            if existing_show:
                # 如果是大麦数据,保留大麦数据
                if 'damai.cn' in (existing_show.detail_url or ''):
                    logger.info(f"保留大麦数据: {existing_show.name}")
                    return True
                # 如果是秀动数据且新数据是大麦数据,则更新
                elif 'showstart.com' in (existing_show.detail_url or '') and 'damai.cn' in (show_data['detail_url'] or ''):
                    logger.info(f"用大麦数据替换秀动数据: {show_data['name']}")
                    # 删除旧的秀动数据
                    db.delete(existing_show)
                    return False
                # 如果都是秀动数据,保留已有数据
                elif 'showstart.com' in (existing_show.detail_url or '') and 'showstart.com' in (show_data['detail_url'] or ''):
                    logger.info(f"保留已有秀动数据: {existing_show.name}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查重复数据失败: {str(e)}")
            raise

    @staticmethod
    def validate_show_data(show_data: dict) -> bool:
        """验证演出数据的完整性"""
        required_fields = ['name', 'date', 'city', 'venue', 'price']
        for field in required_fields:
            if field not in show_data or not show_data[field]:
                logger.error(f"缺少必要字段: {field}")
                return False
        return True

    @staticmethod
    def upload_shows(db: Session, shows: list, artist: str):
        """上传演出数据到数据库"""
        new_count = 0
        skip_count = 0
        update_count = 0
        
        try:
            for show_data in shows:
                try:
                    # 验证数据
                    if not UploadService.validate_show_data(show_data):
                        logger.error(f"数据验证失败: {show_data}")
                        continue
                    
                    # 检查重复
                    if UploadService.is_duplicate(db, show_data, artist):
                        skip_count += 1
                        logger.info(f"跳过重复数据: {show_data['name']}")
                        continue

                    # 创建新记录
                    show = Show(
                        name=show_data['name'],
                        artist=artist,
                        tag='演出',
                        lineup=show_data['lineup'],
                        date=UploadService.parse_date(show_data['date']),
                        city=show_data['city'],
                        venue=show_data['venue'],
                        price=show_data['price'],
                        status='售票中',
                        detail_url=show_data['detail_url'],
                        poster=show_data['poster']
                    )
                    
                    db.add(show)
                    new_count += 1
                    logger.info(f"添加新演出: {show_data['name']}")

                except Exception as e:
                    logger.error(f"处理演出数据失败: {str(e)}, 数据: {show_data}")
                    continue

            # 提交事务
            db.commit()
            logger.info(f"数据上传完成: 新增 {new_count} 条, 跳过 {skip_count} 条")
            return True

        except Exception as e:
            logger.error(f"上传数据失败: {str(e)}")
            db.rollback()
            return False 