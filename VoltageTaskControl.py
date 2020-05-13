import tkinter as tk
from tkinter import ttk, filedialog
import nidaqmx
import nidaqmx.stream_readers
import nidaqmx.constants as cts
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

### dictionary for nidaqmx constants
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
root = tk.Tk()
root.winfo_toplevel().title('NiDAQmx Controller')
root.tk_setPalette(background='white')
### Important Variables ###
##Setting Variables
channel_list = []
max_InputRange = tk.StringVar(root, value=10)
min_InputRange = tk.StringVar(root, value=-10)
##Timing Variables
acquisition_mode = tk.StringVar(root, value='Continuous Samples')
samples_to_read = tk.StringVar(root, value='90000')
rate = tk.StringVar(root, value='10000')
##Triggering Variables
#Start trigger
stt_trigger_source = tk.StringVar(root, value='APFI0')
stt_trigger_type = tk.StringVar(root, value='<None>')
stt_trigger_slope = tk.StringVar(root, value='Rising')
stt_trigger_level = tk.StringVar(root, value='0')
stt_window_top = tk.StringVar(root, value='0')
stt_window_bot = tk.StringVar(root, value='0')
stt_trigger_condition = tk.StringVar(root, value='Entering Window')
stt_trigger_edge = tk.StringVar(root, value='Rising')
#Reference Trigger
ref_trigger_source = tk.StringVar(root, value='APFI0')
ref_trigger_type = tk.StringVar(root, value='<None>')
ref_trigger_slope = tk.StringVar(root, value='Rising')
ref_trigger_level = tk.StringVar(root, value='0')
ref_window_top = tk.StringVar(root, value='0')
ref_window_bot = tk.StringVar(root, value='0')
ref_trigger_condition = tk.StringVar(root, value='Entering Window')
ref_trigger_edge = tk.StringVar(root, value='Rising')
preTriggerSamples = tk.StringVar(root, value='10000')
## Advanced Timing Variables
timeout = tk.StringVar(root, value=10)
##Logging Variables
TDMSLogging = tk.IntVar(root)
TDMS_filepath = tk.StringVar(root)
append = tk.IntVar()
logging_mode = tk.StringVar(root, value='Log and Read')
group_name = tk.StringVar(root)
sample_per_file = tk.StringVar(root, value='0')
span = tk.IntVar(root)

# Channel class:
class Channel():
    channelsInTask = []
    def __new__(cls, *, name):
        for channel in cls.channelsInTask:
            if channel.name == name:
                print('channel already in task')
                return channel
        x = super(Channel, cls).__new__(cls)
        return x

    def __init__(self, *, name):
        self.name = name
        self.max_InputRange = tk.StringVar(root, value=10)
        self.min_InputRange = tk.StringVar(root, value=-10)
        Channel.channelsInTask.append(self)

    def find(name):
        for channel in Channel.channelsInTask:
            if channel.name == name:
                return channel
        return None

    def __repr__(self):
        dict_ = {'name': self.name, 'max': self.max_InputRange.get(), 
                 'min': self.min_InputRange.get()}
        return dict_.__repr__()

    def remove(channel_name):
        for channel in Channel.channelsInTask:
            if channel.name == channel_name:
                Channel.channelsInTask.remove(channel)

    def channels_import(channels):
        for channel in channels:
            c = Channel(name=channel['name'])
            c.max_InputRange.set(channel['max'])
            c.min_InputRange.set(channel['min'])

