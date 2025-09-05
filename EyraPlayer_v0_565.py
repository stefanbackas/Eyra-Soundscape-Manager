#!/usr/bin/env python3
import sys, atexit
import datetime
import time
import gi
import jmespath
import glob
import random
import json
import os
import logging
from logging.handlers import RotatingFileHandler
import Kronos2
import paho.mqtt.client as mqtt


# Uppdatera cron - Done!
# Random tystnad för tracklist - 
# Random tystnad för pooler, 1.Sannolikhet för tystnad 2. 
# Pool loop
# Slotfadetime funkar inte - grupper?
# Skild fade in och skild fadeout - På slotfadetime eller mellan tracks?
# Mastervolym, Pool / grupp / tracklist volym - Master funkar, pool och grupp blir lite kråtas

gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GstController', '1.0')
from gi.repository import GLib, Gst, GstController
from datetime import datetime, timedelta

SOUNDSCAPES_PATH = "/Users/stefanbackas/Documents/000_EYRA/Eyra_Soundscapes/Designed_Soundscapes/"

CONFIG_PATH = "/Users/stefanbackas/Documents/000_EYRA/Kod/"

# http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+3%3A+Dynamic+pipelines
#Gst.debug_set_active(True)
#st.debug_set_default_threshold(3)

APP_PATH = "./"
TRACKS_PATH = "/Users/stefanbackas/Documents/000_EYRA/Eyra_Soundscapes/ALL_EYRA_TRACKS_MP3/"

Gst.init(None)

class ListPlayer(object):
    def __init__(self, tracks, fadetime, listFadeOutTime, loop, randomise, volume, id):
        
        self.tracks = tracks
        self.fadetime = fadetime
        self.volume = volume
        self.trackNr = 0
        self.id = id
        self.listFadeOutTime = listFadeOutTime
        self.loop = loop
        self.randomise = randomise
        self.inactive = False
        self.p1 = None
        #self.p2 = None

        #Get number of tracks in tracks list
        self.NrOfTracks = len(self.tracks)

        #Randomize tracks
        if(randomise):
            random.shuffle(self.tracks)

        #prepare player1 with fist track
        #try:
        self.track = TRACKS_PATH+self.tracks[self.trackNr]
        self.p1 = Player(self.track,self.listFadeOutTime,self.volume)
        self.newtrackmsg()
       #except:
        #    logging.error("Error while loading new file.")
            
    def newtrackmsg(self):
        msg = datetime.now().strftime("%H:%M:%S") + " Slot: " + self.id + " Starting track: " + self.track
        logging.info(msg)
        print(msg)

    def Status(self):
        #Checks if any of the player objects are playing
        #print("Checking status..")
        try:
            if (self.p1 != None and self.p1.IsStopped() == False):
                print("LP1 Status = Playing")
                return "PLAYING"
            else:
                self.p1 = None
        except:
            pass
        try:
            if (self.p2 != None and self.p2.IsStopped() == False):
                print("LP2 Status = Playing")
                return "PLAYING"
            else:
                self.p2 = None
        except:
            pass
        #print("LP Status = INACTIVE")
        return "INACTIVE"
    
    def stop(self):
        try:
            if (self.p1 == None):
                return False
        except:
            logging.info("did not find self.p1 when executing stop in listplayer (1)")
            return False
        
        self.p2 = self.p1
        self.p2.fade_length = self.listFadeOutTime
        self.p2.FadeOutNow()
        try:
            self.p1 = None
        except:
            logging.info("did not find self.p1 when executing stop in listplayer (2)")
            pass

    def refresh(self):
        #Check if player is active
        if (self.p1 == None):
            #Check if p2 exists
            if (self.p2 == None):
                return False
            #If p1 does not exist and p2 exists
            else:
                if self.p2.IsStopped():
                    self.p2 = None
                    return False
                else:
                    return True
                
        if (self.p1.IsFadingOut(self.id)):
            try:
                self.p2 = None
            except:
                logging.info("Could not execute self.p2 = None when executing refresh in listplayer")
                pass
            self.p2 = self.p1

            try:
                self.p1 = None
            except:
                logging.info("did not find self.p1 when executing refresh in listplayer")
                pass
            
            #if this is the last in the playlist, re-randomize playlist and start over
            if (self.trackNr >= self.NrOfTracks -1):
                print("Last track in playlist")
                #Randomize tracks
                if(self.loop):
                    if(self.randomise):
                        random.shuffle(self.tracks)
                    self.trackNr = 0
                    try:
                        self.track = TRACKS_PATH+self.tracks[self.trackNr]
                        self.p1 = Player(self.track,self.fadetime,self.volume)
                        self.newtrackmsg()
                    except:
                        logging.error("Error while loading new file. ")
                else:
                    self.inactive = True

            #if (self.NrOfTracks == 1 and self.loop == False):
            #    self.inactive = True
            else:
                if(self.inactive != True):   
                    #Start new track
                    print("Starting new track")
                    self.trackNr = self.trackNr + 1
                    # print("volume: " + str(volume))
                    try:
                        self.track = TRACKS_PATH+self.tracks[self.trackNr]
                        self.p1 = Player(self.track,self.fadetime,self.volume)
                        self.newtrackmsg()
                    except:
                        logging.error("Error while loading new file. ")

        return True
            
    
    def __del__(self):
        #Delete player objects
        try:
            self.p1 = None
        except:
            logging.info("Could not execute self.p1 = None when executing __del__ in listplayer")
            pass
        try:
            self.p2 = None
        except:
            logging.info("Could not execute self.p2 = None when executing __del__ in listplayer")
            pass


