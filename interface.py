import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import json
import sys

from controller import *

task = Task()

class GUIForm(QtWidgets.QWidget):
    '''Widget class for continuous mode data visualisation'''
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self,parent)
        self.close = False
        self.grid = QtWidgets.QGridLayout(self)
        self.chart = pg.PlotWidget()
        self.chart.plot()
        self.chart.setRange(QtCore.QRectF(0, -10, 100, 20))
        self.grid.addWidget(self.chart,0,0)
        self.show()

    def closeEvent(self, event):
        self.close = True
        event.accept() # let the window close

class Interface(tk.Tk):
    def __init__(self):
        super(Interface, self).__init__()
        self.winfo_toplevel().title('NiDAQmx Controller')
        self.set_menubar()
        self.tk_setPalette(background='white')

        # Setting Variables
        self.max_InputRange = tk.StringVar(self, value=10)
        self.min_InputRange = tk.StringVar(self, value=-10)
        # Timing Variables
        self.acquisition_mode = tk.StringVar(self, value='Continuous Samples')
        self.samples_to_read = tk.StringVar(self, value='90000')
        self.rate = tk.StringVar(self, value='10000')
        # Start trigger
        self.stt_trigger_source = tk.StringVar(self, value='APFI0')
        self.stt_trigger_type = tk.StringVar(self, value='<None>')
        self.stt_trigger_slope = tk.StringVar(self, value='Rising')
        self.stt_trigger_level = tk.StringVar(self, value='0')
        self.stt_window_top = tk.StringVar(self, value='0')
        self.stt_window_bot = tk.StringVar(self, value='0')
        self.stt_trigger_condition = tk.StringVar(self, 
                                                  value='Entering Window')
        self.stt_trigger_edge = tk.StringVar(self, value='Rising')
        # Reference Trigger
        self.ref_trigger_source = tk.StringVar(self, value='APFI0')
        self.ref_trigger_type = tk.StringVar(self, value='<None>')
        self.ref_trigger_slope = tk.StringVar(self, value='Rising')
        self.ref_trigger_level = tk.StringVar(self, value='0')
        self.ref_window_top = tk.StringVar(self, value='0')
        self.ref_window_bot = tk.StringVar(self, value='0')
        self.ref_trigger_condition = tk.StringVar(self, 
                                                  value='Entering Window')
        self.ref_trigger_edge = tk.StringVar(self, value='Rising')
        self.preTriggerSamples = tk.StringVar(self, value='10000')
        # Advanced Timing Variables
        self.timeout = tk.StringVar(self, value=10)
        # Logging Variables
        self.TDMSLogging = tk.IntVar(self)
        self.TDMS_filepath = tk.StringVar(self)
        self.append_data = tk.IntVar()
        self.logging_mode = tk.StringVar(self, value='Log and Read')
        self.group_name = tk.StringVar(self)
        self.sample_per_file = tk.StringVar(self, value='0')
        self.span = tk.IntVar(self)
        ### new:
        self.clock_type = tk.StringVar(self, value='Internal')
        self.clock_source = tk.StringVar(self, value='PFI0')
        self.active_edge = tk.StringVar(self, value='Falling')

        ### not in use
        self.scaled_units = tk.StringVar(self, value='Volts')

        self. variables = [self.acquisition_mode, self.samples_to_read, 
                           self.rate, self.stt_trigger_source, 
                           self.stt_trigger_type, self.stt_trigger_slope, 
                           self.stt_trigger_level, self.stt_window_top, 
                           self.stt_window_bot, self.stt_trigger_condition, 
                           self.stt_trigger_edge, self.ref_trigger_source, 
                           self.ref_trigger_type, self.ref_trigger_slope, 
                           self.ref_trigger_level, self.ref_window_top, 
                           self.ref_window_bot, self.ref_trigger_condition, 
                           self.ref_trigger_edge, self.preTriggerSamples, 
                           self.timeout, self.clock_type, self.clock_source, 
                           self.active_edge, self.TDMSLogging, 
                           self.TDMS_filepath, self.append_data, 
                           self.logging_mode, self.group_name, 
                           self.sample_per_file, self.span
                           ]

        self.notebook = MainNotebook(self)

        # Run Task Button
        self.run_frame = tk.Frame(self, padx=20, pady=10)
        self.run_frame.pack(fill=tk.BOTH)
        tk.Button(self.run_frame, text='Run',
                  width=10, command=self.run).pack(side='right')

    def run(self):
        task.samples_to_read = int(self.samples_to_read.get())
        task.rate = int(self.rate.get())
        task.config()
        print('configured')
        if self.acquisition_mode.get() == 'Continuous Samples':
            def close_window():
                global close 
                close = True
                print('closed')
            close = False
            
            app = QtGui.QApplication(sys.argv)
            myapp = GUIForm()
            # myapp.show()

            pW = myapp.chart
            pW.setRange(QtCore.QRectF(0, -10, int(self.samples_to_read.get()), 20))

            # grid.addWidget(pw,0,0)

            if len(task.clist.names)>1:
                curves = []
                for i in range(len(task.clist.names)):
                    pen = pg.mkPen(pg.intColor(i))
                    curves.append(pW.plot(pen=pen))
                while not myapp.close:
                    data = task.acquire()
                    for i in range(len(curves)):
                        curves[i].setData(data[i])
                    app.processEvents()
            else:
                curve = pW.plot()
                while not myapp.close:
                    data = task.acquire()
                    curve.setData(data)
                    app.processEvents()
            task.close()

        else:
            r = task.acquire()
            task.close()
            r = pd.DataFrame(r)
            if len(task.clist.names) > 1:
                r = r.transpose()
                r.columns = task.clist.names
            r.plot()
            plt.show()
            
    def set_menubar(self):
        ''' Menu '''
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label='Save Task', command=self.save_task)
        self.filemenu.add_command(label='Open Task', command=self.open_task)
        self.filemenu.add_command(label='Exit', command=self.destroy)
        self.menubar.add_cascade(label='File', menu=self.filemenu)

    def save_task(self):
        path = filedialog.asksaveasfilename(title='Select file', 
                                            defaultextension='.task',
                                            filetypes=(('task','*.task'),
                                                       ('all files','*.*')))
        file = open(path, 'w')
        variables = list(map(lambda x: str(x.get()), self.variables))
        file.write('\n'.join(variables) + '\n')
        file.write(task.clist.__repr__())
        file.close()

    def open_task(self):
        path=filedialog.askopenfilename(title='Select file', 
                                        filetypes=(('task','*.task'),
                                                   ('all files','*.*')))
        file = open(path, 'r')
        for variable in self.variables:
            variable.set(file.readline().replace('\n',''))
        channels = file.readline().replace("'",'"')
        file.close()
        task.clist.clear()
        task.importChannels(json.loads(channels))
        self.notebook.lb.delete(0, tk.END)
        self.notebook.lb.insert(tk.END, *task.clist.names)
        self.notebook.channel_update = False
        self.max_InputRange.set('')
        self.min_InputRange.set('')
        self.notebook.channel_update = True
        self.notebook.selected_channel=None