# Run task function
def run():
    task = nidaqmx.Task()
    for channel in Channel.channelsInTask:
        min_val = int(channel.min_InputRange.get())
        max_val = int(channel.max_InputRange.get())
        task.ai_channels.add_ai_voltage_chan(channel.name, min_val=min_val, max_val=max_val)
    stt_triggerType = stt_trigger_type.get()
    ref_triggerType = ref_trigger_type.get()
    samp_clk_src = 'Dev3/ai0'
    samples = int(samples_to_read.get())
    task.timing.cfg_samp_clk_timing(int(rate.get()),
                                    sample_mode=dict_[acquisition_mode.get()],
                                    samps_per_chan=samples
                                    )
    if stt_triggerType == 'Analog Edge':
        task.triggers.start_trigger.cfg_anlg_edge_start_trig(trigger_source=stt_trigger_source.get(),
                                                             trigger_slope=dict_[stt_trigger_slope.get()],
                                                             trigger_level=float(stt_trigger_level.get())
                                                             )
    elif stt_triggerType == 'Analog Window':
        task.triggers.start_trigger.cfg_anlg_window_start_trig(trigger_source=stt_trigger_source.get(),
                                                               window_top=float(stt_window_top.get()),
                                                               window_bottom=float(stt_window_bot.get()),
                                                               trigger_when=dict_[stt_trigger_condition.get()]
                                                               )
    elif stt_triggerType == 'Digital Edge':
        task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=stt_trigger_source.get(),
                                                            trigger_edge=dict_[stt_trigger_edge.get()]
                                                            )
    if ref_triggerType == 'Analog Edge':
        task.triggers.reference_trigger.cfg_anlg_edge_ref_trig(trigger_source=ref_trigger_source.get(),
                                                         pretrigger_samples=int(preTriggerSamples.get()),
                                                         trigger_slope=dict_[ref_trigger_slope.get()],
                                                         trigger_level=float(ref_trigger_level.get())
                                                         )
    elif ref_triggerType == 'Analog Window':
        task.triggers.reference_trigger.cfg_anlg_window_ref_trig(trigger_source=ref_trigger_source.get(),
                                                               window_top=float(ref_window_top.get()),
                                                               window_bottom=float(ref_window_bot.get()),
                                                               pretrigger_samples=int(preTriggerSamples.get()),
                                                               trigger_when=dict_[ref_trigger_condition.get()]
                                                               )
    elif ref_triggerType == 'Digital Edge':
        task.triggers.reference_trigger.cfg_dig_edge_ref_trig(trigger_source=ref_trigger_source.get(),
                                                        pretrigger_samples=int(preTriggerSamples.get()),
                                                        trigger_edge=dict_[ref_trigger_edge.get()]
                                                        )
    if TDMSLogging.get():
        if append.get():
            operation = 'open'
        else:
            operation = 'create'
        task.in_stream.configure_logging(TDMS_filepath.get(), logging_mode=dict_[logging_mode.get()], 
                                         group_name=group_name.get(), operation=dict_[operation])
        task.in_stream.logging_samps_per_file = int(sample_per_file.get())*span.get()
    r = task.read(number_of_samples_per_channel=samples, timeout=float(timeout.get()))
    data = pd.DataFrame(r)
    if len(channel_list) > 1:
        data = data.transpose()
        data.columns = channel_list
    data.plot()
    plt.show()
    task.close()

# Decorative Frame
class BDFrame(tk.Frame):
    'docstring for BDFrame'
    def __init__(self, root_, title):
        super(BDFrame, self).__init__(root_)
        self['highlightbackground'] = 'light steel blue'
        self['highlightcolor'] = 'light steel blue'
        self['highlightthickness'] = 1
        self.parent = root_
        self.title = title
        self.label = tk.Label(self.parent, text=self.title, fg='dodger blue')

    def pack(self):
        super(BDFrame, self).pack(padx=10, pady=10, fill=tk.BOTH)
        root.update()
    def set_title(self):
        root.update()
        x = self.winfo_x()
        y = self.winfo_y()
        self.label.place(x=x+10, y=y-10)

