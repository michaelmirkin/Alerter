import tornado.httpserver
import tornado.ioloop
import tornado.log
import tornado.web
from pymongo import MongoClient
from field import Field
import datetime
from time import gmtime, strftime
from consts import DBURI, HTML_NAME, WAITING_TIME_SEC
import collections
import threading


class MainHandler(tornado.web.RequestHandler):
    client = MongoClient(DBURI)

    @classmethod
    def set_dict(cls, tablelist):
        cls.listfield = tablelist

    def initialize(self):
        super(MainHandler, self).initialize()

    def readdb(self):
        coll = self.client.test.work
        cur = coll.find()
        if cur.count() == 0:
            raise KeyError('The DB seems to be empty')

        tmpdic = {}
        for i in cur:
            tmpdic.update(i)
        return tmpdic

    def get(self):
        tablestr = self.readdb()
        today = datetime.datetime.now()
        today_str = str(today.day) + "." + str(today.month)

        self.render(HTML_NAME, TableStr=tablestr, listFields=self.listfield, today_date=today_str)

def create_field_obj(name):
    return Field(name)



def check_updates():
    print(strftime("%Y-%m-%d, %H:%M:%S: ", gmtime()) + "Update is now running")
    threads = []
    for name in Field.data_dic:
        t = threading.Thread(target=create_field_obj, args=(name,))
        t.setDaemon(True)
        threads.append(t)
        t.start()
    for x in threads:
        x.join()

    if Field.load_and_compare():
        print(strftime("%Y-%m-%d, %H:%M:%S: ", gmtime()) + "End of update: There was an update\n")
    else:
        print(strftime("%Y-%m-%d, %H:%M:%S: ", gmtime()) + "End of update: No update\n")
    listfield = list()
    for el, val in Field.data_dic.iteritems():
        listfield.append(val["soft_name"])

    MainHandler.set_dict(listfield)


if __name__ == "__main__":
    application = tornado.web.Application([
    (r"/", MainHandler),
    ])
    application.listen(8888)

    check_updates()
    task = tornado.ioloop.PeriodicCallback(check_updates, WAITING_TIME_SEC * 1000)
    task.start()
    tornado.ioloop.IOLoop.instance().start()