class Player(object):

    # Gets the state of the Gstreamer pipeline
    def GetState(self):
        retval = 0
        self.pipe.get_state(retval)
        return retval
    
    # Gets the duration of the current loaded media in the pipeline
    # To do: add timeout for function
    def get_duration(self):
        duration_available = False
        while (duration_available == False):
            duration_available = self.pipe.query_duration(Gst.Format.TIME)[0]
            duration = self.pipe.query_duration(Gst.Format.TIME)[1]
        return duration

    def __init__(self, file, fade_length,trackvolume):
        try:
            self.file = file
            self.fade_length = fade_length
            self.trackvolume = trackvolume
            self.lasttrackposition = 0
            self.lasttrackposition_stop = 0

            # create the elements
            self.pipe = Gst.Pipeline.new("pipeline")
            self.source = Gst.ElementFactory.make("filesrc", "source")
            self.parser = Gst.ElementFactory.make("mpegaudioparse", "parser")
            self.decoder = Gst.ElementFactory.make("mpg123audiodec", "decoder")
            self.volume = Gst.ElementFactory.make("volume", "volume")
            self.output = Gst.ElementFactory.make("autoaudiosink", "audio_out")
        
            # add elements to pipeline
            self.pipe.add(self.source)
            self.pipe.add(self.parser)
            self.pipe.add(self.decoder)
            self.pipe.add(self.volume)
            self.pipe.add(self.output)
            
            # Set source
            self.source.set_property("location", file)
            
            # Link everything
            self.source.link(self.parser)
            self.parser.link(self.decoder)
            self.decoder.link(self.volume)
            self.volume.link(self.output)

            #Request pad on volume controller
            self.volume_pad = self.volume.request_pad_simple("sink")

            #Create control source to control volume pad
            self.cs = GstController.InterpolationControlSource()
            #print("Using: GstController.InterpolationMode.LINEAR")
            self.cs.set_property('mode', GstController.InterpolationMode.LINEAR)

            #Bind controller to volume pad
            self.cb = GstController.DirectControlBinding.new(self.volume, 'volume', self.cs)
            self.volume.add_control_binding(self.cb)

            if(fade_length == 0 or fade_length < 0):
                #If no fade is used, set volume control point in the beginning of the file
                self.cs.set(0,trackvolume)
            
            else:
                #Set control points for fade in
                self.cs.set(0, 0.0)
                self.cs.set(Gst.SECOND * fade_length, trackvolume)

            #Start pipe and get duration of the playing media     
            self.pipe.set_state(Gst.State.PLAYING)
            self.duration = self.get_duration()

            if(fade_length <= 0):
                #If no fade is used, set controlpoint in the end of the track
                self.cs.set(self.duration,trackvolume)
            else:
                #Set control points for fade out 
                self.cs.set(self.duration-(Gst.SECOND * fade_length), trackvolume)
                self.cs.set(self.duration, 0)
            
            # Connect to the gstreamer message bus
            self.bus = self.pipe.get_bus()
        except:
            logging.warning("Player object init failed.")
            return None
    # Function to retrieve the current volume
    def get_current_volume(self):
        # Retrieve the current volume directly from the volume element
        current_volume = self.volume.get_property("volume")
        print(f"Current volume: {current_volume}")
        return current_volume
    
                
    def IsStopped(self):
        #print("Entering IsStopped")
        #If the current volume is 0 we can assume that the player is stopped
        if (self.get_current_volume()==0):
            return True
        currentposition_stop = self.pipe.query_position(Gst.Format.TIME).cur
        # If current position has not changed since last poll
        if (currentposition_stop == self.lasttrackposition_stop):
            logging.info("Detected track stop! (IsStopped function)")
            self.lasttrackposition_stop = currentposition_stop
            return True
        self.lasttrackposition_stop = currentposition_stop
        return False
        
    # Detects if the media is fading out or if the media has reached End of Stream
    def IsFadingOut(self,slot):
        try:
            busm = self.GetBusMessages()
            if(busm != "NONE"):
                #print ("Busmessage:", busm)
                msg = ("Busmessage:" + busm)
                logging.info(msg)
            
        except Exception as e:
            s = str(e)
            #print ("Första.. " + s)

        #try:
        currentposition = self.pipe.query_position(Gst.Format.TIME).cur
        #print ("Slot: ", slot, "Last trackpos: ", self.lasttrackposition, "Current", currentposition)

        # If current position has passed the first fade out control point (the media is fading out)
        if (currentposition >= self.duration-Gst.SECOND*self.fade_length):
            #print("Fadeout triggered at: ", str(currentposition))
            logging.info("Fadeout triggered at: " + str(currentposition))
            self.lasttrackposition = currentposition 
            return True
        # If current position has not changed since last poll
        if (currentposition == self.lasttrackposition):
            logging.info("Detected track stop!")
            #print("Detected track stop at: ", str(currentposition))
            self.lasttrackposition = currentposition
            return True
        # The media has reached EOS
        if (busm == "EOS"):
            logging.info("End of stream reached")
            self.lasttrackposition = currentposition
            return True
        
        self.lasttrackposition = currentposition
        return False
        #except Exception as e:
        #    s = str(e)
        #    print ("Andra.. " + s)
        #    logging.error("Error getting fade out or eos data" + s)
        #    # Failure mode is supposed to trigger a track change, hence it returns true
        #   return True

    # Force fade out immediately    
    def FadeOutNow(self):
        now_time = self.pipe.query_position(Gst.Format.TIME).cur
        fade_end_time = now_time + (Gst.SECOND * self.fade_length)
        self.cs.unset_all()
        self.cs.set(now_time, self.trackvolume)
        self.cs.set(fade_end_time, 0)

    # Gets bus messages   
    def GetBusMessages(self):

        msg = self.bus.timed_pop_filtered(0,Gst.MessageType.STATE_CHANGED | Gst.MessageType.EOS | Gst.MessageType.ERROR)
        #print (msg.type)
        if not msg:
            return "NONE"

        t = msg.type

        if t == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            print("ERROR:", msg.src.get_name(), " ", err.message)
            if dbg:
                dbgmsg = "debugging info:" + dbg
                logging.info(dbgmsg)
            return "ERROR"
        elif t == Gst.MessageType.EOS:
            return "EOS"
        
        elif t == Gst.MessageType.STATE_CHANGED:
            # we are only interested in STATE_CHANGED messages from
            # the pipeline
            if msg.src == self.pipe:
                old_state, new_state, pending_state = msg.parse_state_changed()
                dbgmsg = ("Pipeline state changed from {0:s} to {1:s}".format(
                    Gst.Element.state_get_name(old_state),
                    Gst.Element.state_get_name(new_state)))
                logging.info(dbgmsg)
            return "NONE"
        else:
            # should not get here
            logging.error("ERROR: Unexpected message received when getting bus messages.")
            return "UNEXPECTED MESSAGE"
        
    # Gets track counter for display
    def GetTrackCounter(self):
        now_time = self.pipe.query_position(Gst.Format.TIME).cur
        t_now = round((now_time/1000000000), 1)
        t_dur = round((self.duration/1000000000), 1)
        return (str(t_now) + '/' + str(t_dur))
            
    # Destructor
    def __del__(self):
        #Try unsetting all fade-points
        try:
            self.cs.unset_all()
            tmp = self.pipe.set_state(Gst.State.NULL)
        except:
            logging.error("Player desructor failed.")
            pass
        