#NoteBook tab change envent
def tab_change(event):
    index = event.widget.index('current')
    if index == 1:
        triggerChanged('')
        refTriggerChanged('')
        stt_tg_widgets[0].pack(fill=tk.BOTH)
        root.update()
        height = frame4.winfo_height()
        width = frame4.winfo_width()
        stt_tg_widgets[0].pack_forget()
        frame4.pack_propagate(False)
        frame4['height'] = height
        frame5.pack_propagate(False)
        frame5['height'] = height
        root.update()
        frame4.set_title()
        frame5.set_title()
        if acquisition_mode.get() == 'Continuous Samples':
            ref_TgOptions['state'] = tk.DISABLED
            ref_trigger_type.set('<None>')
            refTriggerChanged('')
            # print(ref_tg_widgets[4]['state'])
        else:
            ref_TgOptions['state'] = tk.NORMAL
    elif index == 2:
        frame6.set_title()
        frame7.set_title()
    elif index == 3:
        frame8.set_title()
        enable_logging()

tab_parent = ttk.Notebook(root)
tab_parent.bind('<<NotebookTabChanged>>', tab_change)
# ttk.Style().configure('')

tab1 = tk.Frame(tab_parent)
tab2 = tk.Frame(tab_parent)
tab3 = tk.Frame(tab_parent)
tab4 = tk.Frame(tab_parent)

tab_parent.add(tab1, text='Configuration')
tab_parent.add(tab2, text='Triggering')
tab_parent.add(tab3, text='Advanced Timing')
tab_parent.add(tab4, text='Logging')

tab_parent.pack()

# Run Task Button
run_frame = tk.Frame(root, padx=20, pady=10)
run_frame.pack(fill=tk.BOTH)
tk.Button(run_frame, text='Run', width=10, command=run).pack(side='right')

'''tab1 - Configuration Tab'''
frame1 = BDFrame(tab1, 'Channel Settings')
frame1.pack()
cs_frame = tk.Frame(frame1)
cs_frame.pack(padx=10, pady=10, fill=tk.BOTH)
frame2 = BDFrame(tab1, 'Timing Settings')
frame2.pack()
ts_frame = tk.Frame(frame2)
ts_frame.pack(padx=10, pady=10)

#Channel Setting Frame
clist = tk.Frame(cs_frame)
clist.pack(side=tk.LEFT)

### Add channel function
def add_channel():
    def add_function():
        channel_name = '{}/{}'.format(device_name.get(), dev_channel.get())
        if Channel.find(channel_name) == None:
            channel = Channel(name=channel_name)
            channel_list.append(channel_name)
            channel_list.sort()
            lb.delete(0, tk.END)
            lb.insert(tk.END, *channel_list)
            max_Input['textvariable'] = channel.max_InputRange
            min_Input['textvariable'] = channel.min_InputRange
    add_window = tk.Toplevel(root)
    tk.Label(add_window, text='Device Name:').pack()
    device_name = tk.StringVar(root, value='Dev3')
    tk.Entry(add_window, justify=tk.CENTER, textvariable=device_name).pack()
    tk.Label(add_window, text='Channel:').pack()
    dev_channel = tk.StringVar(root, value='ai0')
    channels_numbers = ['ai{}'.format(str(i)) for i in range(10)]
    tk.OptionMenu(add_window, dev_channel, *channels_numbers).pack()
    tk.Button(add_window, text='add channel', command=add_function).pack()

tk.Button(clist, text='Add', command=add_channel).grid(row=0, column=0, sticky='we')
### Remove channel function
def remove_channel():
    index = lb.curselection()[0]
    name = channel_list.pop(index)
    Channel.remove(name)
    lb.delete(0, tk.END)
    lb.insert(tk.END, *channel_list)

tk.Button(clist, text='Rem', command=remove_channel).grid(row=0, column=1, sticky='we')
### selecting a channel
def select_channel(event):
    if len(lb.curselection()) > 0:
        index = lb.curselection()[0]
        channel_name = channel_list[index]
        channel = Channel.find(channel_name)
        max_Input['textvariable'] = channel.max_InputRange
        min_Input['textvariable'] = channel.min_InputRange
        root.update()

