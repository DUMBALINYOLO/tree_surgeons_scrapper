from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
                    NoSuchElementException,
                    StaleElementReferenceException,
                    TimeoutException,
                )
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time, asyncio
import re
from typing import Any, Callable, Dict, Iterable, Tuple
import logging
import xlsxwriter



logger = logging
logger.basicConfig(format='%(asctime)s - %(message)s', level=logging.ERROR, filename='logs.txt')


NewsOutPut = list[Any]
SlugsOutPut = list[Any]


def parse_content(content_list):

    content_merge = " ".join(content_list)

    content = re.sub('<[^>]+>', '', content_merge)

    return content


def parse_single_content(content):


    content = re.sub('<[^>]+>', '',content)

    return content





class TreeSurgeonSpider(webdriver.Chrome):


    def __init__(self, driver_path='', teardown=False):
        self.driver_path = driver_path
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument("--start-maximized")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-infobars")
        options.add_argument('--disable-popup-blocking')
        options.add_argument('blink-settings=imagesEnabled=false')
        options.add_argument('--disable-gpu')
        super(TreeSurgeonSpider, self).__init__(options=options)
        self.implicitly_wait(6)
        self.maximize_window()



    def parse_county_list_urls(self, county_elements):

        '''
            These is a function that helps us with minimizing the first step 
            function

        '''


        urls = []

        for element in county_elements:
            link_elements = element.find_elements(
                                By.TAG_NAME,
                                "a"
                            )
            for elem in link_elements:
                try:
                    url = elem.get_attribute("href")
                    urls.append(url)

                except:
                    pass

        return urls





    def get_county_urls(self):
        '''
         First Step: This get a list of urls for all Locations and then these Urls
         shall be relied upon to traverse the whole page and extract the expected 
         details

        '''
        self.get("http://www.tree-care.info/treesurgeons/bycounty")

        county_urls = []

        try:
            county_list_element = self.find_element(
                                        By.XPATH,
                                        "//*[@id='fmncountylist']"
                                    )

            county_elements = county_list_element.find_elements(
                                        By.CLASS_NAME,
                                        "fmn_countylist"
                                    )

            county_urls = self.parse_county_list_urls(county_elements)



        except NoSuchElementException:
            print('County List Does Not Exist')


        return county_urls



    def get_arbotist_urls(self, urls):

        '''
         Second Step: The details are hidden in the detail pages for each arbotist 
         hence we first need to scrape the url to the single pages as means to
         navigate to the details and scrape data

        '''
        arbotist_urls = []

        for url in urls:
            self.get(url)
            try:

                table_element = self.find_element(
                                        By.XPATH,
                                        "//*[@id='fmnresults']/table"
                                )
                atags = table_element.find_elements(
                                        By.TAG_NAME,
                                        "a"
                                    )
                for a in atags:
                    try:
                        link = a.get_attribute("href")
                        arbotist_urls.append(link)

                    except:
                        print('Cant find the href on Tag')





            except NoSuchElementException:
                print('The Table seems to be hidden here')


        return arbotist_urls



    def scrape_arbotist_details(self, url):
        self.get(url)

        detail = {}

        try:
            name_element = self.find_element(
                                By.XPATH,
                                "//*[@id='fmndetail']/table/tbody/tr/td"
                            )
            detail['name'] = name_element.get_attribute("innerHTML")
        except NoSuchElementException:
            detail['name'] = None


        try:
            address_element = self.find_element(
                                By.XPATH,
                                "//*[contains(@class, 'adr')]"
                            )
            
            uncleaned_address = address_element.get_attribute("innerHTML")
            detail['address'] = parse_single_content(uncleaned_address)
        except NoSuchElementException:
            detail['address'] = None

        try:
            email_element = self.find_element(
                                By.XPATH,
                                "//*[@id='fmndetail']/table/tbody/tr[3]/td"
                            )
            
            uncleaned_email = email_element.get_attribute("innerHTML")
            detail['email'] = parse_single_content(uncleaned_email)
        except NoSuchElementException:
            detail['email'] = None


        return detail


        







    def scrape_tree_surgeons(self):

        county_urls =  self.get_county_urls()

        print(county_urls)
        arbotist_urls = self.get_arbotist_urls(county_urls)

        print(arbotist_urls)

        workbook = xlsxwriter.Workbook('arbotists.xlsx')
        work_sheet = workbook.add_worksheet("ARBOTISTS")
        work_sheet.write('A1', 'NAME')
        work_sheet.write('B1', 'ADDRESS')
        work_sheet.write('C1', 'EMAIL')
        row_index = 1

        for url in arbotist_urls:
            detail = self.scrape_arbotist_details(url)
            print(detail)

            work_sheet.write('A'+ str(row_index), detail['name'])
            work_sheet.write('B'+ str(row_index), detail['address'])
            work_sheet.write('C'+ str(row_index), detail['email'])
            row_index += 1
        workbook.close()

        self.quit()






        