class BDFrame(tk.Frame):
    '''Frame with title and border'''
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
        self.parent.update()

    def set_title(self):
        self.parent.update()
        x = self.winfo_x()
        y = self.winfo_y()
        self.label.place(x=x+10, y=y-10)

class MainNotebook(ttk.Notebook):
    """docstring for MainNotebook"""
    def __init__(self, root):
        super(MainNotebook, self).__init__(root)
        self.root = root
        self.selected_channel = None
        self.bind('<<NotebookTabChanged>>', self.tab_change)

        self.tab1 = tk.Frame(self)
        self.tab2 = tk.Frame(self)
        self.tab3 = tk.Frame(self)
        self.tab4 = tk.Frame(self)

        self.add(self.tab1, text='Configuration')
        self.add(self.tab2, text='Triggering')
        self.add(self.tab3, text='Advanced Timing')
        self.add(self.tab4, text='Logging')

        self.pack()

        self.set_config_tab()
        self.set_trigg_tab()
        self.set_timing_tab()
        self.set_loggin_tab()
  
    def tab_change(self, event):
        """Update the root window everytime the tab is changed"""
        root = self.root
        index = event.widget.index('current') # check curretly active tab
        if index == 1: # Configuration Tab
            self.triggerChanged('')
            self.refTriggerChanged('')
            self.stt_tg_widgets[0].pack(fill=tk.BOTH)
            root.update()
            height = self.tb2_StartTrigger.winfo_height()
            width = self.tb2_StartTrigger.winfo_width()
            self.stt_tg_widgets[0].pack_forget()
            self.tb2_StartTrigger.pack_propagate(False)
            self.tb2_StartTrigger['height'] = height
            self.tb2_RefTrigger.pack_propagate(False)
            self.tb2_RefTrigger['height'] = height
            root.update()
            self.tb2_StartTrigger.set_title()
            self.tb2_RefTrigger.set_title()
            if interface.acquisition_mode.get() == 'Continuous Samples':
                self.ref_TgOptions['state'] = tk.DISABLED
                interface.ref_trigger_type.set('<None>')
                self.refTriggerChanged('')
            else:
                self.ref_TgOptions['state'] = tk.NORMAL
        elif index == 2:
            self.tb3_SampleClock.set_title()
            self.tb3_AdditTimeSet.set_title()
        elif index == 3:
            self.tb4_TDMSLogging.set_title()
            self.enable_logging()

    def set_config_tab(self):
        '''Create the Configuration Tab'''
        interface = self.root

        self.tb1_ChanSett = BDFrame(self.tab1, 'Channel Settings')
        self.tb1_ChanSett.pack()
        cs_frame = tk.Frame(self.tb1_ChanSett)
        cs_frame.pack(padx=10, pady=10, fill=tk.BOTH)
        self.tb1_TimeSett = BDFrame(self.tab1, 'Timing Settings')
        self.tb1_TimeSett.pack()
        ts_frame = tk.Frame(self.tb1_TimeSett)
        ts_frame.pack(padx=10, pady=10)

        #Channel Setting Frame
        self.clist = tk.Frame(cs_frame)
        self.clist.pack(side=tk.LEFT)
        tk.Button(self.clist, text='Add',
                  command=self.add_channel).grid(row=0, column=0, sticky='we')
        tk.Button(self.clist, text='Rem', 
                  command=self.remove_channel).grid(row=0, column=1, 
                                                    sticky='we')
        self.lb = tk.Listbox(self.clist)
        self.lb.bind('<<ListboxSelect>>', self.select_channel)
        self.lb.grid(row=1, column=0, columnspan=4)
        csetup = tk.Frame(cs_frame)
        csetup.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        tk.Label(csetup, text='Voltage Input Setup', font=('Helvetica',14), 
                 anchor='w').pack(side=tk.TOP, fill=tk.BOTH)
        voltage_IS = ttk.Notebook(csetup)
        setting_tab = tk.Frame(voltage_IS)
        calibration_tab = tk.Frame(voltage_IS)
        voltage_IS.add(setting_tab, text='Settings')
        voltage_IS.add(calibration_tab, text='Calibration')
        voltage_IS.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        #Signal Input Range Frame
        self.tb1_SigInRange = BDFrame(setting_tab, 'Signal Input Range')
        self.tb1_SigInRange.pack()
        self.sirange_frame = tk.Frame(self.tb1_SigInRange)
        self.sirange_frame.pack(padx=10, pady=10, fill=tk.BOTH)
        tk.Label(self.sirange_frame, text='Max').grid()
        tk.Label(self.sirange_frame, text='Min').grid()
        self.channel_update = True
        self.max_Input = tk.Entry(self.sirange_frame, width=10, 
                             justify='right', 
                             textvariable=interface.max_InputRange,
                             validate="focusout", 
                             validatecommand=self.set_channel)
        self.max_Input.grid(row=0, column=1, pady=5)
        self.min_Input = tk.Entry(self.sirange_frame, width=10,
                             justify='right',
                             textvariable=interface.min_InputRange,
                             validate="focusout", 
                             validatecommand=self.set_channel)
        self.min_Input.grid(row=1, column=1)
        #Scaled Units Frame
        self.sir_ScaledU = BDFrame(self.sirange_frame, 'Scaled Units')
        self.sir_ScaledU.grid(row=0, column=2, rowspan=2, padx=10)
        scaledUnits_frame = tk.Frame(self.sir_ScaledU)
        scaledUnits_frame.pack(padx=10, pady=10, fill=tk.BOTH)
        tk.OptionMenu(scaledUnits_frame, interface.scaled_units, 'volts').pack()

        #Time Setting Frame
        tk.Label(ts_frame, text='Acquisition Mode', 
                 anchor='w').grid(row=0, column=0, padx=5, sticky='we')
        tk.Label(ts_frame, text='Sample to Read', 
                 anchor='w').grid(row=0, column=1, padx=5, sticky='we')
        tk.Label(ts_frame, text='Rate (Hz)', 
                 anchor='w').grid(row=0, column=2, padx=5, sticky='we')
        AqOptions = tk.OptionMenu(ts_frame, interface.acquisition_mode, 
                                  *task.acquisition_mode.options)
        AqOptions.config(width=25)
        AqOptions.grid(row=1, column=0, padx=5)
        tk.Entry(ts_frame, textvariable=interface.samples_to_read, 
                 justify='right').grid(row=1, column=1, padx=5, sticky='we')
        tk.Entry(ts_frame, textvariable=interface.rate, 
                 justify='right').grid(row=1, column=2, padx=5, sticky='we')
        
        # insert frame titles
        self.tb1_ChanSett.set_title()
        self.tb1_TimeSett.set_title()
        self.tb1_SigInRange.set_title()
        self.sir_ScaledU.set_title()

    def set_trigg_tab(self):
        '''Create the Triggering Tab'''
        interface=self.root
        self.tb2_StartTrigger = BDFrame(self.tab2, 'Start Trigger')
        self.tb2_StartTrigger.pack()
        st_frame = tk.Frame(self.tb2_StartTrigger)
        st_frame.pack(padx=10, pady=10, fill=tk.BOTH)
        self.tb2_RefTrigger = BDFrame(self.tab2, 'Reference Trigger')
        self.tb2_RefTrigger.pack()
        rt_frame = tk.Frame(self.tb2_RefTrigger)
        rt_frame.pack(padx=10, pady=10, fill=tk.BOTH)

        # Start Trigger Frame
        stt_tgType_frame = tk.Frame(st_frame)
        stt_tgType_frame.pack(fill=tk.BOTH)
        tk.Label(stt_tgType_frame, text='Trigger Type', 
                 anchor='w').grid(row=0, column=0, padx=5, sticky='we')
        TgOptions = tk.OptionMenu(stt_tgType_frame, interface.stt_trigger_type, 
                                  *task.stt_trigger.type.options, 
                                  command=self.triggerChanged)
        TgOptions.config(width=15)
        TgOptions.grid(row=1, column=0, padx=5, sticky='we')

        self.stt_tg_widgets = [tk.Frame(st_frame) for i in range(3)]
        self.stt_tg_widgets.append(tk.Label(stt_tgType_frame,
                                   text='Trigger Source', anchor='w'))
        self.stt_tg_widgets.append(tk.OptionMenu(stt_tgType_frame, 
                                            interface.stt_trigger_source, 
                                            *task.stt_trigger.source.options))
        self.stt_tg_widgets[-1].config(width=21)

        # Analog Edge
        tk.Label(self.stt_tg_widgets[0], text='Slope', 
                 anchor='w').grid(row=0, column=0, padx=5, sticky='we')
        slope_menu = tk.OptionMenu(self.stt_tg_widgets[0], 
                                   interface.stt_trigger_slope, 
                                   *task.stt_trigger.slope.options
                                   )
        slope_menu.config(width=11)
        slope_menu.grid(row=1, column=0, padx=5, sticky='we')
        tk.Label(self.stt_tg_widgets[0], text='Level', 
                 anchor='w').grid(row=0, column=1, padx=5, sticky='we')
        tk.Entry(self.stt_tg_widgets[0],
                 textvariable=interface.stt_trigger_level, 
                 justify='right', 
                 width=15).grid(row=1, column=1, padx=5, sticky='we')

        # Analog Window
        tk.Label(self.stt_tg_widgets[1], text='Window Top', 
                 anchor='w').grid(row=0, column=0, padx=5, sticky='we')
        tk.Entry(self.stt_tg_widgets[1], textvariable=interface.stt_window_top,
                 justify='right').grid(row=1, column=0, padx=5, sticky='we')
        tk.Label(self.stt_tg_widgets[1], text='Window Bottom', 
                 anchor='w').grid(row=0, column=1, padx=5, sticky='we')
        tk.Entry(self.stt_tg_widgets[1], textvariable=interface.stt_window_bot, 
                 justify='right').grid(row=1, column=1, padx=5, sticky='we')
        tk.Label(self.stt_tg_widgets[1], text='Trigger Condition', 
                 anchor='w').grid(row=0, column=2, padx=5, sticky='we')
        condition_menu = tk.OptionMenu(self.stt_tg_widgets[1], 
                                       interface.stt_trigger_condition,
                                       *task.stt_trigger.condition.options
                                       )
        condition_menu.config(width=25)
        condition_menu.grid(row=1, column=2, padx=5, sticky='we')

        # Digital Edge
        tk.Label(self.stt_tg_widgets[2], text='Slope', 
                 anchor='w').grid(row=0, column=0, padx=5, sticky='we')
        edge_menu = tk.OptionMenu(self.stt_tg_widgets[2], 
                                  interface.stt_trigger_edge, 
                                  *task.stt_trigger.edge.options
                                  )
        edge_menu.config(width=11)
        edge_menu.grid(row=1, column=0, padx=5, sticky='we')

        # ref Trigger Frame
        ref_tgType_frame = tk.Frame(rt_frame)
        ref_tgType_frame.pack(fill=tk.BOTH)
        tk.Label(ref_tgType_frame, text='Trigger Type',
                 anchor='w').grid(row=0, column=0, padx=5, sticky='we')
        self.ref_TgOptions = tk.OptionMenu(ref_tgType_frame, 
                                           interface.ref_trigger_type, 
                                           *task.ref_trigger.type.options, 
                                           command=self.refTriggerChanged
                                           )
        self.ref_TgOptions.config(width=15)
        self.ref_TgOptions.grid(row=1, column=0, padx=5, sticky='we')

        self.ref_tg_widgets = [tk.Frame(rt_frame) for i in range(3)]
        self.ref_tg_widgets.append(tk.Label(ref_tgType_frame, 
                                            text='Trigger Source', 
                                            anchor='w'
                                            )
                                   )
        self.ref_tg_widgets.append(tk.OptionMenu(ref_tgType_frame, 
                                        interface.ref_trigger_source, 
                                        *task.ref_trigger.source.options)
                                   )
        self.ref_tg_widgets[-1].config(width=21)
        self.ref_tg_widgets.append(tk.Label(ref_tgType_frame,
                                            text='Pre-Trigger Samples',
                                            anchor='w'
                                            )
                                   )
        self.ref_tg_widgets.append(tk.Entry(ref_tgType_frame, 
                                    textvariable=interface.preTriggerSamples)
                                   )

        ## Analog Edge
        tk.Label(self.ref_tg_widgets[0], text='Slope', 
                 anchor='w').grid(row=0, column=0, padx=5, sticky='we')
        ref_slope_menu = tk.OptionMenu(self.ref_tg_widgets[0], 
                                       interface.ref_trigger_slope,
                                       *task.ref_trigger.slope.options)
        ref_slope_menu.config(width=11)
        ref_slope_menu.grid(row=1, column=0, padx=5, sticky='we')
        tk.Label(self.ref_tg_widgets[0], text='Level', 
                 anchor='w').grid(row=0, column=1, padx=5, sticky='we')
        tk.Entry(self.ref_tg_widgets[0],
                 textvariable=interface.ref_trigger_level, 
                 justify='right', 
                 width=15).grid(row=1, column=1, padx=5, sticky='we')

        ## Analog Window
        tk.Label(self.ref_tg_widgets[1], text='Window Top', 
                 anchor='w').grid(row=0, column=0, padx=5, sticky='we')
        tk.Entry(self.ref_tg_widgets[1], 
                 textvariable=interface.ref_window_top,
                 justify='right').grid(row=1, column=0, padx=5, sticky='we')
        tk.Label(self.ref_tg_widgets[1], text='Window Bottom', 
                 anchor='w').grid(row=0, column=1, padx=5, sticky='we')
        tk.Entry(self.ref_tg_widgets[1],
                 textvariable=interface.ref_window_bot, 
                 justify='right').grid(row=1, column=1, padx=5, sticky='we')
        tk.Label(self.ref_tg_widgets[1], text='Trigger Condition', 
                 anchor='w').grid(row=0, column=2, padx=5, sticky='we')
        ref_condition_menu = tk.OptionMenu(self.ref_tg_widgets[1], 
                                           interface.ref_trigger_condition,
                                           *task.ref_trigger.condition.options)
        ref_condition_menu.config(width=25)
        ref_condition_menu.grid(row=1, column=2, padx=5, sticky='we')

        ## Digital Edge
        tk.Label(self.ref_tg_widgets[2], text='Slope',
                 anchor='w').grid(row=0, column=0, padx=5, sticky='we')
        ref_edge_menu = tk.OptionMenu(self.ref_tg_widgets[2], 
                                      interface.ref_trigger_edge,
                                      *task.ref_trigger.edge.options)
        ref_edge_menu.config(width=11)
        ref_edge_menu.grid(row=1, column=0, padx=5, sticky='we')

    def set_timing_tab(self):
        '''Create the Advanced Timing Tab'''
        interface = self.root
        self.tb3_SampleClock = BDFrame(self.tab3, 'Sample Clock Settings')
        self.tb3_SampleClock.pack()
        scs_frame = tk.Frame(self.tb3_SampleClock)
        scs_frame.pack(padx=10, pady=10, fill=tk.BOTH)
        self.tb3_AdditTimeSet = BDFrame(self.tab3, 'Additional Time Settings')
        self.tb3_AdditTimeSet.pack()
        ats_frame = tk.Frame(self.tb3_AdditTimeSet)
        ats_frame.pack(padx=10, pady=10, fill=tk.BOTH)
        tk.Label(scs_frame, text='Sample Clock Type', 
                 anchor='w').grid(row=0, column=0, padx=5, sticky='we')
        clockType_menu = tk.OptionMenu(scs_frame, interface.clock_type, 
                                       *task.clock_type.options)
        clockType_menu.config(width=11)
        clockType_menu.grid(row=1, column=0, padx=5, sticky='we')
        tk.Label(scs_frame, text='Clock Source', 
                 anchor='w').grid(row=2, column=0, padx=5, sticky='we')
        clockSource_menu = tk.OptionMenu(scs_frame, interface.clock_source,
                                         *task.clock_source.options)
        clockSource_menu.config(width=19, state=tk.DISABLED)
        clockSource_menu.grid(row=3, column=0, columnspan=2, 
                              padx=5, sticky='we')
        tk.Label(scs_frame, text='Active Edge',
                 anchor='w').grid(row=2, column=2, padx=5, sticky='we')
        clockType_menu = tk.OptionMenu(scs_frame, interface.active_edge,
                                       *task.active_edge.options)
        clockType_menu.config(width=11, state=tk.DISABLED)
        clockType_menu.grid(row=3, column=2, padx=5, sticky='we')
        tk.Label(ats_frame, text='Timeout (s)',
                 anchor='w').grid(padx=5, sticky='w')
        ttk.Spinbox(ats_frame, from_=-1, to=10000, 
                    textvariable=interface.timeout, 
                    width=10, justify='right').grid(padx=5, sticky='w')

    def set_loggin_tab(self):
        '''Create the Logging Tab'''
        interface=self.root
        self.tb4_TDMSLogging = BDFrame(self.tab4, 'TDMS File Logging')
        self.tb4_TDMSLogging.pack()
        tdms_frame = tk.Frame(self.tb4_TDMSLogging)
        tdms_frame.pack(padx=10, pady=10, fill=tk.BOTH)
        tk.Checkbutton(tdms_frame, text='Enable TDMS Logging', 
                       var=interface.TDMSLogging, command=self.enable_logging, 
                       anchor='w').pack(padx=5, fill=tk.BOTH)
        self.file_frame = tk.Frame(tdms_frame, 
                              highlightbackground='light steel blue', 
                              highlightcolor='light steel blue', 
                              highlightthickness=1
                              )
        self.file_frame.pack(padx=5, pady=5, ipady=5, fill=tk.BOTH)
        tk.Label(self.file_frame, text='File Path', 
                 anchor='w').grid(padx=5, sticky='we')
        tk.Entry(self.file_frame,
                 textvariable=interface.TDMS_filepath).grid(padx=5, 
                                                            sticky='we')
        tk.Button(self.file_frame, text='Search', 
                  command=self.search_file).grid(row=1, column=1)
        tk.Checkbutton(self.file_frame, text='Append data if file exists', 
                       variable=interface.append_data).grid(padx=5, sticky='w')
        tk.Label(self.file_frame, text='Logging Mode', 
                 anchor='w').grid(padx=5, sticky='we')
        logginMode_menu = tk.OptionMenu(self.file_frame, 
                                        interface.logging_mode, 
                                        *task.logging_mode.options)
        logginMode_menu.config(width=11)
        logginMode_menu.grid(padx=5, sticky='we')


        tk.Label(self.file_frame, text='Group Name', 
                 anchor='w').grid(padx=5, sticky='we')
        tk.Entry(self.file_frame,
                 textvariable=interface.group_name).grid(padx=5, sticky='we')
        tk.Checkbutton(self.file_frame, text='Span multiple files',
                       variable=interface.span,
                       command=self.span_files_function).grid(padx=5, 
                                                              sticky='w')
        smf_frame = tk.Frame(self.file_frame)
        smf_frame.grid(padx=30)
        self.spanLabel = tk.Label(smf_frame, text='Samples Per File',
                                  anchor='w')
        self.spanLabel.grid(sticky='we')
        self.spanEntry = tk.Entry(smf_frame, 
                                  textvariable=interface.sample_per_file)
        self.spanEntry.grid(sticky='we')

    def add_channel(self):
        def add_chan_function():
            channel_name = '{}/{}'.format(device_name.get(), dev_channel.get())
            self.selected_channel = channel_name
            if task.clist.find(channel_name) == None:
                channel = task.add_channel(cname=channel_name)
                self.lb.delete(0, tk.END)
                self.lb.insert(tk.END, *task.clist.names)
                self.channel_update = False
                self.root.max_InputRange.set(channel.maxInputRange)
                self.root.min_InputRange.set(channel.minInputRange)
                self.channel_update = True
        add_window = tk.Toplevel(self.root)
        tk.Label(add_window, text='Device Name:').pack()
        device_name = tk.StringVar(self.root, value='Dev3')
        tk.Entry(add_window, justify=tk.CENTER, 
                 textvariable=device_name).pack()
        tk.Label(add_window, text='Channel:').pack()
        dev_channel = tk.StringVar(self.root, value='ai0')
        channels_numbers = ['ai{}'.format(str(i)) for i in range(10)]
        tk.OptionMenu(add_window, dev_channel, *channels_numbers).pack()
        tk.Button(add_window, text='add channel', command=add_chan_function).pack()

    def remove_channel(self):
        index = self.lb.curselection()[0]
        task.clist.pop(index)
        self.lb.delete(0, tk.END)
        self.lb.insert(tk.END, *task.clist.names)
        self.selected_channel = None

    def select_channel(self, event):
        self.set_channel()
        interface = self.root
        if len(self.lb.curselection()) > 0:
            index = self.lb.curselection()[0]
            self.selected_channel = task.clist.names[index]
            channel = task.clist.find(self.selected_channel)
            self.channel_update = False
            interface.max_InputRange.set(channel.maxInputRange)
            interface.min_InputRange.set(channel.minInputRange)
            self.channel_update = True
            interface.update()

    def set_channel(self):
        interface = self.root
        if self.selected_channel is not None and self.channel_update:
            channel = task.clist.find(self.selected_channel)
            channel.maxInputRange = int(interface.max_InputRange.get())
            channel.minInputRange = int(interface.min_InputRange.get())
        return True

    def triggerChanged(self, event):
        new_choices = ['APFI0', 'APFI1'] + task.clist.names
        source = interface.stt_trigger_source.get()
        for widget in self.stt_tg_widgets:
            widget.pack_forget()
            widget.grid_remove()
        trigger_type = interface.stt_trigger_type.get()
        if trigger_type != '<None>':
            self.stt_tg_widgets[3].grid(row=0, column=1, padx=5, sticky='we')
            interface.stt_trigger_source.set('APFI0')
            self.stt_tg_widgets[4].grid(row=1, column=1, padx=5, sticky='we')
        if trigger_type == 'Analog Edge':
            self.stt_tg_widgets[0].pack(fill=tk.BOTH)
        elif trigger_type == 'Analog Window':
            self.stt_tg_widgets[1].pack(fill=tk.BOTH)
        elif trigger_type == 'Digital Edge':
            interface.stt_trigger_source.set('PFI0')
            self.stt_tg_widgets[2].pack(fill=tk.BOTH)
            new_choices = ['PFI{}'.format(i) for i in range(16)]
        self.stt_tg_widgets[4]['menu'].delete(0, 'end')
        for choice in new_choices:
            self.stt_tg_widgets[4]['menu'].add_command(label=choice, 
                    command=tk._setit(interface.stt_trigger_source, choice))
        if source in new_choices:
            interface.stt_trigger_source.set(source)
    
    def refTriggerChanged(self, event):
        new_choices = ['APFI0', 'APFI1'] + task.clist.names
        source = interface.ref_trigger_source.get()
        for widget in self.ref_tg_widgets:
            widget.pack_forget()
            widget.grid_remove()
        trigger_type = interface.ref_trigger_type.get()
        if trigger_type != '<None>':
            self.ref_tg_widgets[3].grid(row=0, column=1, padx=5, sticky='we')
            interface.ref_trigger_source.set('APFI0')
            self.ref_tg_widgets[4].grid(row=1, column=1, padx=5, sticky='we')
            self.ref_tg_widgets[5].grid(row=0, column=2, padx=5, sticky='we')
            self.ref_tg_widgets[6].grid(row=1, column=2, padx=5, sticky='we')
        if trigger_type == 'Analog Edge':
            self.ref_tg_widgets[0].pack(fill=tk.BOTH)
        elif trigger_type == 'Analog Window':
            self.ref_tg_widgets[1].pack(fill=tk.BOTH)
        elif trigger_type == 'Digital Edge':
            interface.ref_trigger_source.set('PFI0')
            self.ref_tg_widgets[2].pack(fill=tk.BOTH)
            new_choices = ['PFI{}'.format(i) for i in range(16)]
        self.ref_tg_widgets[4]['menu'].delete(0, 'end')
        for choice in new_choices:
            self.ref_tg_widgets[4]['menu'].add_command(label=choice, 
                    command=tk._setit(interface.ref_trigger_source, choice))
        if source in new_choices:
            interface.ref_trigger_source.set(source)

    def enable_logging(self):
        if self.root.TDMSLogging.get() == 1:
            for widget in self.file_frame.winfo_children():
                try:
                    widget.config(state=tk.NORMAL)
                except:
                    pass
                self.span_files_function()
        else:
            for widget in self.file_frame.winfo_children():
                try:
                    widget.config(state=tk.DISABLED)
                except:
                    pass
                self.spanEntry['state'] = tk.DISABLED
                self.spanLabel['state'] = tk.DISABLED

    def span_files_function(self):
        if not self.root.span.get():
            self.spanEntry['state'] = tk.DISABLED
            self.spanLabel['state'] = tk.DISABLED
        else:
            self.spanEntry['state'] = tk.NORMAL
            self.spanLabel['state'] = tk.NORMAL

    def search_file(self):
        self.root.TDMS_filepath.set(filedialog.asksaveasfilename(
              title = 'Select file', filetypes = (('TDMS files','*.tdms'),
                                                  ('TDM files','*.tdm'),
                                                  ('all files','*.*')
                                                  )))

if __name__ == '__main__':
    interface = Interface()
    interface.mainloop()
exit()



    