class timespan:
    def __init__(self,start,stop):
        self.start = int(start)  #Byt mot riktig tid eller ta bort och ha ett expression i slotdefinition som man parsar 
        self.stop = int(stop)
    

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

class Slot(object):
    global mute_groups
    #Checks if Slottype is muted
    def IsMuted(self):
        muted = False
        for m in mute_groups:
            if (self.SlotType == m):
                muted = True
        return muted
    
    def IsTriggered(self):
        triggered = False
        for x in self.ext_trig_list:
            if (self.id == x):
                triggered = True
        return triggered
    
    def IsActive(self):
        if(self.SlotType == "Timeslot"):
            if(self.IsMuted() == False):
                return self.kronos.isactive(datetime.now())
            else:
                #If timeslot is muted, return false
                return False
            
        elif(self.SlotType == "Trigger"):
            if(self.IsTriggered()):
                return True
            else:
                return False
            
            
    
    #Extracts the tracklists from groups and pools
    def GetTracklists(self,item,soundscapedata,retval):
        #Get the type of the item being iterated
        typ = jmespath.search("Soundblocks[?id=='"+item+"'].type", self.configdata)
        #if item is of type group
        if (typ[0] == "Group"):
            #Get items in group and iterate through items
            ret = jmespath.search("Soundblocks[?id=='"+item+"'].items[]", self.configdata)
            for r in ret:
                self.GetTracklists(r,soundscapedata,retval)
        #if item is of type Pool
        if (typ[0] == "Pool"):
            #Get items in pool, randomly choose one of the items in the pool
            ret = jmespath.search("Soundblocks[?id=='"+item+"'].items[]", self.configdata)
            random.shuffle(ret)
            self.GetTracklists(ret[0],soundscapedata,retval)
        if (typ[0] == "Tracklist"):
            #append the tracklist to the return list
            retval.append(item)

    def verify_files(self, tracks):
        try:
            passed = True
            for track in tracks:
                #print("Verifying track: ",track, " in Slot: ", self.id)
                if (os.path.isfile(TRACKS_PATH+track)):
                    #print("File: ", track, " passed")
                    pass
                else:
                    msg = "File: " + track + " not found"
                    print(msg)
                    logging.error(msg)
                    passed = False
            
            if(passed):
                print("Slot:",self.id)
                print("File verification passed.")    
                return True
            else:
                print("File verification failed!")
                return False
        
        except:
            #print ("Error verifying files")
            return False
        
    def __init__(self, id, configdata, ext_trig_list, mute_list):

        #Reference to global list of triggered slots
        self.ext_trig_list = ext_trig_list
        #Reference to list of groups to be muted
        self.mute_list = mute_list
        self.configdata = configdata
        self.kronos = Kronos2.Kronos()
        self.mastervolume = 100
        self.id = id
        temp_tracklists = []
        self.sltrange = slotdefinition()
        self.listplayerinfolist = [] #a list of listplayer info objects that contain all info needed by the listplayer object
        self.SlotType = jmespath.search("Slots[?id=='"+self.id+"'].type", configdata)[0]
        #Get MasterVolume
        self.mastervolume = jmespath.search("SoundscapeSettings[].Volume", configdata)[0]
        self.mastervolume = self.mastervolume / 100

        if(self.SlotType == "Timeslot"):
            #Get the xcron expression
            retval = jmespath.search("Slots[?id=='"+self.id+"'].slotexpression", configdata)
            if len(retval) != 1:
                print("ÄRROR, för mågna expressions någonstans")
            else:
                self.xcron_expression = retval[0]
            #parse the cron
            self.kronos.ParseSlotExpression(self.xcron_expression)
        
        elif(self.SlotType == "Trigger"):
            pass
        else:
            print("ERROR: Unknown slot type")


        #get all items (pools groups and tracks) that belongs to the slot
        tslots = jmespath.search("Slots[?id=='"+self.id+"'].items[]", configdata)

        
        #Get all tracklists
        for t in tslots:
            self.GetTracklists(t,configdata,temp_tracklists)

        #Populate listplayerinfolist 
        for t in temp_tracklists:
            #print (t)
            l = listplayerinfo()
            l.id = jmespath.search("Soundblocks[?id=='"+t+"'].id", configdata)[0]
            l.tracks = jmespath.search("Soundblocks[?id=='"+t+"'].items[]", configdata)
            l.fade_length = jmespath.search("Soundblocks[?id=='"+t+"'].fadetime[]", configdata)[0]
            l.list_fade_length = jmespath.search("Soundblocks[?id=='"+t+"'].slotfadetime", configdata)[0]
            l.volume = jmespath.search("Soundblocks[?id=='"+t+"'].volume", configdata)[0] * self.mastervolume
            l.loop = jmespath.search("Soundblocks[?id=='"+t+"'].loop[]", configdata)[0]
            l.randomise = jmespath.search("Soundblocks[?id=='"+t+"'].randomise[]", configdata)[0]
            l.listplayer = None
            self.listplayerinfolist.append(l)

        for listplayer in self.listplayerinfolist:
            self.verify_files(listplayer.tracks)

    def refresh(self):
        #If time is within start and stoptime
        #if (datetime.today().minute & 1):#If minute is odd (for debugging purposes only) 2BD

        #BUGG Om fadeout inte har hunnit göras har objektet inte förstörts
        #En koll på om listplayern finns första gången slotten blir aktiv behöver göras
        if (self.IsActive()):
            print("Player Is Active", self.id)
            for listplayer in self.listplayerinfolist:
                #print("Checking listplayer", listplayer.id)
            #If player is not playing
                if (listplayer.listplayer == None):
                    print("Starting listplayer: ", listplayer.id)
                    listplayer.listplayer = ListPlayer(listplayer.tracks, listplayer.fade_length,listplayer.list_fade_length, listplayer.loop, listplayer.randomise, listplayer.volume,listplayer.id)
                else:
                    #Refresh listplayer
                    if(listplayer.listplayer.refresh() == False):
                        print("RE-Starting listplayer: ", listplayer.id)
                        #listplayer.listplayer = ListPlayer(listplayer.tracks, listplayer.fade_length,listplayer.list_fade_length, listplayer.loop, listplayer.randomise, listplayer.volume,listplayer.id)
        #Else
        else:
            #print("Player Is NOT Active", self.id)
            for listplayer in self.listplayerinfolist:
                #If player is not playing
                if (listplayer.listplayer == None):
                    #Do nothing
                    pass
                #Else
                else:
                    #Stop player (fade out)
                    listplayer.listplayer.stop()
                    if (listplayer.listplayer.Status() == "INACTIVE"):
                        #Destroying listplayer
                        listplayer.listplayer = None
                    ##!!!! Kolla upp det här: När listplayer slutar blir den inte none. Detta gör att listplayern inte startar om en andra gång.
                    #Raden nedan funkar inte heller eftersom att vi borde vänta på att listplayern har slutat.
                    #self.listplayer = None

        
