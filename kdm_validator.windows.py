# Requirements:
# -install Python 3.5.0 for Windows (http://www.python.it/download/)
# -Start - Exec - cmd
#    > cd C:\Users\USERNAME\AppData\Local\Programs\Python\Python35\Scripts
#    > easy_install.exe requests
#    > easy_install.exe python-dateutil


import tkinter as tk # Python 3
from tkinter.filedialog import askopenfilename
from tkinter import * # Python 3
import os
from xml.dom import minidom
import datetime, dateutil.parser, dateutil.tz
import requests

KDM_FOLDER = ""
JSON_URL = ""
SERIAL = ""

def check_similarity(title_in_JSON,title_in_KDM):
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
            tk.Button(self, text=self.film_JSON_list[i][u'title'],command=lambda i=i: self.setFilm(i),cursor="hand2").grid(sticky=tk.E+tk.W,column=0,row=i)

        self.textbox = tk.Text(self, borderwidth=3, relief="sunken")
        self.textbox.config(font=("consolas", 10), undo=True, wrap='word',state=tk.DISABLED)
        self.textbox.grid(row=3, column=0)

        return

    def selectXML(self):
        self.cleanTextbox()
        
        filetypes = [('XML file','*.xml')]
        file = askopenfilename(parent=self, title='Choose a file', filetypes=filetypes, initialdir=KDM_FOLDER)
        if file != None:
            self.processXML(file)

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

    def getElementByName(self,xmldoc,name):
        return xmldoc.getElementsByTagName(name)[0].childNodes[0].data

    def processXML(self,file):
        if file==None or self.selected_film_ID==-1:
            return

        self.addText("[Data from Web]\n")
        web_title = self.film_JSON_list[self.selected_film_ID][u'title']
        web_start_TS = int(self.film_JSON_list[self.selected_film_ID][u'min_TS'])
        web_stop_TS = int(self.film_JSON_list[self.selected_film_ID][u'max_TS'])
        self.addText("Selected Film:\t\t"+web_title)
        self.addText("\nFirst show:\t\t"+str(datetime.datetime.fromtimestamp(web_start_TS)))
        self.addText("\nLast show:\t\t"+str(datetime.datetime.fromtimestamp(web_stop_TS)))

        self.addText("\n\n[Data from KDM]\n")
        self.addText("Selected KDM:\t\t"+os.path.basename(file))

        xmldoc = minidom.parse(file)
        KDM_start_datetime = dateutil.parser.parse(self.getElementByName(xmldoc,'ContentKeysNotValidBefore')).astimezone(dateutil.tz.gettz('UTC')).replace(tzinfo=None)
        KDM_stop_datetime = dateutil.parser.parse(self.getElementByName(xmldoc,'ContentKeysNotValidAfter')).astimezone(dateutil.tz.gettz('UTC')).replace(tzinfo=None)
        KDM_title = self.getElementByName(xmldoc,'ContentTitleText')
        self.addText("\nContentTitleText:\t\t"+KDM_title)
        self.addText("\nContentKeysNotValidBefore:\t\t\t\t"+str(KDM_start_datetime))
        self.addText("\nContentKeysNotValidAfter:\t\t\t\t"+str(KDM_stop_datetime))

        KDM_start_TS = (KDM_start_datetime - datetime.datetime(1970,1,1)).total_seconds()
        KDM_stop_TS = (KDM_stop_datetime - datetime.datetime(1970,1,1)).total_seconds()
        
        self.addText("\n\n'"+SERIAL+"' found in KDM:\t\t\t\t")
        if SERIAL not in open(file).read():
            self.addText("KO")
        else:
            self.addText("OK")

        self.addText("\nValid KDM interval:\t\t\t\t")
        if web_start_TS>KDM_start_TS and web_stop_TS<KDM_stop_TS:
            self.addText("OK")
        else:
            self.addText("KO")

        self.addText("\nTitle ?= ContentTitleText:\t\t\t\t")
        (similar,match) = check_similarity(web_title,KDM_title)
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

    def highlight_pattern(self, txt, pattern, tag, start="1.0", end="end"):
        start = txt.index(start)
        end = txt.index(end)
        txt.mark_set("matchStart", start)
        txt.mark_set("matchEnd", start)
        txt.mark_set("searchLimit", end)

        count = tk.IntVar()
        while True:
            index = txt.search(pattern, "matchEnd","searchLimit",
                                count=count, regexp=False)
            if index == "": break
            txt.mark_set("matchStart", index)
            txt.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            txt.tag_add(tag, "matchStart", "matchEnd")

app = Application()
app.master.title('KDM Validator')
app.mainloop()
