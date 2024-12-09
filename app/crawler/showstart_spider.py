from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from datetime import datetime

class ShowstartSpider:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_chrome_options()
        self.base_url = "https://www.showstart.com/"
        
    def setup_chrome_options(self):
        """配置Chrome选项"""
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    def get_search_url(self, artist_name: str) -> str:
        """构建搜索URL"""
        return f"https://www.showstart.com/event/list?cityCode=10&keyword={artist_name}"
        
    def search_artist(self, artist_name: str):
        """搜索艺人演出信息"""
        self.logger.info(f"开始搜索艺人: {artist_name}")
        driver = None
        
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            search_url = self.get_search_url(artist_name)
            self.logger.info(f"访问搜索页面: {search_url}")
            
            driver.get(search_url)
            time.sleep(5)  # 等待页面加载
            
            # 保存页面源码以供分析
            with open(f"debug_{artist_name}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            self.logger.info(f"已保存页面源码到 debug_{artist_name}.html")
            
            # 查找所有演出项目
            show_items = driver.find_elements(By.CSS_SELECTOR, "a.show-item")
            self.logger.info(f"找到 {len(show_items)} 个演出")
            
            shows = []
            for item in show_items:
                try:
                    show = {
                        'name': item.find_element(By.CSS_SELECTOR, "div.title").text,
                        'lineup': item.find_element(By.CSS_SELECTOR, "div.artist").text.replace("艺人：", ""),
                        'price': item.find_element(By.CSS_SELECTOR, "div.price").text.replace("价格：", "").replace("¥", ""),
                        'date': item.find_element(By.CSS_SELECTOR, "div.time").text.replace("时间：", ""),
                        'detail_url': item.get_attribute("href"),
                        'poster': item.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
                    }
                    
                    # 处理地点信息
                    addr = item.find_element(By.CSS_SELECTOR, "div.addr").text
                    addr = addr.replace("i class=\"el-icon-location\"></i>", "")
                    city_venue = addr.split("]")
                    show['city'] = city_venue[0].replace("[", "")
                    show['venue'] = city_venue[1] if len(city_venue) > 1 else ""
                    
                    shows.append(show)
                    self.logger.info(f"已提取演出: {show['name']}")
                    self.logger.info(f"详情: {show}")
                    
                except Exception as e:
                    self.logger.error(f"提取演出信息失败: {str(e)}")
                    continue
                    
            return shows
            
        except Exception as e:
            self.logger.error(f"搜索艺人失败: {str(e)}")
            return None
            
        finally:
            if driver:
                driver.quit() 