lb = tk.Listbox(clist)
lb.bind('<<ListboxSelect>>', select_channel)
lb.grid(row=1, column=0, columnspan=4)

csetup = tk.Frame(cs_frame)
csetup.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
tk.Label(csetup, text='Voltage Input Setup', font=('Helvetica',14), anchor='w').pack(side=tk.TOP, fill=tk.BOTH)
voltage_IS = ttk.Notebook(csetup)

setting_tab = tk.Frame(voltage_IS)
calibration_tab = tk.Frame(voltage_IS)

voltage_IS.add(setting_tab, text='Settings')
voltage_IS.add(calibration_tab, text='Calibration')

voltage_IS.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

frame3 = BDFrame(setting_tab, 'Signal Input Range')
frame3.pack()
SIRange_frame = tk.Frame(frame3)
SIRange_frame.pack(padx=10, pady=10, fill=tk.BOTH)
tk.Label(SIRange_frame, text='Max').grid()
tk.Label(SIRange_frame, text='Min').grid()
max_Input = tk.Entry(SIRange_frame, width=10, justify='right', textvariable=max_InputRange)
max_Input.grid(row=0, column=1, pady=5)
min_Input = tk.Entry(SIRange_frame, width=10, justify='right', textvariable=min_InputRange)
min_Input.grid(row=1, column=1)

#Time Setting Frame
tk.Label(ts_frame, text='Acquisition Mode', anchor='w').grid(row=0, column=0, padx=5, sticky='we')
tk.Label(ts_frame, text='Sample to Read', anchor='w').grid(row=0, column=1, padx=5, sticky='we')
tk.Label(ts_frame, text='Rate (Hz)', anchor='w').grid(row=0, column=2, padx=5, sticky='we')

aquisition_options = ['1 Sample (On Demand)', '1 Sample (HW Timed)', 'N Samples', 'Continuous Samples']
AqOptions = tk.OptionMenu(ts_frame, acquisition_mode, *aquisition_options)
AqOptions.config(width=25)
AqOptions.grid(row=1, column=0, padx=5)

tk.Entry(ts_frame, textvariable=samples_to_read, justify='right').grid(row=1, column=1, padx=5, sticky='we')
tk.Entry(ts_frame, textvariable=rate, justify='right').grid(row=1, column=2, padx=5, sticky='we')

frame1.set_title()
frame2.set_title()
frame3.set_title()


'''tab2 - Triggering Tab'''
frame4 = BDFrame(tab2, 'Start Trigger')
frame4.pack()
st_frame = tk.Frame(frame4)
st_frame.pack(padx=10, pady=10, fill=tk.BOTH)

frame5 = BDFrame(tab2, 'Reference Trigger')
frame5.pack()
rt_frame = tk.Frame(frame5)
rt_frame.pack(padx=10, pady=10, fill=tk.BOTH)

# Start Trigger Frame
def triggerChanged(event):
    global stt_tg_widgets
    new_choices = ['APFI0', 'APFI1'] + channel_list
    source = stt_trigger_source.get()
    for widget in stt_tg_widgets:
        widget.pack_forget()
        widget.grid_remove()
    if stt_trigger_type.get() != '<None>':
        stt_tg_widgets[3].grid(row=0, column=1, padx=5, sticky='we')
        stt_trigger_source.set('APFI0')
        stt_tg_widgets[4].grid(row=1, column=1, padx=5, sticky='we')
    if stt_trigger_type.get() == 'Analog Edge':
        stt_tg_widgets[0].pack(fill=tk.BOTH)
    elif stt_trigger_type.get() == 'Analog Window':
        stt_tg_widgets[1].pack(fill=tk.BOTH)
    elif stt_trigger_type.get() == 'Digital Edge':
        stt_trigger_source.set('PFI0')
        stt_tg_widgets[2].pack(fill=tk.BOTH)
        new_choices = ['PFI{}'.format(i) for i in range(16)]
    stt_tg_widgets[4]['menu'].delete(0, 'end')
    for choice in new_choices:
        stt_tg_widgets[4]['menu'].add_command(label=choice, command=tk._setit(stt_trigger_source, choice))
    if source in new_choices:
        stt_trigger_source.set(source)

