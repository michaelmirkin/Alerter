import tornado.httpserver
import tornado.ioloop
import tornado.log
import tornado.web
from pymongo import MongoClient
from field import field
import datetime
from time import gmtime, strftime
from consts import DBURI, HTML_NAME, WAITING_TIME_SEC, JSON_NAME
import collections


class MainHandler(tornado.web.RequestHandler):

    @classmethod
    def set_dict(cls,list):
        cls.listfield = list

    def initialize(self):
        self.client = MongoClient(DBURI)

        super(MainHandler,self).initialize()



    def readDB(self):
        coll = self.client.test.work
        cur = coll.find()
        if cur.count() == 0:
            raise KeyError('The DB seems to be empty')

        tmpdic = {}
        for i in cur:
            tmpdic.update(i)
        return tmpdic


    def get(self):

        TableStr = self.readDB()
        today = datetime.datetime.now()
        today_str = str(today.day)+"."+str(today.month)

        self.render(HTML_NAME, TableStr=TableStr, listFields=self.listfield,today_date=today_str)




application = tornado.web.Application([
    (r"/", MainHandler),
])

def check_updates():
    print(strftime("%Y-%m-%d, %H:%M:%S: ", gmtime()) + "Update is now running")


    for name in field.data_dic:
        field(name)
    if field.load_and_compare():
        print(strftime("%Y-%m-%d, %H:%M:%S: ", gmtime()) + "End of update: There was an update\n")
    else:
        print(strftime("%Y-%m-%d, %H:%M:%S: ", gmtime()) + "End of update: No update\n")
    listfield = list()
    for el,val in field.data_dic.iteritems():
        listfield.append(val["soft_name"])

    MainHandler.set_dict(listfield)






if __name__ == "__main__":

    application.listen(8888)

    check_updates()
    task = tornado.ioloop.PeriodicCallback(check_updates, WAITING_TIME_SEC*1000)
    task.start()
    tornado.ioloop.IOLoop.instance().start()