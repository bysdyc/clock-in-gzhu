import os
import sys
import traceback

import requests
import selenium.webdriver
from loguru import logger
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support.wait import WebDriverWait


class clockIn():

    def __init__(self):
        self.xuhao = os.environ["XUHAO"]
        self.mima = os.environ["MIMA"]
        self.pushplus = os.environ["PUSHPLUS"]

        options = Options()
        options_list = [
            "--headless",
            "--enable-javascript",
            "start-maximized",
            "--disable-gpu",
            "--blink-settings=imagesEnabled=false",
            "--disable-extensions",
            "--no-sandbox",
            "--disable-browser-side-navigation",
            "--disable-dev-shm-usage",
        ]

        for option in options_list:
            options.add_argument(option)

        options.page_load_strategy = "none"
        options.add_experimental_option(
            "excludeSwitches", ["ignore-certificate-errors", "enable-automation"]
        )

        self.driver = selenium.webdriver.Chrome(options=options)
        self.wdwait = WebDriverWait(self.driver, 30)
        self.titlewait = WebDriverWait(self.driver, 5)
        
        # self.page用来表示当前页面
        # 0表示初始页面，Unified Identity Authentication页面，统一身份认证页面和其它页面
        self.page = 0
        self.fail = False

    def __call__(self):
        for retries in range(5):
            try:
                logger.info(f"第{retries+1}次运行")
                if retries:
                    self.refresh()

                if self.page == 0:
                    self.step1()

                if self.page in [0, 1]:
                    self.step2()

                if self.page in [0, 1, 2]:
                    self.step3()

                if self.page in [0, 1, 2, 3]:
                    self.step4()
                    break
            except Exception:
                logger.error(traceback.format_exc())
                logger.error(f'第{retries+1}次运行失败，当前页面标题为：{self.driver.title}')

                if retries == 4:
                    self.fail = True

        self.driver.quit()
        self.notify()

    def refresh(self):
        refresh_times = 0

        while True:
            logger.info('刷新页面')
            self.driver.refresh()

            title = self.driver.title
            if title == '融合门户':
                self.page = 1
            elif title == '学生健康状况申报':
                self.page = 2
            elif title in ['填报健康信息 - 学生健康状况申报', '表单填写与审批::加载中']:
                self.page = 3
            elif title == "":
                logger.info('当前页面标题为：')

                refresh_times += 1
                if refresh_times < 4:
                    continue
            else:
                self.page = 0

            break

        logger.info(f'当前页面标题为：{title}')

    def step1(self):
        logger.info('正在转到统一身份认证页面')
        self.driver.get(
            'https://yq.gzhu.edu.cn/infoplus/form/XSJKZKSB/start'
        )

        self.wdwait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[@class='robot-mag-win small-big-small']")))

        logger.info('正在尝试登陆融合门户')
        for script in [
                f"document.getElementById('un').value='{self.xuhao}'",
                f"document.getElementById('pd').value='{self.mima}'",
                "document.getElementById('index_login_btn').click()"
        ]:
            self.driver.execute_script(script)

    def step2(self):
        logger.info('正在转到学生健康状况申报页面')

    def step3(self):
        logger.info('正在转到填报健康信息 - 学生健康状况申报页面')

    def step4(self):
        self.wdwait.until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="V1_CTRL51"]')))

        logger.info('开始填表')

        self.driver.find_element(By.XPATH,'//*[@id="V1_CTRL51"]').click()

        logger.info('尝试提交表单')
        self.driver.find_element(By.XPATH,
                                 '//*[@id="form_command_bar"]/li[1]').click()

        self.wdwait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@class='dialog_button default fr']")))

        message = self.driver.find_element(
            By.XPATH, "//div[@class='dialog_content']").text

        if message == 'Done successfully!':
            logger.info("打卡成功")
        else:
            logger.error(f"弹出框消息不正确，为:{message}")
            self.fail = True

    def notify(self):
        if not self.pushplus:
            if self.fail:
                sys.exit("打卡失败")
            else:
                sys.exit()
        else:
            if self.fail:
                title = content = "健康打卡失败"
            else:
                title = content = "健康打卡成功"

            logger.info("推送打卡成功与否的消息")

        if self.pushplus:
            data = {"token": self.pushplus, "title": title, "content": content}
            url = "http://www.pushplus.plus/send/"
            logger.info(requests.post(url, data=data).text)


if __name__ == "__main__":
    cl = clockIn()
    cl()
