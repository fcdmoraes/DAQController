import tkinter as tk
from tkinter import ttk, filedialog
import nidaqmx
import nidaqmx.stream_readers
import nidaqmx.constants as cts
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

# A dictionary to convert string inputs into nidaqmx constants
dict_ = {'Rising': cts.Slope.RISING,
         'Falling': cts.Slope.FALLING,
         'Continuous Samples': cts.AcquisitionType.CONTINUOUS,
         'N Samples': cts.AcquisitionType.FINITE,
         '1 Sample (HW Timed)': cts.AcquisitionType.HW_TIMED_SINGLE_POINT,
         'Entering Window': cts.WindowTriggerCondition1.ENTERING_WINDOW,
         'Leaving Window': cts.WindowTriggerCondition1.LEAVING_WINDOW,
         'Log Only': cts.LoggingMode.LOG,
         'Log and Read': cts.LoggingMode.LOG_AND_READ,
         'create': cts.LoggingOperation.CREATE_OR_REPLACE,
         'open': cts.LoggingOperation.OPEN_OR_CREATE,
         }

class _Config(object):
    """Support class to tkinter OptionMenu, that can keep not only
    selected value but also a list of valid options.
    """
    def __init__(self, value, *options):
        self.__value = value
        self.options = list(options)
    
    def set(self, value: str):
        self.__value = value

    def get(self):
        return self.__value

    def __repr__(self):
        return self.__value

        
class _RawTrigger(object):
    """Support class for start and reference triggers"""
    def __init__(self):
        self.source = _Config('APFI0', 'APFI0', 'APFI1')
        self.type = _Config('<None>', '<None>', 'Analog Edge', 
                            'Analog Window', 'Digital Edge')
        self.slope = _Config('Rising', 'Rising', 'Falling')
        self.level = 0
        self.window_top = 0
        self.window_bot = 0
        self.condition = _Config('Entering Window', 
                                 'Entering Window', 'Leaving Window')
        self.edge = _Config('Rising', 'Rising', 'Falling')

class StartTrigger(_RawTrigger):
    """Start trigger configuration"""
    def __init__(self):
        super(StartTrigger, self).__init__()

class RefTrigger(_RawTrigger):
    """Reference trigger configuration"""
    def __init__(self):
        super(RefTrigger, self).__init__()
        self.source.options.append('Voltage')
        preTriggerSamples = '10000'

class _ChannelList(list):
    """A singleton list of channels to be added to the task 
    before executing the task.

    Channels are object that are automatically added to the 
    ChannelList when created. The Channel object can only be 
    created if there is no other Channel with the same name 
    in the ChannelList.
    """
    def __init__(self):
        super(_ChannelList, self).__init__
        self.names = []

    def find(self, name):
        for channel in self:
            if channel.name == name:
                return channel
        return None 

    def pop(self, index):
        channel_name = self.names.pop(index)
        self.remove(channel_name)

    def remove(self, channel_name):
        for channel in self:
            if channel.name == channel_name:
                super(_ChannelList, self).remove(channel)

    def append(self, channel):
        super(_ChannelList,self).append(channel)
        self.names.append(channel.name)
        self.names.sort()

    def clear(self):
        self.names.clear()
        super(_ChannelList, self).clear()

class Channel(object):
    """Create a Channel to be included in the DAQ Task.

    Channels are object that are automatically added to the 
    ChannelList clist when created. The Channel object can 
    only be created if there is no other Channel with the 
    same name in the list.
    """
    def __new__(cls, clist, name, *kwargs):
        if not clist.find(name):
            x = super(Channel, cls).__new__(cls)
            return x 
        print('channel <{}> already in task'.format(name))
        return None    

    def __init__(self, clist, name, maxInputRange, minInputRange):
        self.name = name
        self.maxInputRange = maxInputRange
        self.minInputRange = minInputRange
        clist.append(self)

    def __repr__(self):
        dict_ = {'name': self.name, 'max': self.maxInputRange, 
                 'min': self.minInputRange}
        return dict_.__repr__()     

