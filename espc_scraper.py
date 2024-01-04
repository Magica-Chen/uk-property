import time
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd


class EspcScraper:
    def __init__(self):
        self.results = []

    def fetch(self, url):
        print('HTTP GET request to URL: %s' % url, end='')
        res = requests.get(url)
        print(' | Status code: %s' % res.status_code)
        return res

    def parse(self, html):
        content = BeautifulSoup(html, 'lxml')
        cards = content.findAll('div', {'class': 'infoWrap'})

        delimiters = ":|,"
        for card in cards:
            # hyperlink
            link = 'https://espc.com' + card.find('a')['href']
            # title includes property type, address, town and postcode
            title = card.find('h3', {'class': 'propertyTitle'}).text
            title_part = re.split(delimiters, title)
            postcode = title_part[-1].strip()
            if postcode.count(' ') > 1:
                town = postcode.split()[0]
                postcode = ' '.join(postcode.split()[-2:])
            else:
                town = title_part[2].strip()

            # description
            description = card.find('div', {'class': 'description'})
            # price & offer
            offer_type = card.find('span', {'class': 'offersOver'}).text
            price = card.find('span', {'class': 'price'}).text
            # facilities
            facilities = card.find('div', {'class': 'facilities'}).text
            # Ensure the list is at least 3 elements long by extending with 'U'
            facilities = (facilities + 'U' * 3)[:3]

            try:
                agent = card.find('div', {'class': 'logoWrap'}).find('img')['alt']
            except:
                agent = 'N/A'

            self.results.append({
                'offer_type': offer_type[:-len(price) - 1],
                'price': price.strip(),
                'property_type': title_part[0].strip(),
                'address': title_part[1].strip(),
                'town': town,
                'postcode': postcode,
                'area': postcode.split()[0],
                'beds': facilities[0],
                'toilets': facilities[1],
                'living_rooms': facilities[2],
                'description': description.text.split('\n', 1)[0],
                'link': link,
                'parking': 'parking' in description,
                'allocated': 'allocated' in description,
                'agent': agent
            })

    def to_csv(self):
        # save results
        df = pd.DataFrame(self.results)
        df.drop_duplicates(subset=['agent',
                                   'address',
                                   'price'],
                           inplace=True)
        print('Saving ', len(df), ' items to csv file (espc.csv)...')
        df.to_csv('espc.csv', index=False,
                  encoding='utf-8-sig')

    def run(self):
        # get first page
        url = 'https://espc.com/properties?locations=edinburgh&minbeds=2plus&maxprice=300000'
        res = self.fetch(url)
        self.parse(res.text)
        # get number of pages
        li_tags = BeautifulSoup(res.text, 'lxml').select('ul.paginationList > li')
        n_pages = int(li_tags[-2].text)
        # get all pages
        insert_position = url.find('?') + 1  # +1 to insert after the '?'
        for page in range(2, n_pages + 1):
            string_to_insert = 'p=' + str(page) + '&'
            new_url = url[:insert_position] + string_to_insert + url[insert_position:]
            new_res = self.fetch(new_url)
            self.parse(new_res.text)
            time.sleep(2)

        self.to_csv()


if __name__ == "__main__":
    scraper = EspcScraper()
    scraper.run()