def __del__():
    logging.info("Eyra Player exiting.")
    try:
        p1 = None
    except:
        pass

    try:
        p2 = None
    except:
        pass

    try:
        p3 = None
    except:
        pass

def GetJsonFileData(filename):
    import json

    # Om filename är absolut sökväg, använd den direkt
    if filename.startswith("/") or filename.startswith("./"):
        filpath = filename
    else:
        # Annars lägg till sökvägen till soundscape-mappen
        filpath = SOUNDSCAPES_PATH + filename

    with open(filpath, "r") as fil:
        data = json.load(fil)
    return data


# Funktioner för att hantera olika ämnen
def handle_trigger_single(payload):
    print(f"Single: {payload} triggered!")
    
# Funktioner för att hantera olika ämnen
def handle_trigger_slot(payload):
    print(f"Slot: {payload} triggered!")
    if payload == "CLEAR":
        ext_triggered_slots.clear()
    else:
        ext_triggered_slots.append(payload)

def handle_mute(payload):
    global mute_groups
    print(f"Muting: {payload}")
    if payload == "CLEAR":
        mute_groups.clear()
    else:
        mute_groups.append(payload)

def handle_unmute(payload):
    global mute_groups
    print(f"Unmuting: {payload}")
    try:
        mute_groups = [item for item in mute_groups if item != payload]
    except TypeError as e:
        print(f"Typfel uppstod: {e}")
    except Exception as e:
        print(f"Ett oväntat fel uppstod: {e}")
    pass


