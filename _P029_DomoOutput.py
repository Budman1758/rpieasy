#!/usr/bin/env python3
#############################################################################
################# (Domoticz) Output helper for RPIEasy ######################
#############################################################################
#
# Two way communication is implemented through plugin_receivedata()
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import lib.lib_gpiohelper as gpiohelper
import Settings

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 29
 PLUGIN_NAME = "Output - Output Helper"
 PLUGIN_VALUENAME1 = "State"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_SINGLE
  self.vtype = rpieGlobals.SENSOR_TYPE_SWITCH
  self.valuecount = 1
  self.senddataoption = True
  self.recdataoption = True
  self.pullupoption = False
  self.inverselogicoption = False

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.decimals[0]=0
  self.sync()

 def webform_load(self):
  webserver.addFormNote("Please make sure to select <a href='pinout'>pin configured for Output!</a>")
  webserver.addFormCheckBox("Preserve state at startup","p029_preserve",self.taskdevicepluginconfig[0])
  return True

 def webform_save(self,params):
  if (webserver.arg("p029_preserve",params)=="on"):
   self.taskdevicepluginconfig[0] = True
  else:
   self.taskdevicepluginconfig[0] = False
  self.sync()
  return True

 def sync(self):
  if self.enabled:
   if self.taskdevicepin[0]>=0:
    v1 = gpios.HWPorts.input(self.taskdevicepin[0])
    if self.taskdevicepluginconfig[0]==True:
       ot = False
       for p in range(len(Settings.Pinout)):
        if str(Settings.Pinout[p]["BCM"])==str(self.taskdevicepin[0]):
         if Settings.Pinout[p]["startupstate"]==4:
          ot = True
          break
       if ot==False:
        misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Pin is not an Output, State preserving disabled")
        self.taskdevicepluginconfig[0] = False
    if v1 != self.uservar[0]:
     if self.taskdevicepluginconfig[0]==True:
      self.set_value(1,int(self.uservar[0]),True)   # restore previous state from uservar
      misc.addLog(rpieGlobals.LOG_LEVEL_INFO,self.taskname+": Restoring previous GPIO value "+str(self.uservar[0]))
     else:
      self.uservar[0] = v1                      # store actual pin state into uservar
      misc.addLog(rpieGlobals.LOG_LEVEL_INFO,self.taskname+": Syncing actual GPIO value "+str(v1))
   if self.initialized:
    if self.taskdevicepluginconfig[0]==True:
     sps = "en"
    else:
     sps = "dis"
    misc.addLog(rpieGlobals.LOG_LEVEL_INFO,"State preserving is "+sps+"abled")


 def set_value(self,valuenum,value,publish=True,suserssi=-1,susebattery=-1): # Also reacting and handling Taskvalueset
  if self.initialized:
   if self.taskdevicepin[0]>=0:
    if 'on' in str(value).lower() or str(value)=="1":
     val = 1
    else:
     val = 0
    try:
     gpios.HWPorts.output(self.taskdevicepin[0],val)     # try to set gpio according to requested status
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Please set up GPIO type before use "+str(e))
  plugin.PluginProto.set_value(self,valuenum,value,publish,suserssi,susebattery)

 def plugin_receivedata(self,data):                        # set value based on mqtt input
  if (len(data)>0) and self.initialized and self.enabled:
   if 'on' in str(data[0]).lower() or str(data[0])=="1":
    val = 1
   else:
    val = 0
   self.set_value(1,val,False)
#  print("Data received:",data) # DEBUG

 def plugin_write(self,cmd):
  res = False
  cmdarr = cmd.split(",")
  cmdarr[0] = cmdarr[0].strip().lower()
  if cmdarr[0].strip().lower() in ["gpio","pwm","pulse","longpulse","tone","rtttl"]:
   res = gpiohelper.gpio_commands(cmd)
  return res
