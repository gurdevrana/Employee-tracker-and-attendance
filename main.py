import json
import htmlPy
import os
#import signin
from selenium import webdriver
import selenium
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PySide.QtCore import *
from PySide.QtGui import *
from selenium.webdriver.common.keys import Keys
from geopy.distance import vincenty
import sqlite3
from datetime import datetime
from Queue import Queue, Empty
from PySide import QtCore
import xlwt
from timeit import default_timer
date=""



def welcome():
    conn = sqlite3.connect('employee.db')
    c = conn.cursor()
    c.execute("SELECT * from empdetail")
    results = c.fetchall()
    res = []
    k = 1
    for row in results:
        res.append((row[0], row[1], row[2]))
    return res

class WorkerThread(QThread):
    def __init__(self,user,passw,mapno,parent=None):
        super(WorkerThread, self).__init__(parent)
        self.username=user
        self.password=passw
        self.mapno=mapno


    def run(self):
        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--incognito")
        #self.driver = webdriver.Chrome()
        self.driver = selenium.webdriver.PhantomJS()
        location = findlocation(self.username, self.driver,self.password)
        if location==1:
            #self.app.evaluate_javascript("alert('couldnt able to locate"+self.username+"');")
            #self.app.evaluate_javascript("document.getElementsById('retry-link1').style.display='block';")
            print("unable to create thread")
            self.emit(SIGNAL("Threaddone(QString,QString,QString,QString,QString)"), "NON", "NON", self.mapno, "NON",self.username)
        else:
            distance=find_distance(self.username,location)
            save_to_database(self.username,distance)
            distance=str(distance)

            lat = location.split(',')[0]
            lon = location.split(',')[1]
            self.emit(SIGNAL("Threaddone(QString,QString,QString,QString,QString)"), lon, lat,self.mapno,distance,self.username)