def handle_unknown_topic(topic, payload):
    print(f"Okänt ämne: {topic} med meddelande: {payload}")

# Ordbok som mappar ämnen till hanteringsfunktioner
topic_handlers = {
    "eyra/TriggerSingle": handle_trigger_single,
    "eyra/TriggerSlot": handle_trigger_slot,
    "eyra/Mute": handle_mute,
    "eyra/UnMute": handle_unmute
}

# Huvudfunktion för att hantera inkommande meddelanden
def handle_message(message):
    # Avkoda meddelandet
    payload = message.payload.decode('utf-8')
    
    # Hämta rätt hanteringsfunktion baserat på ämnet, eller använd 'handle_unknown_topic'
    handler = topic_handlers.get(message.topic, handle_unknown_topic)
    
    # Anropa den funktions som hanterar meddelandet
    handler(message.topic, payload) if handler == handle_unknown_topic else handler(payload)


def on_message(client, userdata, message):
    handle_message(message)
    # Avkoda meddelandet
    #payload = message.payload.decode('utf-8')

    # Kolla vilket ämne (topic) meddelandet kom från
    #if message.topic == "eyra/TriggerSlot":
    #    print(f"Slot: {payload} triggered!")
    #    if(payload == "CLEAR"):
    #        ext_triggered_slots.clear()
    #    else:
    #        ext_triggered_slots.append(payload)
    #   
    #elif message.topic == "eyra/Mute":
    #    print(f"Muting: {payload}")
    #    if(payload == "CLEAR"):
    #        mute_groups.clear()
    #    else:
    #        mute_groups.append(payload)
     #   
    #else:
    #    print(f"Okänt ämne: {message.topic} med meddelande: {payload}")

