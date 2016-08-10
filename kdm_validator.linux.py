#!/usr/bin/env python
import Tkinter as tk
import tkFileDialog
from Tkinter import *
import os
from xml.dom import minidom
import calendar, datetime, re, time
import requests

KDM_FOLDER = ""
JSON_URL = ""
SERIAL = ""

_date_date_re = re.compile(r'([\d-]+)T?')
_date_time_re = re.compile(r'(?:T| )([\d:]+)')
def parse_date(datetime_str, default_to_local_time = True, get_timestamp = False):
    """
    Parses a string for a date and time, assuming
    that the date is of the format 'YYYY-MM-DD' and the time is of the format 'HH:MM:SS'
    and handles +/-HH:MM offsets according to RFC3339.
    Returns the datetime as a posix timestamp or None if it fails to parse
    """
    date_search = _date_date_re.search(datetime_str)
    if date_search:
        if date_search.group(1).find('-') != -1:
            date_time_array = [int(i) for i in date_search.group(1).split('-')]
        else:
            date_time_array = [
                int(date_search.group(1)[0:4]),
                int(date_search.group(1)[4:6]),
                int(date_search.group(1)[6:8])
            ]
        datetime_str = datetime_str[date_search.end(1):]

        # -- Search for the time component (which is optional)
        time_search = _date_time_re.search(datetime_str)
        if time_search:
            if time_search.group(1).find(':') != -1:
                time_array = [int(i) for i in time_search.group(1).split(':')]
            else:
                time_array = [
                    int(time_search.group(1)[i] + time_search.group(1)[i+1])
                    for i in range(0, len(time_search.group(1)), 2)
                ]
            # -- Pad out any missing time components with zeroes
            for i in range(3 - len(time_array)):
                time_array.append(0)
            date_time_array.extend(time_array)
            datetime_str = datetime_str[time_search.end():]
        else:
            #Missing time so fill it with zeros
            date_time_array += [0,0,0]

        #Create the datetime object
        parsed_timestamp = float(calendar.timegm(date_time_array))

        #Convert the KDM's local time to UTC
        parsed_timestamp += _parse_time_zone(datetime_str, parsed_timestamp, default_to_local_time)

        if get_timestamp:
            return int(parsed_timestamp)
        else:
            return datetime.datetime.utcfromtimestamp(parsed_timestamp)

    return ValueError

_date_timezone_regex = re.compile(r'(\+|-)(\d\d):?(\d\d)')
_zulu_time_regex     = re.compile(r'Z')
def _parse_time_zone(datetime_str, parsed_timestamp, default_to_local_time):
    """
    Parses a datetime string and looks for the RFC 3339 specified time offset +\-HH:MM
    and returns a int that will convert the timestamp to UTC
    It doesn't look for the possible Z (zulu) case because zulu==UTC and a failed search results in 0 being returned
    """

    tz_search = _date_timezone_regex.search(datetime_str)
    if tz_search:
        utc_offset_direction = tz_search.group(1)
        utc_offset_hours = int(utc_offset_direction + tz_search.group(2))
        utc_offset_mins = int(utc_offset_direction + tz_search.group(3))
        #Multiply the result by -1 because +05:00 means the UTC time will be 5 hours less than local time
        return (60*60*utc_offset_hours + 60*utc_offset_mins) * -1
    elif _zulu_time_regex.match(datetime_str) or not default_to_local_time:
        return 0
    else:
        if time.localtime(parsed_timestamp).tm_isdst and time.daylight:
            return time.altzone
        else:
            return time.timezone

