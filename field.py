#!/usr/bin/python
# -*- coding: utf-8 -*-
import feedparser
import re
import datetime

from bs4 import BeautifulSoup
import urllib2
from time import mktime
from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText
import json
import requests
from consts import *
import operator
import csv
import types
from collections import OrderedDict
import unicodedata


class EmptyField(object):
    """
    A Class that might be cancelled in the future. Is used for returning empty values in the empty table entries.
    Also is the parent Class of Field.
    """

    @classmethod
    def return_date(cls, date):
        return ''

    def new_release_mail(self):
        return


class Field(EmptyField):
    # A table (realised through dictionary with values as 2-dim list) containing all the Objects of selected releases.
    with open(JSON_NAME) as data_file:
        data_dic = json.load(data_file, object_pairs_hook=OrderedDict)

    TableObj = dict((val["soft_name"], EmptyField()) for el, val in
                    data_dic.iteritems())

    # A table (realised through dictionary with values as 2-dim list) containing all the dates (Strings)
    # of selected releases. This is the Table which is written to the DB and creates the HTML file.
    TableStr = dict((val["soft_name"], ['', '', '']) for el, val in data_dic.iteritems())
    html_code = ''
    currentYear = datetime.datetime.now().year


    @classmethod
    def return_date(cls, date):
        """
        Returns the date: If the year is the current year it will return it in DD.MM format else it will be returned in
        DD.MM.YYYY format.

        :return:
        String date
        """

        if date.year == cls.currentYear:
            return '{d.day}.{d.month}'.format(d=date)
        return '{d.day}.{d.month}.{d.year}'.format(d=date)

    def get_data_firefox(self):
        try:
            link = self.data_dic[self.name]["link"]
            r = requests.get(link, stream=True)

            for line in r.iter_lines():
                m = re.search(self.data_dic[self.name]["format"], line)
                if m:
                    self.version = m.group(1)

                    r2 = requests.get(
                        self.data_dic[self.name]["date_link_beg"] + self.version + self.data_dic[self.name][
                            "date_link_end"])
                    for e in r2.iter_lines():
                        m2 = re.search(self.data_dic[self.name]["format2"], e)
                        if m2:
                            k = m2.group(1)
                            self.date = datetime.datetime.strptime(m2.group(1), self.data_dic[self.name]["date_format"])
                            self.generate_table(link, self.data_dic[self.name]["date_link_beg"] + self.version +
                                                self.data_dic[self.name]["date_link_end"])
                            return
            raise KeyError()
        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)


    def generate_table(self, source_link, download_link=""):
        """
        This method puts the Object to the object table and the date to the date table.
        This method is very generic and we don't provide it with exact location.
        :param download_link: This is the download link. If empty nothing would be added to the table.
        """
        self.TableObj[self.soft_name] = self
        self.TableStr[self.soft_name][0] = self.return_date(self.date)
        self.TableStr[self.soft_name][2] = source_link
        if download_link != "":
            self.TableStr[self.soft_name][1] = download_link

    def get_data_ios_beta(self):
        """
        Grabs releases from official Apple's Developer's RSS.
        The method throws KeyError if it can't find any release.
        The code grabs the matching from the XML file so it can easily be changed to handle other RSS feeds.
        :return:
        None
        """
        error_mess = ""
        try:
            link = self.data_dic[self.name]["link"]
            d = feedparser.parse(link)

            for e in d.entries:
                m = re.search(self.data_dic[self.name]["format"], e.title)
                if m:
                    self.version = m.group(1)
                    self.beta = m.group(2)
                    self.date = \
                        datetime.datetime.fromtimestamp(mktime(e.published_parsed))


        except Exception as e:
            error_mess = error_mess + "ERROR: Error reading version or date: " + self.name + " Apple RSS. "

        try:
            link_wiki = self.data_dic[self.name]["link_wiki"]
            html = urllib2.urlopen(link_wiki).read()
            soup = BeautifulSoup(html)
            soup.prettify()
            wiki = {}
            rows = soup.find('table').find_all('tr')
            color = self.data_dic[self.name]["color"]
            for row in rows:
                if row.find("td", {"style": "background:" + color + ";"}):
                    version = row.contents[1].get_text()
                    date_string = row.contents[5].get_text().split(";")[0]
                    date_string = unicodedata.normalize('NFKD', date_string).encode('ascii', 'ignore')
                    date_format_wiki = self.data_dic[self.name]["date_format_wiki"]
                    date = datetime.datetime.strptime(date_string, date_format_wiki)
                    wiki.update({version: date})
            last_wiki = max(wiki.iteritems(), key=operator.itemgetter(1))

            if last_wiki[1] >= self.date:
                self.date = last_wiki[1]
                self.version = last_wiki[0]
                link = link_wiki
            self.generate_table(link)

        except Exception as e:
            error_mess = error_mess + "ERROR: Error reading version or date: " + self.name + "Wikipedia. "
        if error_mess:
            raise Exception(error_mess)

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
            soup = BeautifulSoup(xml, 'xml')

            files = []
            dates = []

            for f in soup.findAll('Contents'):
                file_name = f.find('Key').contents[0]
                if file_name.startswith(self.version + "/chromedriver_"):
                    files.append(file_name[len(self.version + "/chromedriver_"):])
                    date_string = f.find('LastModified').contents[0]
                    date = (datetime.datetime.strptime(date_string[:10], self.data_dic[self.name]["format"]))
                    dates.append(date)
                    if file_name.startswith(self.version + "/chromedriver_win32"):
                        self.date = date

            self.generate_table(link, self.data_dic[self.name]["link_download"] + self.version + "/")


        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)


    def get_data_chrome(self):
        """
        Grabs releases from the official Chrome CSV.
        The method throws KeyError if it can't find any release.
        :return:
        """
        try:

            link = self.data_dic[self.name]["link"]
            response = urllib2.urlopen(link)
            cr = csv.reader(response)

            for row in cr:
                if row[0] == self.data_dic[self.name]["os"] and row[1] == self.data_dic[self.name]["channel"]:
                    self.version = row[2]
                    self.date = datetime.datetime.strptime(row[4], self.data_dic[self.name]["date_format"])
            self.generate_table(link, self.data_dic[self.name]["link_download"])


        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)


    def get_data_driver(self):
        """
        Grabs releases from the official Selenium drivers (Safari, IE and folder) xml directory.
        The method throws KeyError if it can't find any release.
        This is a really general method. Probably there won't be changes.
        :return:
        """
        try:

            link = self.data_dic[self.name]["link"]
            xml = urllib2.urlopen(link).read()
            soup = BeautifulSoup(xml, 'xml')

            files = {}

            # We create a dictionary with all Driver files
            for f in soup.findAll('Contents'):
                file_name = f.find('Key').contents[0]
                if file_name.find(self.data_dic[self.name]["text_format"]) != -1:
                    date_string = f.find('LastModified').contents[0]
                    date = (datetime.datetime.strptime(date_string[:10], self.data_dic[self.name]["format"]))
                    files[file_name] = date

            # We find the most recent release
            last_rel = max(files.iteritems(), key=operator.itemgetter(1))

            split_char = self.data_dic[self.name]["split_char"]
            split_section = self.data_dic[self.name]["split_section"]
            num_last_char = self.data_dic[self.name]["num_last_char"]
            if num_last_char == "":
                num_last_char = None

            self.version = last_rel[0].split(split_char)[split_section][:num_last_char]
            self.date = last_rel[1]

            self.generate_table(link, self.data_dic[self.name]["link_download"] + self.version + "/")


        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)


    def get_data_selenium(self):
        """
        Grabs official releases from Selenium site.
        The code uses BeautifulSoup to grab the first table. The code looks for a row with the right Software.
        In case the Seleniums's format has changed a KeyError is thrown.
        :return:
        """
        try:
            link = self.data_dic[self.name]["link"]
            html = urllib2.urlopen(link).read()
            soup = BeautifulSoup(html)
            soup.prettify()

            rows = soup.find('table').find_all('tr')
            for row in rows:
                text = row.contents[1].get_text()

                if text == "Python":
                    self.version = row.contents[3].get_text()
                    self.date = datetime.datetime.strptime(row.contents[5].get_text(),
                        self.data_dic[self.name]["date_format"])
                    self.generate_table(link, self.data_dic[self.name]["link2"])
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
            link = self.data_dic[self.name]["link"]
            html = urllib2.urlopen(link).read()
            soup = BeautifulSoup(html)
            soup.prettify()

            rows = soup.find_all('table')[1].find_all('tr')
            for row in rows[1:10]:
                b = row.contents
                datestring = row.contents[1].get_text()
                name = row.contents[3].get_text()
                q = ord(datestring[2]) - ord('A')
                year = 2009 + q // 4
                date = datetime.datetime(year, (q % 4) * 4 + 1, 1)
                days = int(datestring[3:5]) - 1
                date = date + datetime.timedelta(days=days)
                data[name] = date

            # We find the most recent release
            last_rel = max(data.iteritems(), key=operator.itemgetter(1))
            self.version = last_rel[0][8:]
            self.date = last_rel[1]
            self.generate_table(link, self.data_dic[self.name]["link2"])

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
            link = self.data_dic[self.name]["link"]

            html = urllib2.urlopen(link).read()
            soup = BeautifulSoup(html)
            soup.prettify()

            rows = soup.find('table').find_all('tr')
            for row in rows:
                text = row.contents[0].get_text()

                m = re.search(self.data_dic[self.name]["format"], text)
                if m:
                    self.version = m.group(1)
                    self.date = datetime.datetime.strptime(row.contents[4].get_text(),
                        self.data_dic[self.name]["date_format"])

                    self.generate_table(link)
                    return

            raise KeyError()
        except:
            raise KeyError('ERROR: Error reading version or date: ' + self.name)


    def __init__(self, name):
        self.date = None
        self.version = None
        self.beta = None
        self.type = self.data_dic[name]["type"]
        self.name = name
        self.soft_name = self.data_dic[name]["soft_name"]

        # Decides which Web-Grabbing function will be called according to the JSON file.
        try:
            self.method = self.data_dic[name]["method"]
            getattr(self, self.method)()

        except AttributeError as e:
            raise Exception("Error unknown method: " + self.method + " : " + e.message)
        except Exception as e:
            if type(e) == KeyError and e.message == "method":
                raise Exception("No method Field in " + self.name + " JSON entry.")

            self.error_mail(e.message)


    def error_mail(self, messages):
        """
        Gets messages variable and decides if it's an List or String:
        In the case of list we run and send each element and send a mail.
        """
        if isinstance(messages, types.StringTypes):
            self.send_mail(ERROR_MAIL_LIST, messages, content="")
        else:
            for m in messages:
                self.send_mail(ERROR_MAIL_LIST, m, content="")


    @classmethod
    def load_and_compare(cls):
        """
        Loads the DB from MongoDB (If the selected Document doesn't exist we create it). Checks for changes and calls
        new_release_mail for every changea and update the change in the DB.
        :return
        True - if there was a change
        False - if there was no change
        """
        change = False
        client = MongoClient(DBURI)
        coll = client.test.work
        cur = coll.find_one()
        if not cur:
            coll.insert(cls.TableStr)
            return False

        for k1 in cls.TableStr:
            item = cur.get(k1, [None])
            if item[0] != cls.TableStr[k1][0]:
                print(item[0])
                if not item[0]:
                    cls.TableObj[k1].new_release_mail()
                coll.update({
                }, {
                    '$set': {
                        k1: cls.TableStr[k1]
                    }
                }, upsert=True)
                change = True
        return change


    def send_mail(self, mails, subject, content=""):
        """
        General Method for sending mails
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
                smtp_error = "Error connecting" + SMTP_MAIL
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
        self.send_mail(MAIL_LIST, ALERT_SYSTEM_NAME + ': New ' + (
            ('Beta ' if not (self.data_dic[self.name]["is_main_rel"]) else '')) + 'Release for ' + self.soft_name)