class Task():
    """docstring for Task"""

    def __init__(self, *arg):
        super(Task, self).__init__()
        self.arg = arg
        ##Setting Variables
        self.clist = _ChannelList()
        ##Timing Variables
        self.acquisition_mode = _Config('Continuous Samples', '1 Sample (On Demand)', 
                                   '1 Sample (HW Timed)', 'N Samples', 
                                   'Continuous Samples')
        self.samples_to_read = 90000
        self.rate = 10000
        ## Triggering Variables
        self.stt_trigger = StartTrigger()
        self.ref_trigger = RefTrigger()
        ## Advanced Timing Variables
        self.timeout = 10
        self.clock_type = _Config('Internal', 'Internal')
        self.clock_source = _Config('PFI0', 'PFI0')
        self.active_edge = _Config('Falling', 'Rising', 'Falling')
        ##Logging Variables
        self.tdmsLogging = None
        self.tdmsFilepath = None
        self.append = None
        self.logging_mode = _Config('Log and Read', 'Log and Read', 'Log Only')
        self.group_name = None
        self.sample_per_file = '0'
        self.span = None

    def add_channel(self, *, cname, maxInputRange=10, minInputRange=-10):
        return Channel(self.clist, cname, maxInputRange, minInputRange)


    def importChannels(self, channels):
        for channel in channels:
            c = Channel(self.clist, channel['name'], 
                        channel['max'], channel['min'])

    def config(self):
        # Add channels to Task
        self.task = nidaqmx.Task()
        for channel in self.clist:
            self.task.ai_channels.add_ai_voltage_chan(
                channel.name, 
                min_val=channel.minInputRange,
                max_val=channel.maxInputRange)
        # Set task timing
        self.task.timing.cfg_samp_clk_timing(
            self.rate,
            sample_mode=dict_[self.acquisition_mode.get()],
            samps_per_chan=self.samples_to_read)
        # Set start trigger configuration
        if self.stt_trigger.type == 'Analog Edge':
            self.task.triggers.start_trigger.cfg_anlg_edge_start_trig(
                trigger_source=self.stt_trigger.source,
                trigger_slope=dict_[self.stt_trigger.slope.get()],
                trigger_level=self.stt_trigger.level)
        elif self.stt_trigger.type == 'Analog Window':
            self.task.triggers.start_trigger.cfg_anlg_window_start_trig(
                trigger_source=self.stt_trigger.source,
                window_top=self.stt_trigger.window_top,
                window_bottom=self.stt_trigger.window_bot,
                trigger_when=dict_[self.stt_trigger.condition.get()])
        elif self.stt_trigger.type == 'Digital Edge':
            self.task.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source=self.stt_trigger.source,
                trigger_edge=dict_[self.stt_trigger.edge.get()])
        # Set reference trigger configuration
        if self.ref_trigger.type == 'Analog Edge':
            self.task.triggers.reference_trigger.cfg_anlg_edge_ref_trig(
                trigger_source=self.ref_trigger.source,
                pretrigger_samples=self.ref_trigger.preTriggerSamples,
                trigger_slope=dict_[self.ref_trigger.slope.get()],
                trigger_level=self.ref_trigger.level)
        elif self.ref_trigger.type == 'Analog Window':
            self.task.triggers.reference_trigger.cfg_anlg_window_ref_trig(
                trigger_source=self.ref_trigger.source,
                window_top=self.ref_trigger.window_top,
                window_bottom=self.ref_trigger.window_bot,
                pretrigger_samples=self.ref_trigger.preTriggerSamples,
                trigger_when=dict_[self.ref_trigger.condition.get()])
        elif self.ref_trigger.type == 'Digital Edge':
            self.task.triggers.reference_trigger.cfg_dig_edge_ref_trig(
                trigger_source=self.ref_trigger.source,
                pretrigger_samples=self.ref_trigger.preTriggerSamples,
                trigger_edge=dict_[self.ref_trigger.edge.get()])
        # Set TDMS Loggin configuration
        if self.tdmsLogging:
            loggin_samples = self.sample_per_file*self.span
            if self.append:
                operation = 'open'
            else:
                operation = 'create'
            self.task.in_stream.configure_logging(
                self.tdmsFilepath, 
                logging_mode=dict_[self.logging_mode.get()],
                group_name=self.group_name, 
                operation=dict_[operation])
            self.task.in_stream.logging_samps_per_file = loggin_samples
    
    def acquire(self):
        r = self.read()
        return r

    def read(self):
        # Run Task
        r = self.task.read(
            number_of_samples_per_channel=self.samples_to_read,
            timeout=self.timeout)
        return np.array(r)

    def close(self):
        self.task.close()

if __name__ == '__main__':
    daq=Task()