stt_tgType_frame = tk.Frame(st_frame)
stt_tgType_frame.pack(fill=tk.BOTH)
tk.Label(stt_tgType_frame, text='Trigger Type', anchor='w').grid(row=0, column=0, padx=5, sticky='we')
tg_options = ['<None>', 'Analog Edge', 'Analog Window', 'Digital Edge']
TgOptions = tk.OptionMenu(stt_tgType_frame, stt_trigger_type, *tg_options, command=triggerChanged)
TgOptions.config(width=15)
TgOptions.grid(row=1, column=0, padx=5, sticky='we')

stt_tg_widgets = [tk.Frame(st_frame) for i in range(3)]
stt_tg_widgets.append(tk.Label(stt_tgType_frame, text='Trigger Source', anchor='w'))
stt_tg_widgets.append(tk.OptionMenu(stt_tgType_frame, stt_trigger_source, 'APFI0', 'APFI1'))
stt_tg_widgets[-1].config(width=21)

## Analog Edge
tk.Label(stt_tg_widgets[0], text='Slope', anchor='w').grid(row=0, column=0, padx=5, sticky='we')
slope_menu = tk.OptionMenu(stt_tg_widgets[0], stt_trigger_slope, 'Rising', 'Falling')
slope_menu.config(width=11)
slope_menu.grid(row=1, column=0, padx=5, sticky='we')
tk.Label(stt_tg_widgets[0], text='Level', anchor='w').grid(row=0, column=1, padx=5, sticky='we')
tk.Entry(stt_tg_widgets[0], textvariable=stt_trigger_level, justify='right', width=15).grid(row=1, column=1, padx=5, sticky='we')
## Analog Window
tk.Label(stt_tg_widgets[1], text='Window Top', anchor='w').grid(row=0, column=0, padx=5, sticky='we')
tk.Entry(stt_tg_widgets[1], textvariable=stt_window_top, justify='right').grid(row=1, column=0, padx=5, sticky='we')
tk.Label(stt_tg_widgets[1], text='Window Bottom', anchor='w').grid(row=0, column=1, padx=5, sticky='we')
tk.Entry(stt_tg_widgets[1], textvariable=stt_window_bot, justify='right').grid(row=1, column=1, padx=5, sticky='we')
tk.Label(stt_tg_widgets[1], text='Trigger Condition', anchor='w').grid(row=0, column=2, padx=5, sticky='we')
condition_menu = tk.OptionMenu(stt_tg_widgets[1], stt_trigger_condition, 'Entering Window', 'Leaving Window')
condition_menu.config(width=25)
condition_menu.grid(row=1, column=2, padx=5, sticky='we')

## Digital Edge
tk.Label(stt_tg_widgets[2], text='Slope', anchor='w').grid(row=0, column=0, padx=5, sticky='we')
edge_menu = tk.OptionMenu(stt_tg_widgets[2], stt_trigger_edge, 'Rising', 'Falling')
edge_menu.config(width=11)
edge_menu.grid(row=1, column=0, padx=5, sticky='we')


