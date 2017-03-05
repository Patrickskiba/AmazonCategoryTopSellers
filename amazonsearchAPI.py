import time
import amazonproduct
import bleach
import datetime
from goodreads import client
from lxml import etree


class TopTenSellerASINs(object):

    def __init__(self, node):
        self._node = node

    def __request_top_ten_sellers_by_node(self, nodeid):
        api = amazonproduct.API(locale='us')
        return api.call(
            Operation='BrowseNodeLookup',
            BrowseNodeId=nodeid,
            ResponseGroup='TopSellers',
            Sort='salesrank')

    def __extract_asin_from_response(self, AmazonResponse):
        listofitems = []
        for item in range(0, 10):
            listofitems.append(AmazonResponse['BrowseNodes']['BrowseNode'][
                'TopSellers']['TopSeller'][item]['ASIN'])
        return listofitems

    def list_of_asin_numbers(self):
        return self.__extract_asin_from_response(
            self.__request_top_ten_sellers_by_node(self._node))


class ItemDetails(object):

    def __init__(self, asinList):
        self._asinList = asinList
        self.gc = client.GoodreadsClient(os.environ['GOOD_READS_KEY'], os.environ['GOOD_READS_SECRET'])

    def get_top_ten_item_details(self):
        itemdetails = []
        for asinVal in self._asinList:
            itemdetails.append(self.__request_item_detail(asinVal))
        return itemdetails

    def __request_item_detail(self, asin):
        api = amazonproduct.API(locale='us')
        item = api.item_lookup(ItemId = asin, ResponseGroup = "Large")
        time.sleep(2)
        return self.__extract_only_useful_info(item)

    def __extract_only_useful_info(self, itemDetails):
        itemProfile = {}
        itemProfile['ASIN'] = (itemDetails['Items']['Item']['ASIN'])
        itemProfile['DetailPageURL'] = (itemDetails['Items']['Item']['DetailPageURL'])
        itemProfile['ImgUrl'] = (itemDetails['Items']['Item']['LargeImage']['URL'])
        itemProfile['Title'] = str(itemDetails['Items']['Item']['ItemAttributes']['Title']).replace(': A novel', '').replace(': A Novel', '')
        itemProfile['Author'] = (itemDetails['Items']['Item']['ItemAttributes']['Author'])
        try:
            itemProfile['ISBN'] = (itemDetails['Items']['Item']['ItemAttributes']['ISBN'])
        except:
            itemProfile['ISBN'] = itemProfile['ASIN']
        try:
            itemProfile['ProductDescription'] = self.__clean_description(self.__good_reads_desc(itemProfile['ISBN'], itemProfile['Title']))
        except:
            browse(locals)
            itemProfile['ProductDescription'] = (itemDetails['Items']['Item']['DetailPageURL'])


        return itemProfile

    def __clean_description(self, desc):
        with_tags_description = str((desc).encode('ascii', 'ignore').decode('ascii'))
        description = bleach.clean(with_tags_description, tags=['br','p'], strip=True)
        return description

    def __good_reads_desc(self, isbn, title):
        try:
            time.sleep(1)
            book = self.gc.search_books(str(isbn))
            browse(book)
        except:
            time.sleep(1)
            book = self.gc.search_books(str(title))
            browse(book)
        return book[0].description




class PageGenerator(object):
    def __init__(self, item_details):
        self._item_details = item_details

    def write_page_text(self):
        for item in range(0, 10):
            text = "--- \nlayout: post \n"
            text += ("title: " + str(self._item_details[item]['Title']).replace(':', '-') + "\n")
            text += ("author: " + self._item_details[item]['Author'] + "\n")
            text += ("img: " + self._item_details[item]['ImgUrl'] + "\n--- \n")
            text += (self._item_details[item]['ProductDescription'] + "\n")
            text += ("<br/><br/> <a href=\"" + self._item_details[item]['DetailPageURL'] + "\"><img src=\"https://images-na.ssl-images-amazon.com/images/G/01/associates/remote-buy-box/buy1.gif\"></a>")
            print(text)
            with open("/home/vagrant/bookshopguide.github.io/_posts/" + datetime.datetime.now().strftime("%Y-%m-%d") + "-" +str(self._item_details[item]['Title']) + ".md", "w") as file_:
                file_.write(text)



ps4TopSellerAsins = TopTenSellerASINs(4919323011)
ps4ItemDetails = ItemDetails(ps4TopSellerAsins.list_of_asin_numbers())

ps4Items = PageGenerator(ps4ItemDetails.get_top_ten_item_details())
ps4Items.write_page_text()
