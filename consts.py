FROM_MAIL = 'test@test.com'
SMTP_MAIL = 'smtp.gmail.com:587'
SMTP_USER = 'yotamproject'
SMTP_PASS = 'Tirasham'
ALERT_SYSTEM_NAME = "SOFTWARE ALERT SYSTEM"

JSON_NAME = 'sources.json'
HTML_NAME = 'info.html'
DBURI = 'mongodb://localhost:27017/'
TORNADO_URL = "http://localhost:8888"
FORMAT = "Link to table: "+TORNADO_URL+"\n\n"+"Link to source: %s"


MAIL_LIST = ["michael.mirkin@gmail.com",
             ]

ERROR_MAIL_LIST = ["michael.mirkin@gmail.com",
                   "danscwarz@gmail.com",
                   ]

WAITING_TIME_HOURS = 1
WAITING_TIME_SEC = WAITING_TIME_HOURS * 60 * 60