# ref Trigger Frame
def refTriggerChanged(event):
    global ref_tg_widgets
    new_choices = ['APFI0', 'APFI1'] + channel_list
    source = ref_trigger_source.get()
    for widget in ref_tg_widgets:
        widget.pack_forget()
        widget.grid_remove()
    if ref_trigger_type.get() != '<None>':
        ref_tg_widgets[3].grid(row=0, column=1, padx=5, sticky='we')
        ref_trigger_source.set('APFI0')
        ref_tg_widgets[4].grid(row=1, column=1, padx=5, sticky='we')
        ref_tg_widgets[5].grid(row=0, column=2, padx=5, sticky='we')
        ref_tg_widgets[6].grid(row=1, column=2, padx=5, sticky='we')
    if ref_trigger_type.get() == 'Analog Edge':
        ref_tg_widgets[0].pack(fill=tk.BOTH)
    elif ref_trigger_type.get() == 'Analog Window':
        ref_tg_widgets[1].pack(fill=tk.BOTH)
    elif ref_trigger_type.get() == 'Digital Edge':
        ref_trigger_source.set('PFI0')
        ref_tg_widgets[2].pack(fill=tk.BOTH)
        new_choices = ['PFI{}'.format(i) for i in range(16)]
    ref_tg_widgets[4]['menu'].delete(0, 'end')
    for choice in new_choices:
        ref_tg_widgets[4]['menu'].add_command(label=choice, command=tk._setit(ref_trigger_source, choice))
    if source in new_choices:
        ref_trigger_source.set(source)

ref_tgType_frame = tk.Frame(rt_frame)
ref_tgType_frame.pack(fill=tk.BOTH)
tk.Label(ref_tgType_frame, text='Trigger Type', anchor='w').grid(row=0, column=0, padx=5, sticky='we')
ref_TgOptions = tk.OptionMenu(ref_tgType_frame, ref_trigger_type, *tg_options, command=refTriggerChanged)
ref_TgOptions.config(width=15)
ref_TgOptions.grid(row=1, column=0, padx=5, sticky='we')

ref_tg_widgets = [tk.Frame(rt_frame) for i in range(3)]
ref_tg_widgets.append(tk.Label(ref_tgType_frame, text='Trigger Source', anchor='w'))
ref_tg_widgets.append(tk.OptionMenu(ref_tgType_frame, ref_trigger_source, 'APFI0', 'APFI1', 'Voltage'))
ref_tg_widgets[-1].config(width=21)
ref_tg_widgets.append(tk.Label(ref_tgType_frame, text='Pre-Trigger Samples', anchor='w'))
ref_tg_widgets.append(tk.Entry(ref_tgType_frame, textvariable=preTriggerSamples))

## Analog Edge
tk.Label(ref_tg_widgets[0], text='Slope', anchor='w').grid(row=0, column=0, padx=5, sticky='we')
ref_slope_menu = tk.OptionMenu(ref_tg_widgets[0], ref_trigger_slope, 'Rising', 'Falling')
ref_slope_menu.config(width=11)
ref_slope_menu.grid(row=1, column=0, padx=5, sticky='we')
tk.Label(ref_tg_widgets[0], text='Level', anchor='w').grid(row=0, column=1, padx=5, sticky='we')
tk.Entry(ref_tg_widgets[0], textvariable=ref_trigger_level, justify='right', width=15).grid(row=1, column=1, padx=5, sticky='we')
## Analog Window
tk.Label(ref_tg_widgets[1], text='Window Top', anchor='w').grid(row=0, column=0, padx=5, sticky='we')
tk.Entry(ref_tg_widgets[1], textvariable=ref_window_top, justify='right').grid(row=1, column=0, padx=5, sticky='we')
tk.Label(ref_tg_widgets[1], text='Window Bottom', anchor='w').grid(row=0, column=1, padx=5, sticky='we')
tk.Entry(ref_tg_widgets[1], textvariable=ref_window_bot, justify='right').grid(row=1, column=1, padx=5, sticky='we')
tk.Label(ref_tg_widgets[1], text='Trigger Condition', anchor='w').grid(row=0, column=2, padx=5, sticky='we')
ref_condition_menu = tk.OptionMenu(ref_tg_widgets[1], ref_trigger_condition, 'Entering Window', 'Leaving Window')
ref_condition_menu.config(width=25)
ref_condition_menu.grid(row=1, column=2, padx=5, sticky='we')

