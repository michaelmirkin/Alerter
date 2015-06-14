import tornado.httpserver
import tornado.ioloop
import tornado.log
import tornado.web
from pymongo import MongoClient
from field import field
from time import gmtime, strftime
from consts import DBURI, HTML_NAME, WAITING_TIME_SEC, JSON_NAME


class MainHandler(tornado.web.RequestHandler):
    client = MongoClient(DBURI)

    listfield = {val["soft_name"] for el,val in field.data_dic.iteritems()}

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
        self.render(HTML_NAME, TableStr=TableStr, listFields=self.listfield)




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




if __name__ == "__main__":

    application.listen(8888)

    check_updates()
    task = tornado.ioloop.PeriodicCallback(check_updates, WAITING_TIME_SEC*1000)
    task.start()
    tornado.ioloop.IOLoop.instance().start()