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
        return self.__value.__repr__()

    def __eq__(self, other):
        return self.__value == other

        
class _RawTrigger(object):
    """Support class for start and reference triggers"""
    def __init__(self):
        self.source = _Config('APFI0', 'APFI0', 'APFI1')
        self.type = _Config('<None>', '<None>', 'Analog Edge', 
                            'Analog Window', 'Digital Edge')
        self.slope = _Config('Rising', 'Rising', 'Falling')
        self.level = _Config(0)
        self.wtop = _Config(0)
        self.wbot = _Config(0)
        self.condition = _Config('Entering Window', 
                                 'Entering Window', 'Leaving Window')
        self.edge = _Config('Rising', 'Rising', 'Falling')

class StartTrigger(_RawTrigger):
    """Start trigger configuration"""
    def __init__(self):
        super(StartTrigger, self).__init__()

    def __repr__(self):
        return 'Start Trigger'

class RefTrigger(_RawTrigger):
    """Reference trigger configuration"""
    def __init__(self):
        super(RefTrigger, self).__init__()
        self.source.options.append('Voltage')
        self.presamp = _Config(10000)

    def __repr__(self):
        return 'Reference Trigger'

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
    ChannelList 'clist' when created. The Channel object can 
    only be created if there is no other Channel with the 
    same name in the clist.
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
    """
    A simplified version for the nidaqmx Task, which represents a DAQmx Task.
    
    A Task object can be used to read or write data through a DAQ board.
    It has an implicit list of channels and initial configuration for 
    triggering, timing and logging. 
    - New channels can be added to the task by the method add_channel()
    - The list of setup attributes can be queried using the built in __dict__ 
    attribute.
    - Start and Reference Triggers are objects. All others non-integer setup 
    attributes have a list of valid entrances that may be queried using the 
    attribute.options (ex. task.acquisition_mode.options) however there is no 
    validation method, thus always be sure to enter correct values.
    - After setting attributes and/or adding/editing channels the method config
    must be called before reading or writing the task, or changes will not be
    applied.
    - Taks must be explicitly close to ensure that no resource will still be 
    reserved. In case that tasks were not properly closed and the device cannot
    be accessed anymore, the device may be reseted by the NI-MAX software.
    
    ***IMPORTANT: The Task class is not child of the nidaqmx.Task, thus it 
    does not accept nidaqmx.Task methods, however Taks.nitask does.
    """
    def __init__(self):
        super(Task, self).__init__()
        self.nitask = None
        ##Setting Variables
        self.clist = _ChannelList()
        self.mode = None
        ##Timing Variables
        self.acquisition_mode = _Config('Continuous Samples', 
                                   '1 Sample (On Demand)', 
                                   '1 Sample (HW Timed)', 
                                   'N Samples', 
                                   'Continuous Samples')
        self.samples_per_channel = _Config(1000)
        self.rate = _Config(10000)
        ## Triggering Variables
        self.stt_trigger = StartTrigger()
        self.ref_trigger = RefTrigger()
        ## Advanced Timing Variables
        self.timeout = _Config(10)
        self.clock_type = _Config('Internal', 'Internal')
        self.clock_source = _Config('PFI0', 'PFI0')
        self.active_edge = _Config('Falling', 'Rising', 'Falling')
        ##Logging Variables
        self.tdmsLogging = _Config(None)
        self.tdmsFilepath = _Config(None)
        self.append_data = _Config(None)
        self.logging_mode = _Config('Log and Read', 'Log and Read', 'Log Only')
        self.group_name = _Config(None)
        self.sample_per_file = _Config(0)
        self.span = _Config(None)

    def add_channel(self, cname, *, maxInputRange=10, minInputRange=-10):
        channel = Channel(self.clist, cname, maxInputRange, minInputRange)
        if 'ai' in cname:
            channel.type = 'analog input'
        elif 'ao' in cname:
            channel.type = 'analog output'
        return channel

    def importChannels(self, channels):
        for channel in channels:
            c = Channel(self.clist, channel['name'], 
                        channel['max'], channel['min'])

    def config(self, *, timing='intrinsic'):
        if self.nitask:
            self.nitask.close()
        self.nitask = nidaqmx.Task()
        # Add channels to Task
        for channel in self.clist:
            if channel.name not in self.nitask.channel_names:
                if channel.type == 'analog input':
                    self.nitask.ai_channels.add_ai_voltage_chan(
                        channel.name, 
                        min_val=channel.minInputRange,
                        max_val=channel.maxInputRange)
                elif channel.type == 'analog output':
                    self.nitask.ao_channels.add_ao_voltage_chan(
                        channel.name, 
                        min_val=channel.minInputRange,
                        max_val=channel.maxInputRange)
        # Set task timing
        if timing == 'on_demand':
            self.nitask.timing.samp_timing_type=cts.SampleTimingType.ON_DEMAND
        else:
            self.nitask.timing.cfg_samp_clk_timing(
                self.rate.get(),
                sample_mode=dict_[self.acquisition_mode.get()],
                samps_per_chan=self.samples_per_channel.get())
        # Set start trigger configuration
        if self.stt_trigger.type == 'Analog Edge':
            self.nitask.triggers.start_trigger.cfg_anlg_edge_start_trig(
                trigger_source=self.stt_trigger.source.get(),
                trigger_slope=dict_[self.stt_trigger.slope.get()],
                trigger_level=self.stt_trigger.level.get())
        elif self.stt_trigger.type == 'Analog Window':
            self.nitask.triggers.start_trigger.cfg_anlg_window_start_trig(
                trigger_source=self.stt_trigger.source.get(),
                window_top=self.stt_trigger.window_top.get(),
                window_bottom=self.stt_trigger.window_botget(),
                trigger_when=dict_[self.stt_trigger.condition.get()])
        elif self.stt_trigger.type == 'Digital Edge':
            self.nitask.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source=self.stt_trigger.source.get(),
                trigger_edge=dict_[self.stt_trigger.edge.get()])
        # Set reference trigger configuration
        if self.ref_trigger.type == 'Analog Edge':
            self.nitask.triggers.reference_trigger.cfg_anlg_edge_ref_trig(
                trigger_source=self.ref_trigger.source.get(),
                pretrigger_samples=self.ref_trigger.preTriggerSamples.get(),
                trigger_slope=dict_[self.ref_trigger.slope.get()],
                trigger_level=self.ref_trigger.level.get())
        elif self.ref_trigger.type == 'Analog Window':
            self.nitask.triggers.reference_trigger.cfg_anlg_window_ref_trig(
                trigger_source=self.ref_trigger.source.get(),
                window_top=self.ref_trigger.window_top.get(),
                window_bottom=self.ref_trigger.window_bot.get(),
                pretrigger_samples=self.ref_trigger.preTriggerSamples.get(),
                trigger_when=dict_[self.ref_trigger.condition.get()])
        elif self.ref_trigger.type == 'Digital Edge':
            self.nitask.triggers.reference_trigger.cfg_dig_edge_ref_trig(
                trigger_source=self.ref_trigger.source.get(),
                pretrigger_samples=self.ref_trigger.preTriggerSamples.get(),
                trigger_edge=dict_[self.ref_trigger.edge.get()])
        # Set TDMS Loggin configuration
        if self.tdmsLogging.get():
            loggin_samples = self.sample_per_file.get()*self.span.get()
            if self.append_data.get():
                operation = 'open'
            else:
                operation = 'create'
            self.nitask.in_stream.configure_logging(
                self.tdmsFilepath.get(), 
                logging_mode=dict_[self.logging_mode.get()],
                group_name=self.group_name.get(), 
                operation=dict_[operation])
            self.nitask.in_stream.logging_samps_per_file = loggin_samples

    def read(self):
        '''Read the task and returns a numpy array'''
        if self.nitask is None:
            raise TaskError('Task must be configured before read. Try to use '\
                            'task.config() before task.read()')
        r = self.nitask.read(
            number_of_samples_per_channel=self.samples_per_channel.get(),
            timeout=self.timeout.get())
        return np.array(r)

    def write(self, data):
        error = None
        try:
            self.nitask.write(data)
        except nidaqmx.errors.DaqError as err:
            if err.error_code == -200547:
                error = TaskError('buffer size is defined to {} by default. '\
                    'Try to increase the value of samples_per_channel or '\
                    'configure timing to on_demand with task.config(timing='\
                    '"on_demand")'.format(self.samples_per_channel))
            else: 
                error=err
        if error:
            raise error
            
    def start(self):
        if self.nitask:
            self.nitask.start()
        else:
            raise TaskError('It is impossible to start a task that was not '\
                            'previously configured. Try to use task.config() '\
                            'first')

    def stop(self):
        if self.nitask:
            self.nitask.stop()
        else:
            raise TaskError('It is impossible to stop a task that was not '\
                            'configured yet. Try to use task.config() first')

    def close(self):
        if self.nitask:
            self.nitask.close()
            self.nitask = None

class TaskError(Exception):
    def __init__(self, message):
        # self.expression = expression
        self.message = message
        

if __name__ == '__main__':
    task=Task()
    # print(task.__dict__)
    # print(task.acquisition_mode.options)
    task.add_channel('dev3/ai0')
    task.add_channel('dev3/ai1')
    task.config()
    task.read()
    channel = task.nitask.channels
    print(task.nitask.channels.chan_type)
    task.config()

    print(channel.name)
    task.close()