## Digital Edge
tk.Label(ref_tg_widgets[2], text='Slope', anchor='w').grid(row=0, column=0, padx=5, sticky='we')
ref_edge_menu = tk.OptionMenu(ref_tg_widgets[2], ref_trigger_edge, 'Rising', 'Falling')
ref_edge_menu.config(width=11)
ref_edge_menu.grid(row=1, column=0, padx=5, sticky='we')

'''tab3 - Advanced Timing Tab'''
frame6 = BDFrame(tab3, 'Sample Clock Settings')
frame6.pack()
scs_frame = tk.Frame(frame6)
scs_frame.pack(padx=10, pady=10, fill=tk.BOTH)
frame7 = BDFrame(tab3, 'Additional Time Settings')
frame7.pack()
ats_frame = tk.Frame(frame7)
ats_frame.pack(padx=10, pady=10, fill=tk.BOTH)

tk.Label(scs_frame, text='Sample Clock Type', anchor='w').grid(row=0, column=0, padx=5, sticky='we')
clock_type = tk.StringVar(root, value='Internal')
clockType_menu = tk.OptionMenu(scs_frame, clock_type, 'Internal')
clockType_menu.config(width=11)
clockType_menu.grid(row=1, column=0, padx=5, sticky='we')

tk.Label(scs_frame, text='Clock Source', anchor='w').grid(row=2, column=0, padx=5, sticky='we')
clock_source = tk.StringVar(root, value='PFI0')
clockSource_menu = tk.OptionMenu(scs_frame, clock_source, 'PFI0')
clockSource_menu.config(width=19, state=tk.DISABLED)
clockSource_menu.grid(row=3, column=0, columnspan=2, padx=5, sticky='we')

tk.Label(scs_frame, text='Active Edge', anchor='w').grid(row=2, column=2, padx=5, sticky='we')
clock_type = tk.StringVar(root, value='Falling')
clockType_menu = tk.OptionMenu(scs_frame, clock_type, 'Rising', 'Falling')
clockType_menu.config(width=11, state=tk.DISABLED)
clockType_menu.grid(row=3, column=2, padx=5, sticky='we')

tk.Label(ats_frame, text='Timeout (s)', anchor='w').grid(padx=5, sticky='w')
ttk.Spinbox(ats_frame, from_=-1, to=10000, textvariable=timeout, width=10, justify='right').grid(padx=5, sticky='w')

'''tab4 - Logging Tab'''
frame8 = BDFrame(tab4, 'TDMS File Logging')
frame8.pack()
tdms_frame = tk.Frame(frame8)
tdms_frame.pack(padx=10, pady=10, fill=tk.BOTH)

def enable_logging():
    if TDMSLogging.get() == 1:
        for widget in file_frame.winfo_children():
            try:
                widget.config(state=tk.NORMAL)
            except:
                pass
            span_files_function()
    else:
        for widget in file_frame.winfo_children():
            try:
                widget.config(state=tk.DISABLED)
            except:
                pass
            spanEntry['state'] = tk.DISABLED
            spanLabel['state'] = tk.DISABLED
            

tk.Checkbutton(tdms_frame, text='Enable TDMS Logging', var=TDMSLogging, command=enable_logging, anchor='w').pack(padx=5, fill=tk.BOTH)

file_frame = tk.Frame(tdms_frame, highlightbackground='light steel blue', highlightcolor='light steel blue', highlightthickness=1)
file_frame.pack(padx=5, pady=5, ipady=5, fill=tk.BOTH)

def search_file():
    TDMS_filepath.set(filedialog.asksaveasfilename(title = 'Select file', 
                                                   filetypes = (('TDMS files','*.tdms'),
                                                                ('TDM files','*.tdm'),
                                                                ('all files','*.*')
                                                                )))