class Tracker(htmlPy.Object):
#GUI callable functions have to be inside a class.

    def __init__(self, app):
        super(Tracker, self).__init__()
        self.app = app
        #self.workerThread = WorkerThread()
        #self.connect(self.workerThread, SIGNAL("Threaddone(QString,QString,QString,QString)"), self.Threaddone, Qt.QueuedConnection)

    @htmlPy.Slot(str)
    def form(self, json_data):
        # @htmlPy.Slot(arg1_type, arg2_type, ..., result=return_type)
        # This function can be used for GUI forms.
        form_data = json.loads(json_data)
        global date
        date = form_data['date']
        date = str(date)
        if date.strip()=="":
            self.app.evaluate_javascript("alert('Please enter date')")
        else:
            check=checkdate(date)
            if check==0:
                self.app.evaluate_javascript("var x=document.getElementsByClassName('load');"
                "var i;"
                "for (i = 0; i < x.length; i++) {"
                "x[i].style.display = 'block';"
                "}")
                conn = sqlite3.connect('employee.db')
                c = conn.cursor()
                c.execute("SELECT * from empdetail")
                results = c.fetchall()
                res = []
                k = 1
                for row in results:
                    mapno="map"+str(row[0])
                    res.append((row[2], row[3],mapno))


                print("hello")
                self.workers = list()

                for i in res:
                    self.workerThread = WorkerThread(i[0],i[1],i[2])
                    self.connect(self.workerThread, SIGNAL("Threaddone(QString,QString,QString,QString,QString)"),
                                 self.Threaddone, Qt.QueuedConnection)

                    self.workers.append(self.workerThread)
                    k=k+1
                for worker in self.workers:
                    worker.start()



            else:
                self.app.evaluate_javascript("alert('attendance already taken');")

    @htmlPy.Slot()
    def refresh(self):
        self.workerThread.quit()
        self.workerThread2.quit()


        self.app.evaluate_javascript("window.location.reload();")
        app.template = ("index.html", {})
        self.workerThread.driver.quit()
        self.workerThread2.driver.quit()

    @htmlPy.Slot()
    def append(self):
        print("addend")

        self.app.evaluate_javascript(""" var bubble_img = $('body').data('bubble-img');"""+
        """var text='<img src='+bubble_img+' class="load"  >' ;"""+
        """$("body").append(text);""")

    @htmlPy.Slot(str)
    def addemployee(self,json_data):
        print("in addemployee")
        form_data = json.loads(json_data)
        name=form_data['name']
        empid=form_data['employeeid']
        passw=form_data['password']
        age=form_data['age']
        add=form_data['address']
        desig=form_data['designation']
        sal_per_day=form_data['sal_per_day']
        if name and empid and passw and sal_per_day:
            conn = sqlite3.connect('employee.db')
            c = conn.cursor()
            c.execute("INSERT INTO empdetail(name,employeeid,password,age,address,designation,sal_per_day) "
                      "VALUES (?,?,?,?,?,?,?);" ,(name,empid,passw,age,add,desig,sal_per_day,))
            conn.commit()
            res = welcome()
            app.template = ("index.html", {"results": res})
        else:
            app.template=("add_employee.html",{"error":"Enter required Fields"})

    @htmlPy.Slot(str,str)
    def destroy_thread(self,username,mapno):
        print("in retry")
        no="retry-link"+str(mapno[3])
        print(no)

        self.app.evaluate_javascript("alert('couldnt able to locate" + username + "');")
        self.app.evaluate_javascript("document.getElementById('"+no+"').style.display='block';")
        self.workerThread.terminate()


    @htmlPy.Slot()
    def excel(self):
        salexcel()
        self.app.evaluate_javascript("alert('excel sheet generated');")

    @htmlPy.Slot()
    def show_salary(self):
        conn = sqlite3.connect('employee.db')
        c = conn.cursor()
        c.execute("SELECT * from employ")
        results = c.fetchall()
        app.template = ("show_salary.html", {"results": results})


    @htmlPy.Slot(str,str)
    def retry(self):
        print("retry")

    @htmlPy.Slot(str,str,str,str,str)
    def Threaddone(self,lon,lat,mapno,distance,username):
        print("in threaddone")
        if lon == "NON" or lat == "NON" :
            self.destroy_thread(username,mapno)
        else:
            self.jsfunction(lon,lat,mapno,distance)


    @htmlPy.Slot()
    def back(self):
        conn = sqlite3.connect('employee.db')
        c = conn.cursor()
        c.execute("SELECT * from empdetail")
        results = c.fetchall()
        res = []
        k = 1
        for row in results:
            res.append((row[0], row[1], row[2]))

        print(results)

        app.template = ("index.html", {"results": res})

    @htmlPy.Slot()
    def display_employ(self):
        conn = sqlite3.connect('employee.db')
        c = conn.cursor()
        c.execute("SELECT * from empdetail")
        results = c.fetchall()
        app.template = ("show_emp.html", {"results": results})

    @htmlPy.Slot()
    def delete_emp(self):
        conn = sqlite3.connect('employee.db')
        c = conn.cursor()
        c.execute("SELECT * from empdetail")
        results = c.fetchall()
        app.template = ("delete_emp.html", {"results": results})

    @htmlPy.Slot()
    def add(self):
        app.template=("add_employee.html",{})

    @htmlPy.Slot(str,str,str,str)
    def jsfunction(self,lon,lat,mapno,distance):
        # Any function decorated with @htmlPy.Slot decorater can be called
        # using javascript in GUI

        print("in js"+lon+lat+mapno)
        mapno=str(mapno)
        self.app.evaluate_javascript("var x=document.getElementsByClassName('load');"
                                     "var i;"
                                     "for (i = 0; i < x.length; i++) {"
                                     "x[i].style.display = 'none';"
                                     "}"
                                     "var d1=document.getElementById('"+mapno+"');"
                                     "d1.style.display='block';")
        self.app.evaluate_javascript("alert('"+mapno+"');"

                                     "var uluru={lat:"+lat+",lng:"+lon+"};"

                                     "var map = new google.maps.Map(document.getElementById('"+mapno+"'),{zoom: 17,center: uluru});"
                                     "var marker = new google.maps.Marker({"
                                     "position: uluru,"
                                     "map: map});")
                                    # "}")


        distance = float(distance)
        if distance < 100:
            self.app.evaluate_javascript("document.getElementById('attendance"+mapno+"').innerHTML = 'PRESENT' ;")
            self.app.evaluate_javascript("$('#tick"+mapno+"').removeClass('notdisplay');")

        else:
            self.app.evaluate_javascript("document.getElementById('attendance"+mapno+"').innerHTML ='ABSENT';")
            self.app.evaluate_javascript("$('#cross"+mapno+"').removeClass('notdisplay');")

        self.workerThread.terminate()
        #salexcel()
def createxcel():
    book = xlwt.Workbook(encoding="utf-8")
    sheet1 = book.add_sheet("Sheet 1")
    global date
    date_object = datetime.strptime(date, '%m/%d/%Y')
    month = date_object.strftime("%m")
    for i in range(1,31):
        st=str(i)+"/"+str(month)
        sheet1.write(0, i,st)
    month = date_object.strftime("%B")
    book.save(month+".xls")

