#!/usr/bin/python
# -*- coding: utf-8 -*-
import feedparser
import re
import datetime

from bs4 import BeautifulSoup
import urllib2
from time import mktime
from pymongo import MongoClient
from DictDiffer import DictDiffer
import smtplib
from email.mime.text import MIMEText
import json
import requests
from consts import *
import operator
import csv
import types


class empty_field(object):

    """
    A Class that might be cancelled in the future. Is used for returning empty values in the empty table entries.
    Also is the parent Class of field.
    """

    def return_date(self):
        return ''

    def new_release_mail(self):
        return


class field(empty_field):

    # A table (realised through dictionary with values as 2-dim list) containing all the Objects of selected releases.
    with open(JSON_NAME) as data_file:
        data_dic = json.load(data_file)


    TableObj = dict((val["soft_name"], [empty_field(), empty_field(), ""]) for el,val in
                    data_dic.iteritems())

    # A table (realised through dictionary with values as 2-dim list) containing all the dates (Strings)
    # of selected releases. This is the Table which is written to the DB and creates the HTML file.

    TableStr = dict((val["soft_name"], ['', '','']) for el,val in data_dic.iteritems())
    html_code = ''
    currentYear = datetime.datetime.now().year



    def return_date(self):
        """
        Returns the date: If the year is the current year it will return it in DD.MM format else it will be returned in
        DD.MM.YYYY format.

        :return:
        String date
        """

        if self.date.year == self.currentYear:
            return '{d.day}.{d.month}'.format(d=self.date)
        return '{d.day}.{d.month}.{d.year}'.format(d=self.date)

    def get_data_firefox(self):
        try:
            r = requests.get(self.data_dic[self.name]["link"], stream=True)

            for e in r.iter_lines():
                m = re.search(self.data_dic[self.name]["format"], e)
                if m:
                    self.version = m.group(1)

                    r2 = requests.get(self.data_dic[self.name]["date_link_beg"] + self.version + self.data_dic[self.name]["date_link_end"])
                    for e in r2.iter_lines():
                        m2 = re.search(self.data_dic[self.name]["format2"], e)
                        if m2:
                            k = m2.group(1)
                            self.date = datetime.datetime.strptime(m2.group(1), self.data_dic[self.name]["date_format"])
                            self.generate_table(self.data_dic[self.name]["date_link_beg"] + self.version + self.data_dic[self.name]["date_link_end"])
                            return
            raise KeyError()
        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)



    def generate_table(self,download_link=""):
        """
        This method puts the Object to the object table and the date to the date table.
        This method is very generic and we don't provide it with exact location.
        :param download_link: This is the download link. If empty nothing would be added to the table.
        """
        self.TableObj[self.soft_name][self.is_official] = self
        self.TableStr[self.soft_name][self.is_official] = self.return_date()
        if download_link!="":
            self.TableStr[self.soft_name][2] = download_link

    def get_data_ios_beta(self):
        """
        Grabs releases from official Apple's Developer's RSS.
        The method throws KeyError if it can't find any release.
        The code grabs the matching from the XML file so it can easily be changed to handle other RSS feeds.
        :return:
        None
        """
        try:
            d = feedparser.parse(self.data_dic[self.name]["link"])

            for e in d.entries:
                m = re.search(self.data_dic[self.name]["format"], e.title)
                if m:
                    self.version = m.group(1)
                    self.beta = m.group(2)
                    self.date = \
                        datetime.datetime.fromtimestamp(mktime(e.published_parsed))
                    self.generate_table()
                    return
            raise KeyError()
        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)

    def get_data_chrome_driver(self):
        """
        Grabs releases from the official Selenium Chrome driver xml directory.
        The method throws KeyError if it can't find any release.
        This is a really general method. Probably there won't be changes.
        :return:
        """
        try:
            link = self.data_dic[self.name]["link"]
            self.version = urllib2.urlopen(link).read()


            xml = urllib2.urlopen(self.data_dic[self.name]["link2"]).read()
            soup = BeautifulSoup(xml,'xml')

            files = []
            dates = []

            for file in soup.findAll('Contents'):
                file_name = file.find('Key').contents[0]
                if file_name.startswith(self.version+"/chromedriver_"):
                    files.append(file_name[len(self.version+"/chromedriver_"):])
                    date_string = file.find('LastModified').contents[0]
                    date = (datetime.datetime.strptime(date_string[:10],self.data_dic[self.name]["format"]))
                    dates.append(date)
                    if file_name.startswith(self.version+"/chromedriver_win32"):
                        self.date = date


            self.generate_table(self.data_dic[self.name]["link_download"]+self.version+"/")


        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)





    def get_data_chrome(self):
        """
        Grabs releases from the official Chrome CSV.
        The method throws KeyError if it can't find any release.
        :return:
        """
        try:


            response = urllib2.urlopen(self.data_dic[self.name]["link"])
            cr = csv.reader(response)

            for row in cr:
                if row[0]==self.data_dic[self.name]["os"] and row[1]==self.data_dic[self.name]["channel"]:
                    self.version=row[2]
                    self.date = datetime.datetime.strptime(row[4],self.data_dic[self.name]["date_format"])
            self.generate_table(self.data_dic[self.name]["link_download"])


        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)





    def get_data_ie_driver(self):
        """
        Grabs releases from the official Selenium IE driver xml directory.
        The method throws KeyError if it can't find any release.
        This is a really general method. Probably there won't be changes.
        :return:
        """
        try:


            xml = urllib2.urlopen(self.data_dic[self.name]["link"]).read()
            soup = BeautifulSoup(xml,'xml')

            files = {}

            #We create a dictionary with all Driver files
            for file in soup.findAll('Contents'):
                file_name = file.find('Key').contents[0]
                if file_name.find(self.data_dic[self.name]["text_format"])!=-1:
                    date_string = file.find('LastModified').contents[0]
                    date = (datetime.datetime.strptime(date_string[:10],self.data_dic[self.name]["format"]))
                    files[file_name] = date

            #We find the most recent release
            last_rel = max(files.iteritems(), key=operator.itemgetter(1))

            #We remove the last 4 characters (.zip).
            self.version = last_rel[0].split("_")[2][:-6]
            self.date = last_rel[1]



            self.generate_table(self.data_dic[self.name]["link_download"]+self.version+"/")


        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)

    def get_data_selenium_folder(self):
        """
        Grabs newest releases from the official Selenium xml directory.
        The method throws KeyError if it can't find any release.
        This is a really general method. Probably there won't be changes.
        :return:
        """
        try:


            xml = urllib2.urlopen(self.data_dic[self.name]["link"]).read()
            soup = BeautifulSoup(xml,'xml')

            files = {}

            #We create a dictionary with all Driver files
            for file in soup.findAll('Contents'):
                file_name = file.find('Key').contents[0]
                if file_name.find(self.data_dic[self.name]["text_format"])!=-1:
                    date_string = file.find('LastModified').contents[0]
                    date = (datetime.datetime.strptime(date_string[:10],self.data_dic[self.name]["format"]))
                    files[file_name] = date

            #We find the most recent release
            last_rel = max(files.iteritems(), key=operator.itemgetter(1))

            #We remove the file name and onlt leave the folder name
            self.version = last_rel[0].split("/")[0]
            self.date = last_rel[1]



            self.generate_table(self.data_dic[self.name]["link_download"]+self.version+"/")


        except Exception as e:
            print(e.message)
            raise KeyError('ERROR: Error reading version or date: ' + self.name)

    def get_data_selenium(self):
        """
        Grabs official releases from Selenium site.
        The code uses BeautifulSoup to grab the first table. The code looks for a row with the right Software.
        In case the Seleniums's format has changed a KeyError is thrown.
        :return:
        """
        try:
            html = urllib2.urlopen(self.data_dic[self.name]["link"]).read()
            soup = BeautifulSoup(html)
            soup.prettify()

            rows = soup.find('table').find_all('tr')
            for row in rows:
                text = row.contents[1].get_text()

                if text == "Python":
                    self.version = row.contents[3].get_text()
                    self.date = datetime.datetime.strptime(row.contents[5].get_text(), self.data_dic[self.name]["date_format"])
                    self.generate_table(self.data_dic[self.name]["link2"])
                    return

            raise KeyError()
        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)


    def get_data_android(self):
        """
        Grabs official releases from Android site.
        The code uses BeautifulSoup to grab the second table. We look for the most recent release.
        The table is not sorted so we actually find the latest date in the table.
        Key error is thrown if something has changes or the url is problematic.
        :return:
        """
        data = {}
        try:
            html = urllib2.urlopen(self.data_dic[self.name]["link"]).read()
            soup = BeautifulSoup(html)
            soup.prettify()

            rows = soup.find_all('table')[1].find_all('tr')
            for row in rows[1:10]:
                b = row.contents
                datestring = row.contents[1].get_text()
                name = row.contents[3].get_text()
                q = ord(datestring[2])-ord('A')
                year = 2009+q//4
                date = datetime.datetime(year,(q%4)*4+1,1)
                days = int(datestring[3:5])-1
                date = date + datetime.timedelta(days=days)
                data[name]=date

            #We find the most recent release
            last_rel = max(data.iteritems(), key=operator.itemgetter(1))
            self.version = last_rel[0][8:]
            self.date = last_rel[1]
            self.generate_table(self.data_dic[self.name]["link2"])

        except Exception as e:
            print(e.message)
            raise KeyError('ERROR: Error reading version or date: ' + self.name)









    def get_data_apple(self):
        """
        Grabs official releases from Apple site.
        The code uses BeautifulSoup to grab the first table. The code looks for a row with the right Software.
        In case the Apple's format has changed a KeyError is thrown.
        :return:
        """
        try:
            html = urllib2.urlopen(self.data_dic[self.name]["link"]).read()
            soup = BeautifulSoup(html)
            soup.prettify()

            rows = soup.find('table').find_all('tr')
            for row in rows:
                text = row.contents[0].get_text()

                m = re.search(self.data_dic[self.name]["format"], text)
                if m:
                    self.version = m.group(1)
                    self.date = datetime.datetime.strptime(row.contents[4].get_text(), self.data_dic[self.name]["date_format"])

                    self.generate_table()
                    return

            raise KeyError()
        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)



    def __init__(self, name):

        self.type = self.data_dic[name]["type"]
        self.name = name
        self.soft_name = self.data_dic[name]["soft_name"]


        # Checks what type is the Object and decides which Web-Grabbing function will be called.
        try:
            if self.type == 'rss':
                self.is_official = 0
                self.get_data_ios_beta()
            elif self.type == 'html_table_apple':
                self.is_official = 1
                self.get_data_apple()
            elif self.type == 'hidden_in_html_source':
                self.is_official = 1
                self.get_data_firefox()
            elif self.type == "plain_file":
                self.is_official = 1
                self.get_data_chrome_driver()
            elif self.type == "plain_file_without_latest":
                self.is_official = 1
                self.get_data_ie_driver()
            elif self.type == "csv":
                self.is_official = 1
                self.get_data_chrome()
            elif self.type == "html_table_selenium":
                self.is_official = 1
                self.get_data_selenium()
            elif self.type == "plain_file_without_latest_folder":
                self.is_official = 1
                self.get_data_selenium_folder()
            elif self.type == "html_table_android":
                self.is_official = 1
                self.get_data_android()
            else:
                raise Exception("Error unknown type: " + self.type)
        except Exception as e:
            self.error_mail(e.message)
            

    def error_mail(self,messages):
        if isinstance(messages, types.StringTypes):
            self.send_mail(ERROR_MAIL_LIST,messages,content="")
        else:
            for m in messages:
                self.send_mail(ERROR_MAIL_LIST,m,content="")
    



    @classmethod
    def load_and_compare(cls):
        """
        Loads the DB from MongoDB (If the selected Document doesn't exist we create it). Checks for changes and calls
        new_release_mail for every change. In the end we write back the Table to the DataBase. Due to the small maximum
        size of the Table we remove the old one and insert the new.
        :return
        True - if there was a change
        False - if there was no change
        """
        change = False
        client = MongoClient(DBURI)
        coll = client.test.work
        cur = coll.find()
        if cur.count() == 0:
            coll.insert(cls.TableStr)
            return

        tmpdic = {}
        for i in cur:
            tmpdic.update(i)

        diff = DictDiffer(tmpdic, cls.TableStr)
        for i in diff.changed():
            if cls.TableStr[i][0] != tmpdic[i][0]:
                change = True
                cls.TableObj[i][0].new_release_mail()
            if cls.TableStr[i][1] != tmpdic[i][1]:
                change = True
                cls.TableObj[i][1].new_release_mail()

        coll.remove({})
        coll.insert(cls.TableStr)
        return change


    def send_mail(self, mails, subject, content=""):
        """
        General Function for sending mails
        """

        msg = MIMEText(content)

        msg['Subject'] = subject

        msg['From'] = FROM_MAIL
        errors = []
        smtp_error = ""
        for mail in mails:



            msg['To'] = mail
            try:
                s = smtplib.SMTP(SMTP_MAIL)

                s.ehlo()
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
            except:
                smtp_error="Error connecting" + SMTP_MAIL
                break
            try:
                s.sendmail(FROM_MAIL, mail,
                           msg.as_string())
            except:
                errors.append('ERROR: Sending to that mail: ' + mail + ', Please Check connection or mail address.')
            s.quit()

        if smtp_error:
            raise Exception(smtp_error)
        elif errors:
            self.error_mail(errors)


    def new_release_mail(self):
        """
        Tries to send a mail in the wanted format. In case there is an error probably due to SMTP connection problem
        throws error. In the future it would be wise to write the message to a log file for future sending.
        """
        self.send_mail(MAIL_LIST, 'SOFTWARE ALERT SYSTEM New ' + (('Beta ' if not(self.is_official) else '')) + 'Release for ' + self.soft_name)