tk.Label(file_frame, text='File Path', anchor='w').grid(padx=5, sticky='we')
tk.Entry(file_frame, textvariable=TDMS_filepath).grid(padx=5, sticky='we')
tk.Button(file_frame, text='Search', command=search_file).grid(row=1, column=1)
tk.Checkbutton(file_frame, text='Append data if file exists', variable=append).grid(padx=5, sticky='w')

tk.Label(file_frame, text='Logging Mode', anchor='w').grid(padx=5, sticky='we')
logginMode_menu = tk.OptionMenu(file_frame, logging_mode, 'Log and Read', 'Log Only')
logginMode_menu.config(width=11)
logginMode_menu.grid(padx=5, sticky='we')

def span_files_function():
    if not span.get():
        spanEntry['state'] = tk.DISABLED
        spanLabel['state'] = tk.DISABLED
    else:
        spanEntry['state'] = tk.NORMAL
        spanLabel['state'] = tk.NORMAL
tk.Label(file_frame, text='Group Name', anchor='w').grid(padx=5, sticky='we')
tk.Entry(file_frame, textvariable=group_name).grid(padx=5, sticky='we')
tk.Checkbutton(file_frame, text='Span multiple files', variable=span, command=span_files_function).grid(padx=5, sticky='w')
smf_frame = tk.Frame(file_frame)
smf_frame.grid(padx=30)
spanLabel = tk.Label(smf_frame, text='Samples Per File', anchor='w')
spanLabel.grid(sticky='we')
spanEntry = tk.Entry(smf_frame, textvariable=sample_per_file)
spanEntry.grid(sticky='we')

def variables_list():
    variables = [
                acquisition_mode,
                samples_to_read,
                rate,
            #Start Trigger
                stt_trigger_source,
                stt_trigger_type,
                stt_trigger_slope,
                stt_trigger_level,
                stt_window_top,
                stt_window_bot,
                stt_trigger_condition,
                stt_trigger_edge,
            #Reference Trigger
                ref_trigger_source,
                ref_trigger_type,
                ref_trigger_slope,
                ref_trigger_level,
                ref_window_top,
                ref_window_bot,
                ref_trigger_condition,
                ref_trigger_edge,
                preTriggerSamples,
            ## Advanced Timing Variables
                timeout,
            ##Logging Variables
                TDMSLogging,
                TDMS_filepath,
                append,
                logging_mode,
                group_name,
                sample_per_file,
                span]
    return variables

def save_task():
    path = filedialog.asksaveasfilename(title = 'Select file', defaultextension='.task',
                                        filetypes = (('task','*.task'),('all files','*.*')))
    file = open(path, 'w')
    variables = list(map(lambda x: str(x.get()), variables_list()))
    file.write('\n'.join(variables) + '\n')
    file.write(Channel.channelsInTask.__repr__())
    file.close()

def open_task():
    global channel_list
    variables = variables_list()
    path=filedialog.askopenfilename(title = 'Select file', 
                                    filetypes = (('task','*.task'),('all files','*.*')))
    file = open(path, 'r')
    for variable in variables_list():
        variable.set(file.readline().replace('\n',''))
    channels = file.readline().replace("'",'"')
    file.close()
    channel_list = []
    Channel.channelsInTask = []
    Channel.channels_import(json.loads(channels))
    for channel in Channel.channelsInTask:
        channel_list.append(channel.name)
    channel_list.sort()
    print(channel_list)
    lb.delete(0, tk.END)
    lb.insert(tk.END, *channel_list)
    max_InputRange.set('')
    min_InputRange.set('')

''' Menu '''
menubar = tk.Menu(root)
root.config(menu=menubar)

filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label = 'Save Task', command = save_task)
filemenu.add_command(label = 'Open Task', command = open_task)
filemenu.add_command(label = 'Exit', command = root.destroy)
menubar.add_cascade(label = 'File', menu = filemenu)

root.mainloop()