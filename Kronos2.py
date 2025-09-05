#!/usr/bin/env python3

import datetime

class timespan:
    def __init__(self, start, stop):
        self.start = -1 if start == "*" else int(start)
        self.stop = -1 if stop == "*" else int(stop)


class slotdefinition:
    def __init__(self):
        self.seconds = []
        self.minutes = []
        self.hours = []
        self.days = []
        self.months = []
        self.weeks = []
        self.years = []

class listplayerinfo:
    def __init__(self):
        self.id = None
        self.tracks = None
        self.slotexpression = None
        self.fade_length = None
        self.list_fade_length = None
        self.volume = None
        self.loop = None
        self.randomise = None
        self.listplayer = None

def ConvertTime2Seconds(Timeexpression):
    t = Timeexpression.split(":")
    if (len(t) == 3):
        seconds = int(t[0])*3600 + int(t[1])*60 + int(t[2])
    elif (len(t) == 1):
        if(int(t[0])>=0):
            seconds = int(t[0])*3600
        else:
            seconds = int(t[0])
    else:
        print("Error converting time to seconds")
        return - 1
    return seconds

class Kronos(object):
    def __init__(self):
        self.sltrange = slotdefinition()

    def ParseSlotExpression(self,slotexpression):
        times=[]
        timex=[]
        sltemp = []
        index = 0
        #Split expression parts (seconds, minutes, etc.)
        slist = slotexpression.split(" ")
        if(len(slist) == 7):
            #Handle seconds
            #Split all times defined
            spx = slist[0].split(",")
            #Add all sepate defined times
            for s in spx:
                s = s.split(">")
                if (len(s) == 2):
                    t=timespan(s[0],s[1])
                elif(len(s) == 1):
                    t=timespan(s[0],s[0])
                times.append(t)
            timex.append(times)
            times = []

            #Handle minutes
            #Split all times defined
            spx = slist[1].split(",")
            #Add all sepate defined times
            for s in spx:
                s = s.split(">")
                if (len(s) == 2):
                    t=timespan(s[0],s[1])
                elif(len(s) == 1):
                    t=timespan(s[0],s[0])
                times.append(t)
            timex.append(times)
            times = []

            #Handle hours
            #Split all times defined
            spx = slist[2].split(",")
            #Add all sepate defined times
            for s in spx:
                s = s.split(">")
                if (len(s) == 2):
                    if(s[0].find(":") != -1):
                        t=timespan(ConvertTime2Seconds(s[0]), ConvertTime2Seconds(s[1]))
                    else:
                        t=timespan(ConvertTime2Seconds(s[0]), ConvertTime2Seconds(s[1])+3599)
                elif(len(s) == 1):
                    if(ConvertTime2Seconds(s[0]) == -1):
                        t=timespan(-1,-1)
                    else:
                        t=timespan(ConvertTime2Seconds(s[0]),ConvertTime2Seconds(s[0])+3599)
                times.append(t)
            timex.append(times)
            times = []

            #Handle days
            #Split all times defined
            spx = slist[3].split(",")
            #Add all sepate defined times
            for s in spx:
                s = s.split(">")
                if (len(s) == 2):
                    t=timespan(s[0],s[1])
                elif(len(s) == 1):
                    t=timespan(s[0],s[0])
                times.append(t)
            timex.append(times)
            times = []

            #Handle months
            #Split all times defined
            spx = slist[4].split(",")
            #Add all sepate defined times
            for s in spx:
                s = s.split(">")
                if (len(s) == 2):
                    t=timespan(s[0],s[1])
                elif(len(s) == 1):
                    t=timespan(s[0],s[0])
                times.append(t)
            timex.append(times)
            times = []

            #Handle weekday
            #Split all times defined
            spx = slist[5].split(",")
            #Add all sepate defined times
            for s in spx:
                s = s.split(">")
                if (len(s) == 2):
                    t=timespan(s[0],s[1])
                elif(len(s) == 1):
                    t=timespan(s[0],s[0])
                times.append(t)
            timex.append(times)
            times = []

            #Handle years
            #Split all times defined
            spx = slist[3].split(",")
            #Add all sepate defined times
            for s in spx:
                s = s.split(">")
                if (len(s) == 2):
                    t=timespan(s[0],s[1])
                elif(len(s) == 1):
                    t=timespan(s[0],s[0])
                times.append(t)
            timex.append(times)
            times = []

        
        self.sltrange.seconds = timex[0]
        for ti in timex[0]:
            if(ti.start < -1 or ti.start > 59 or ti.stop < -1 or ti.start > 59):
                print ("ERROR seconds out of range")
        self.sltrange.minutes = timex[1]
        for ti in timex[1]:
            if(ti.start < -1 or ti.start > 59 or ti.stop < -1 or ti.start > 59):
                print ("ERROR minutes out of range")
        self.sltrange.hours = timex[2]
        for ti in timex[2]:
            if(ti.start < -1 or ti.start > 86399 or ti.stop < -1 or ti.start > 86399):
                print ("ERROR hours out of range")
        self.sltrange.days = timex[3]
        for ti in timex[3]:
            if(ti.start < -1 or ti.start==0 or ti.start > 31 or ti.stop < -1 or ti.stop == 0 or ti.start > 31):
                print ("ERROR days out of range")
        self.sltrange.months = timex[4]
        for ti in timex[4]:
            if(ti.start < -1 or ti.start==0 or ti.start > 12 or ti.stop < -1 or ti.stop==0 or ti.start > 12):
                print ("ERROR")
        self.sltrange.weeks = timex[5]
        for ti in timex[5]:
            if(ti.start < -1 or ti.start > 6 or ti.stop < -1 or ti.start > 6):
                print ("ERROR")
        self.sltrange.years = timex[6]
        
        
        for times in timex:
            #print("New item")
            for t in times:
                pass
                #print(t.start, " ", t.stop)

    def isactive(self,dt):
        #Check if current scheduled time is active
        cont = False
        for range in self.sltrange.years:
            if((range.start <= dt.year <= range.stop) or range.start == -1):
                cont = True
            else:
                cont = False
        if(not cont):
            return False

        cont = False
        for range in self.sltrange.weeks:
            if range.start <= range.stop:
                if((range.start <= dt.weekday() <= range.stop) or range.start == -1):
                    cont = True
            else: # over midnight e.g., 23:30-04:15
                if range.start <= dt.weekday() or dt.weekday() <= range.stop:
                    cont = True
        if(not cont):
            return False
    
        cont = False
        for range in self.sltrange.months:
            if range.start <= range.stop:
                if((range.start <= dt.month <= range.stop) or range.start == -1):
                    cont = True
            else: # over midnight e.g., 23:30-04:15
                if range.start <= dt.month or dt.month <= range.stop:
                    cont = True
        if(not cont):
            return False
        
        cont = False
        for range in self.sltrange.days:
            if range.start <= range.stop:
                if((range.start <= dt.day <= range.stop) or range.start == -1):
                    cont = True
            else: # over midnight e.g., 23:30-04:15
                if range.start <= dt.day or dt.day <= range.stop:
                    cont = True
        if(not cont):
            return False
        
        cont = False
        for range in self.sltrange.hours:
            if range.start <= range.stop:
                secs = dt.hour*3600+dt.minute*60+dt.second
                if((range.start <= secs <= range.stop) or range.start == -1):
                    cont = True
            else: # over midnight e.g., 23:30-04:15
                secs = dt.hour*3600+dt.minute*60+dt.second
                if range.start <= secs or secs <= range.stop:
                    cont = True
        if(not cont):
            return False
        
        cont = False
        for range in self.sltrange.minutes:
            if range.start <= range.stop:
                if((range.start <= dt.minute <= range.stop) or range.start == -1):
                    cont = True
            else: # over hour e.g., XX:58-XX:03
                if range.start <= dt.minute or dt.minute <= range.stop:
                    cont = True
        if(not cont):
            return False
        
        cont = False
        for range in self.sltrange.seconds:
            if range.start <= range.stop:
                if((range.start <= dt.second <= range.stop) or range.start == -1):
                    cont = True
            else: # over miniute 
                if range.start <= dt.second or dt.second <= range.stop:
                    cont = True
        if(not cont):
            return False
        
        return True
    
if __name__ == '__main__':

    p = Kronos()
    p.ParseSlotExpression("-1 -1 20:15:00>00:37:59 -1 -1 -1 -1")
    print (p.isactive(datetime.datetime.now()))
   