def salexcel():
    book = xlwt.Workbook(encoding="utf-8")
    sheet1 = book.add_sheet("Sheet 1")
    conn = sqlite3.connect('employee.db')
    c = conn.cursor()
    c.execute("SELECT * FROM employ")
    results = c.fetchall()
    i = 0
    sheet1.write(i, 0, "S.No")
    sheet1.write(i, 1, "name")
    sheet1.write(i, 2, "employeeid")
    sheet1.write(i, 3, "month")
    sheet1.write(i, 4, "present_days")
    sheet1.write(i, 5, "sal_per_day")
    sheet1.write(i, 6, "total_salary")
    k = 1
    i = 2
    for row in results:
        sheet1.write(i, 0, k)
        sheet1.write(i, 1, row[0])
        sheet1.write(i, 2, row[1])
        sheet1.write(i, 3, row[2])
        sheet1.write(i, 4, row[3])
        sheet1.write(i, 5, row[4])
        sheet1.write(i, 6, row[5])
        i = i + 1
        k = k + 1
    book.save("salary.xls")


def find_distance(username,location):
    lat = location.split(',')[0]
    lon = location.split(',')[1]
    employee = (lat, lon)
    college = (28.631657, 77.116550)
    #college = (28.5657113, 77.234947)
    print(username + " is at distance")
    print(vincenty(employee, college).meters)
    distance = vincenty(employee, college).meters
    return distance


def findlocation(username,driver,password):
    wait = WebDriverWait(driver, 20)
    driver.get("https://www.google.com/android/devicemanager")
    try:
        elem = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
    except Exception as e:
        print("exception found", format(e))
        return 1

    #elem = driver.find_element_by_id("Email")
    elem.send_keys(username)
    elem.send_keys(Keys.RETURN)
    #driver.find_element_by_id("next").click()
    time.sleep(5)
    try:
        elem = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']")))
    except Exception as e:
        print("exception found", format(e))
        return 1

    # elem2.clear()

    elem.send_keys(password)
    elem.send_keys(Keys.RETURN)
    lon = ""
    lat = ""
    flag = 1
    start = default_timer()

    while lat is None or lat == ""  :

        try:
            map = WebDriverWait(driver, 49).until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@id='devices-container']/div[@class='device visible-device-details']")))
            duration = default_timer() - start
            if (duration > 50):
                driver.quit()
                return 1

            if map is not None:
            # time.sleep(30)
                lat = map.get_attribute('data-lat')
                lon = map.get_attribute('data-lon')


            else:
                locatebutton = driver.find_element_by_xpath("//div[@class='summary-buttons']/button[@data-action='locate']")
                locatebutton.click()
                time.sleep(5)
        except Exception as e:
            driver.quit()
            return 1
    if lat is None or lat == "" :
        driver.quit()
        return 1
    print(username+" latitude is " + lat)
    print(username+" longitude is " + lon)
    time.sleep(5)
    driver.quit()
    return lat+","+lon

def save_to_database(username,distance):
    conn = sqlite3.connect('employee.db')
    c = conn.cursor()
    global date
    date_object = datetime.strptime(date, '%m/%d/%Y')
    month = date_object.strftime("%B")
    print(month)
    days=0
    salperday=100
    found=0

    if distance < 100:
        for results in c.execute("SELECT employeeid,present_days from employ where month=? AND employeeid=?", (month, username,)):
            days = results[1]
            if days!=0:
                found=1
        print(days)
        for detail in c.execute("SELECT name ,sal_per_day from empdetail where employeeid=?", (username,)):
            name = detail[0]
            salperday = detail[1]
        if found==0:
            c.execute("INSERT INTO employ VALUES (?,?,?,?,?,?)", (name, username, month, 1, salperday, salperday,))
            conn.commit()
        else:
            days = days + 1
            c.execute("UPDATE employ set present_days = ?,total_salary=? "
                     "where employeeid=?", (days, days * salperday, username,))
            conn.commit()


def checkdate(date):
    conn = sqlite3.connect('employee.db')
    c = conn.cursor()
    c.execute("SELECT * from attendance where date=?", (date,))
    data = c.fetchall()
    if len(data) == 0:
        c.execute("INSERT INTO attendance VALUES(?)", (date,))
        conn.commit()
        return 0
    else:

        return 1

def signin(us):
    print("hello bro"+us)
## You have to bind the class instance to the AppGUI instance to be
## callable from GUI
app = htmlPy.AppGUI(title=u"Employee Tracker", maximized=True)

app.template_path = os.path.abspath(".")
app.static_path = os.path.abspath(".")
app.bind(Tracker(app))
res=welcome()
app.template = ("index.html", {"results":res})

app.start()