def title_and_KDM_title_are_similar(title_in_JSON,title_in_KDM):
    common_words = ['-', 'DI', 'A', 'DA', 'IN', 'CON', 'SU', 'PER', 'TRA', 'FRA', 'IL', 'LO', 'LA', 'I', 'GLI', 'LE', 'UN', 'UNO', 'UNA', 'THE']
    # removes non-ASCII char
    title_from_JSON_only_ASCII = title_in_JSON.encode('ascii', 'ignore').upper().decode("utf-8")
    for word in [x for x in title_from_JSON_only_ASCII.split() if x not in common_words]:
        if str(word) in title_in_KDM.upper():
            return (True,str(word))
    return (False,'')

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid()
        self.createWidgets()
        self.selected_film_ID = -1

    def createWidgets(self):
        self.film_JSON_list = requests.get(JSON_URL,headers={'User-Agent': 'HELLO'}).json()

        # if JSON has less than 3 films, add empty buttons
        while len(self.film_JSON_list)<3:
            self.film_JSON_list.append({u'title':u'',u'min_TS':'0',u'max_TS':'0'})

        for i in range(3):
            tk.Button(self, text=self.film_JSON_list[i][u'title'],command=lambda i=i: self.setFilm(i),cursor="hand2").grid(sticky=E+W,column=0,row=i)

        self.textbox = tk.Text(self, borderwidth=3, relief="sunken")
        self.textbox.config(font=("consolas", 10), undo=True, wrap='word',state=tk.DISABLED)
        self.textbox.grid(row=3, column=0)

        return

    def selectXML(self):
        self.cleanTextbox()
        
        file = tkFileDialog.askopenfile(parent=self, mode='rb', title='Choose a file', filetypes=[('XML file','*.xml')], initialdir=KDM_FOLDER)
        if file != None:
            self.processXML(file.name)

    def setFilm(self,selected_film_ID):
        self.selected_film_ID = selected_film_ID
        if self.film_JSON_list[selected_film_ID][u'title']=='':
            return
        self.selectXML()

    def addText(self,text):
        self.textbox.config(state=tk.NORMAL)
        self.textbox.insert(tk.INSERT,text)
        self.textbox.config(state=tk.DISABLED)

    def cleanTextbox(self):
        self.textbox.config(state=tk.NORMAL)
        self.textbox.delete(1.0, tk.END)
        self.textbox.config(state=tk.DISABLED)

    def processXML(self,file):
        if file==None or self.selected_film_ID==-1:
            return

        self.addText("[Data from Web]\n")
        self.addText("Selected Film:\t\t"+self.film_JSON_list[self.selected_film_ID][u'title'])
        self.addText("\nFirst show:\t\t"+str(datetime.datetime.fromtimestamp(int(self.film_JSON_list[self.selected_film_ID][u'min_TS']))))
        self.addText("\nLast show:\t\t"+str(datetime.datetime.fromtimestamp(int(self.film_JSON_list[self.selected_film_ID][u'max_TS']))))

        self.addText("\n\n[Data from KDM]\n")
        self.addText("Selected KDM:\t\t"+os.path.basename(file))

        xmldoc = minidom.parse(file)
        self.addText("\nContentTitleText:\t\t"+str(xmldoc.getElementsByTagName('ContentTitleText')[0].childNodes[0].data))
        self.addText("\nContentKeysNotValidBefore:\t\t\t\t"+str(parse_date(xmldoc.getElementsByTagName('ContentKeysNotValidBefore')[0].childNodes[0].data)))
        self.addText("\nContentKeysNotValidAfter:\t\t\t\t"+str(parse_date(xmldoc.getElementsByTagName('ContentKeysNotValidAfter')[0].childNodes[0].data)))
        
        self.addText("\n\n'"+SERIAL+"' found in KDM:\t\t\t\t")
        if SERIAL not in open(file).read():
            self.addText("KO")
        else:
            self.addText("OK")

        self.addText("\nValid KDM interval:\t\t\t\t")
        KDM_start_TS = parse_date(xmldoc.getElementsByTagName('ContentKeysNotValidBefore')[0].childNodes[0].data,get_timestamp=True)
        KDM_stop_TS = parse_date(xmldoc.getElementsByTagName('ContentKeysNotValidAfter')[0].childNodes[0].data,get_timestamp=True)
        if int(self.film_JSON_list[self.selected_film_ID][u'min_TS'])>KDM_start_TS and int(self.film_JSON_list[self.selected_film_ID][u'max_TS'])<KDM_stop_TS:
            self.addText("OK")
        else:
            self.addText("KO")

        self.addText("\nTitle ?= ContentTitleText:\t\t\t\t")
        (similar,match) = title_and_KDM_title_are_similar(self.film_JSON_list[self.selected_film_ID][u'title'],str(xmldoc.getElementsByTagName('ContentTitleText')[0].childNodes[0].data))
        if similar:
            self.addText("OK ('"+match+"' matches ContentTitleText)")
        else:
            self.addText("KO (Please check manually!!!)")

        self.textbox.tag_configure("red", foreground= "white", background = "red")
        self.highlight_pattern(self.textbox,"KO", "red")

        self.textbox.tag_configure("green", foreground= "white", background = "green")
        self.highlight_pattern(self.textbox,"OK", "green")

        self.textbox.tag_configure("blue", foreground= "blue", background = "white")
        self.highlight_pattern(self.textbox,"[Data from Web]", "blue")
        self.highlight_pattern(self.textbox,"[Data from KDM]", "blue")

    def highlight_pattern(self, txt, pattern, tag, start="1.0", end="end",regexp=False):
        '''Apply the given tag to all text that matches the given pattern

        If 'regexp' is set to True, pattern will be treated as a regular
        expression.
        '''

        start = txt.index(start)
        end = txt.index(end)
        txt.mark_set("matchStart", start)
        txt.mark_set("matchEnd", start)
        txt.mark_set("searchLimit", end)

        count = tk.IntVar()
        while True:
            index = txt.search(pattern, "matchEnd","searchLimit",
                                count=count, regexp=regexp)
            if index == "": break
            txt.mark_set("matchStart", index)
            txt.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            txt.tag_add(tag, "matchStart", "matchEnd")

app = Application()
app.master.title('KDM Validator')
app.mainloop()