# Callback för MQTT anslutning
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Anslutning lyckades")
    else:
        print(f"Anslutning misslyckades med kod {rc}")

#create list to hold global control variables
#triggered slots (a list of all externally triggered slots)
ext_triggered_slots = []
mute_groups = []

if __name__ == '__main__':

    # MQTT Broker (använd "localhost" om Mosquitto körs på samma dator)
    #broker = "192.168.50.93"
    #port = 1883

    

    print("Eyra Player v0.565_LTS Copyright: Oy Eyra AB")
    
    # Skapa en klient och anslut till brokern
    #client = mqtt.Client()

    # Använd användarnamn och lösenord
    #client.username_pw_set("MQTT", "Öronvax")

    #client.connect(broker, port)

    # Prenumerera på ett ämne
    #topic = "eyra/#"
    #client.subscribe(topic)

    # Tilldela callback för att hantera inkommande meddelanden
    #client.on_message = on_message

    # Starta loop för att hantera kommunikation
    #client.loop_forever()

    atexit.register(__del__)
    

    loglevel = logging.INFO #Change back to WARNING!!!
    try:
        dbglvl = sys.argv[1]
        if(dbglvl == "debug"):
                loglevel = logging.DEBUG
                print("Logging set to debug")
        else:
            print("Unknown parameter.")
    except:
        pass
    logfilepath = APP_PATH + "eyra.log"
    logging.basicConfig(
        handlers=[RotatingFileHandler(logfilepath, maxBytes=100000, backupCount=5)],
        level=loglevel,
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt='%Y-%m-%dT%H:%M:%S')
    
    
    
    logging.info("Eyra Player starting")
    #Get config file
    # Opening config file
    configdata = GetJsonFileData(CONFIG_PATH + "EyraConfig.json")


    ActiveSoundscape = jmespath.search("GeneralSettings[].ActiveSoundscape", configdata)[0]

    sscapedata = GetJsonFileData(ActiveSoundscape)
    
    #Get id:s of all Slots
    tsid = jmespath.search("Slots[].id", sscapedata)
    
    #Create Slot list
    slist = []
    for s in tsid:
        slist.append(Slot(s, sscapedata,ext_triggered_slots,mute_groups))

    #Loop forevah    
    while(1):
        #client.loop()
        for slot in slist:
            slot.refresh()
        #check if config has been updated.

        time.sleep(1)
    """"
    # Check if all configured files exist
    passed = True
    for s in slotlist:
        if (s.verify_files() == False):
            passed = False
    if (passed):
        print("All track files verified.")
        logging.info("All track files verified")
    else:
        print("Error! Track files missing.") 
        logging.error("File verification failed.")
    

    #Keep refreshing slots
    while(1):
        for s in slotlist:
            s.refresh()
        time.sleep(1)
    """
    # x= input()
    sys.exit(1)

