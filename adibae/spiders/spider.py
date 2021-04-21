import datetime
import json
import re

import scrapy

from scrapy.loader import ItemLoader

from ..items import AdibaeItem
from itemloaders.processors import TakeFirst
import requests

url = "https://www.adib.ae/en/_vti_bin/listdataapi.aspx/GetNewsList"

headers = {
	'Connection': 'keep-alive',
	'Pragma': 'no-cache',
	'Cache-Control': 'no-cache',
	'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
	'Accept': 'application/json, text/javascript, */*; q=0.01',
	'X-Requested-With': 'XMLHttpRequest',
	'sec-ch-ua-mobile': '?0',
	'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
	'Content-Type': 'application/json; charset=UTF-8',
	'Origin': 'https://www.adib.ae',
	'Sec-Fetch-Site': 'same-origin',
	'Sec-Fetch-Mode': 'cors',
	'Sec-Fetch-Dest': 'empty',
	'Referer': 'https://www.adib.ae/en/Pages/Personal_Media_Centre_News.aspx',
	'Accept-Language': 'en-US,en;q=0.9,bg;q=0.8',
	'Cookie': 'ADIBIN=u0021xR3wt/5vTo7JCFjy5/liQMAN1kPwBgvuQUEO2AUk8bzmHs/jEQM10QgAHkiamNgWZwgoH92bqC6Fuw==; TS01e545d1=01955bf7fd0d7a1df1c95a6eed60d59f2155c7e507813a60776330ea9637ae20760d524e1a66d2b95bc779bd8e91eb8035969acdf6859bdb9ea50716de12cf19e016989727; __utma=200617214.1398529291.1618989542.1618989542.1618989542.1; __utmc=200617214; __utmz=200617214.1618989542.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; _vwo_uuid_v2=D58688491496398A0E0042A52FBEE903B|16f2091ac39b7639c346c7c46b7d59b4; _gcl_au=1.1.1877433402.1618989542; _hjTLDTest=1; _hjid=8d41c25b-43e3-4deb-b909-0b12908b9227; _hjFirstSeen=1; _ga=GA1.2.1398529291.1618989542; _gid=GA1.2.825149198.1618989542; _vwpnfcm=1; WSS_FullScreenMode=false; _vz=viz_607fc96ffd5b1; _hjAbsoluteSessionInProgress=1; _vwpnstate=BL; __utmb=200617214.3.10.1618989542; ADIBIN=!rJXgALDowptnG7Ly5/liQMAN1kPwBiOX8hCRZxkl/Oe1h1B/7wqZLZVhjzJIk67Lgl1G4JT6Aaw7Ag==; TS01e545d1=01955bf7fd7e8f5a99addbf4bcd79fa1f5f2d53ddb813a60776330ea9637ae20760d524e1a66d2b95bc779bd8e91eb8035969acdf6e922c80334fbd4b5de5c0a6969e6bb47'
}

months = ['January',
          'February',
          'March',
          'April',
          'May',
          'June',
          'July',
          'August',
          'September',
          'October',
          'November',
          'December'
          ]


class AdibaeSpider(scrapy.Spider):
	name = 'adibae'
	year = 2014
	start_urls = ['https://www.adib.ae/en/Pages/Personal_Media_Centre_News.aspx']

	def parse(self, response):
		for month in months:
			payload = '{' + f"'year':'{self.year}','month':'{month}'" + '}'
			data = requests.request("POST", url, headers=headers, data=payload)
			data = json.loads(data.text)
			if data['d'] != 'No Data Found':
				_id = re.findall(r'ID":"(\d+)","YearCal"', data['d'], re.DOTALL)[0]
				date = re.findall(r'\d{1,2}\s[A-Za-z]+\s\d{4}', data['d'])[0]
				link = f'https://www.adib.ae/en/Pages/News_Details.aspx?id={_id}'
				yield response.follow(link, self.parse_post, cb_kwargs={'date': date})

		if self.year < datetime.datetime.now().year:
			self.year += 1
			yield response.follow(response.url, self.parse, dont_filter=True)

	def parse_post(self, response, date):
		title = response.xpath('//p[@class="offerTitle"]/text()').get()
		description = response.xpath('//div[@class="newsWrap"]//text()[normalize-space() and not(ancestor::p[@class="offerTitle"] | ancestor::a[@class="backTo"])]').getall()
		description = [p.strip() for p in description if '{' not in p]
		description = ' '.join(description).strip()

		item = ItemLoader(item=AdibaeItem(), response=response)
		item.default_output_processor = TakeFirst()
		item.add_value('title', title)
		item.add_value('description', description)
		item.add_value('date', date)

		return item.load_item()
