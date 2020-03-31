import nidaqmx
import tkinter as tk
from tkinter import messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class Interface(tk.Tk):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Interface, cls).__new__(cls)
        else:
            cls._instance.destroy()
        return cls._instance

    def __init__(self):
        super(Interface, self).__init__()
        self.winfo_toplevel().title("NiDAQmx Controller")
        f1 = tk.Frame(self)
        f1.pack()
        tk.Label(f1, text='Device Name:').pack()
        self.device_name = tk.StringVar(self, value='Dev3')
        tk.Entry(f1, justify=tk.CENTER, textvariable=self.device_name).pack()

        tk.Label(f1, text='Channel:').pack()
        self.channel_y = tk.StringVar(f1)
        channel_list = ['ai{}'.format(str(i)) for i in range(10)]
        self.channel_y.set('ai0')
        tk.OptionMenu(f1, self.channel_y, *channel_list).pack()
        tk.Button(f1, text='add channel', command=self.add_channel).pack()
        tk.Label(f1).pack()
        self.channelsInTask = []
        self.lb = tk.Listbox(f1, selectmode=tk.EXTENDED)
        self.lb.pack()
        tk.Button(f1, text='remove channel', command=self.remove_channel).pack()
        tk.Label(f1).pack()

        tk.Label(f1, text='Number of samples to read:').pack()
        self.samples_number = tk.StringVar(self, value='1')
        vcmd = (self.register(self.validate), '%P')
        self.entry = tk.Entry(f1, justify=tk.CENTER, textvariable=self.samples_number, validate='key', validatecommand=vcmd)
        self.entry.pack()
        tk.Button(f1, text='read channels', command=self.read_channels).pack()

        tk.Button(f1, text='show data', command=self.show).pack()

    def validate(self, P):
        if P == '':
            return True
        try:
            P = int(P)
        except:
            return False
        n = len(self.channelsInTask)
        if n == 0:
            return True
        if P*n<700000:
            return True
        else:
            # messagebox.showerror('Error', 'The total aquisition data must be smaller than 700k')
            self.samples_number.set(str(int(700000/n)))
            self.entry['validate']='key'
        return False

    def add_channel(self):
        channel = '{}/{}'.format(self.device_name.get(),self.channel_y.get())
        if channel not in self.channelsInTask:
            self.channelsInTask.append(channel)
            self.channelsInTask.sort()
            self.lb.delete(0, tk.END)
            self.lb.insert(tk.END, *self.channelsInTask)
        self.validate(P=self.entry.get())

    def remove_channel(self):
        indexes = self.lb.curselection()
        for i in indexes:
            self.channelsInTask.remove(self.lb.get(i))
        self.lb.delete(0, tk.END)
        self.lb.insert(tk.END, *self.channelsInTask)

    def read_channels(self):
        self.task = nidaqmx.Task()
        while True:
            try:
                for channel in self.channelsInTask:
                    self.task.ai_channels.add_ai_voltage_chan(channel)
                n = int(self.samples_number.get())
                r = self.task.read(number_of_samples_per_channel=n)
                self.data = pd.DataFrame(r)
                if len(self.channelsInTask) > 1:
                    self.data = self.data.transpose()
                self.data.columns = self.task.channel_names
                print(self.data)
                self.task.close()
                return
            except:
                if not messagebox.askretrycancel('Error',  'Channel {} not found. Try again?'.format(channel)):
                    self.task.close()
                    return

    def show(self):
        def plot():
            plt.figure()
            for column in self.data.columns:
                plt.plot(self.data[self.x_axes.get()], self.data[column])
            plt.show()
        try:
            self.data.plot()
        except:
            return
        window = tk.Toplevel(self)
        tk.Label(window, text='select x axes:').pack()
        self.x_axes = tk.StringVar(window)
        tk.OptionMenu(window, self.x_axes, *self.data.columns).pack()
        tk.Button(window, text='plot', command=plot).pack()


        plt.show()

    def save(self):
        df = self.data


if __name__ == '__main__':
    interface = Interface()
    interface.mainloop()