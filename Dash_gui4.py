# -*- coding: utf-8 -*-
"""
Created on Sat Nov  4 09:58:33 2017

@author: Christian Orner
"""

import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")

from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import numpy as np
np.set_printoptions(threshold=np.nan)
from scipy.optimize import fsolve

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

style.use('ggplot')
LARGE_FONT= ("Verdana", 12)

 # timestep for the SOC calculation
t_step=1
t=np.arange(0,24,t_step)
t_len=np.size(t)

N_cells=50

#days are gui input
def time(days):
    global Input_days
    global t_ges
    global t_len
    global d_len
    
    #days=days.get()
    days=int(days)
    Input_days=np.arange(0,days,1)            
    d_len=np.size(Input_days)
    t_ges=np.arange(0,t_len*d_len,1)

class Solar():
    
    def __init__(self):
        
 #       U_oc=0.7 #get Uoc from gui input
#       self.Uoc= float(U_oc)
#        I_sc=1
        # Does not change the graph much
#       self.Isc= float(I_sc)
        self.Uoc=0.7
        self.Isc=1
        self.ktemp= 0.3
        #self.R= np.arange(0.1,3,0.1) takes to long to compute
        self.R= np.array([0.1,0.2,0.5, 0.6, 0.7, 0.8, 0.9, 1, 2, 3])
    #zeros(row,columns)
        #self.I=np.zeros([np.size(self.get_Rad()),np.size(self.R)])
        self.I=np.zeros(np.size(self.R))
        self.U=np.zeros(np.size(self.R))
        self.I_plot=np.zeros(np.size(self.R))
        self.U_plot=np.zeros(np.size(self.R))
        
        
        self.P=np.zeros(np.size(self.R))
        #self.U=np.zeros([np.size(self.get_Rad()),np.size(self.R)])
        #self.P=np.zeros([np.size(self.get_Rad()),np.size(self.R)])
        self.Pmpp=np.zeros(np.size(t))
#E= 600
#T= 350

    def solargen(self,I,R,Uoc,Isc,ktemp,E,T):
        #R=4        
        k= 1.38*10**(-23)
        q=1.602*10**(-19)
        UT= k*T/q
        const= 0.001 
        #print(UT)
        
        
        Iph= E*const
        Uoc_T= self.Uoc+(-self.ktemp*0.01*(T-298))
        #print(Uoc_T)
        I0=self.Isc/(np.exp(Uoc_T/UT)-1)        
        y=Iph-I0*(np.exp((I*R)/UT)-1)-I
        #print(np.exp(Uoc_T/UT)-1)
        return y
    
#    def get_Temp(self):
#        y=Temp.get()
#        return y

    def get_Rad(self,rad_ampl,rad_width):
 #       a=Rad_width.get()
        a=rad_width
        y= rad_ampl
 #       y=10
        Rad= np.zeros(np.size(t))
        for i in range(np.size(t)):        
            Rad[i]= (-a)*(t[i]-14)**2+y
            if Rad[i] < 0:
                Rad[i]=0
        return Rad
    
    def get_U_I(self):
        x= self.U_plot
        y= self.I_plot
        return x,y
    
    def get_P_Pmpp(self):
        x =self.P
        y =self.Pmpp
        return x,y

    
    def calc_Pmpp(self,N_cells,T,rad_ampl,rad_width):
        #T= self.get_Temp()
        E= self.get_Rad(rad_ampl,rad_width)
        #E=1000
        for e in range(E.shape[0]):
            #print(E.shape[0])
            k=0
            l=0
            for i in self.R:
                x= fsolve(self.solargen, 0.8, args=(i,self.Uoc,self.Isc,self.ktemp,E[e],T))
                #I[row,column]
                #print(x)
                self.I[k]=x
                self.U[k]=x*i
                
                # save I and U for the peak radiation to plot UI curve
                if e == 14:
                    self.I_plot[l]=x
                    self.U_plot[l]=x*i
                    l+=1
                    
                k+=1
        
            self.P=self.U*self.I*N_cells
            self.Pmpp[e]=np.max(self.P)
        #return Pmpp, P
    
class Battery():
    def __init__(self):
        # maximum storage capacity in Wh
        # input from gui
#        C=Input_capacity.get()
        self.Wmax=100
        print(self.Wmax)
        #self.stored_energy=np.zeros(np.size(t_ges))
        self.stored_energy=np.full(np.size(t_ges),200)
        self.SOC=np.zeros(np.size(t_ges))
        
        # unused energy
        self.W_unused=np.zeros(np.size(t_ges))
        
        
    def get_SOC(self):
        x=self.SOC
        return x
    
#    def set_Wmax(self,capacity):
#        
#        battery_capacity=int(capacity)
        
        
    
    def get_W_unused(self):
        x= self.W_unused
        return x
    
    def get_stored_energy(self):
        x=self.stored_energy
        return x
        
        
    def calc_SOC(self,t,T,rad_ampl,rad_width):
        
        #k=0
        # time counting after SOC=1
        #t_lost=1
        #Pmpp=calc_Pmpp(Uoc, Isc, ktemp, E)
        Cons=Consumer()
        Cons.calc_power(T,rad_ampl,rad_width)
        P_store=Cons.get_power_to_bat()
       # P, Pmpp=Solar.get_P_Pmpp()
        #consumer=0.8*Pmpp
        
        for d in Input_days:  
            for i in t:
                if (self.stored_energy[i-1+t_len*d]+P_store[i]>=0) and (self.stored_energy[i-1+t_len*d]+P_store[i]<=self.Wmax): #charge
                #Pmpp from solargen
                    self.stored_energy[i+t_len*d] = self.stored_energy[i-1+t_len*d] + P_store[i]
                    self.W_unused[i+t_len*d]=self.W_unused[i-1+t_len*d]
                    
                    
                
                
                elif self.stored_energy[i-1+t_len*d]+P_store[i]<0:
                    self.stored_energy[i+t_len*d] = 0
                    self.W_unused[i+t_len*d]=self.W_unused[i-1+t_len*d]
                    #print(i)
                    
                    
                    
                elif self.stored_energy[i-1+t_len*d]+P_store[i]>self.Wmax:
                    #print(self.Wmax-self.stored_energy[i-1])
                    self.W_unused[i+t_len*d] = self.W_unused[i-1+t_len*d] + self.stored_energy[i-1+t_len*d]+P_store[i]-self.Wmax
                    self.stored_energy[i+t_len*d] = self.Wmax
                    
                self.SOC[i+t_len*d]=self.stored_energy[i+t_len*d]/self.Wmax
                
                

class Consumer():
    
    def __init__(self):
        self.power = np.zeros(np.size(t))
        self.P_diff=np.zeros(np.size(t))
        
        
    def get_power(self):
        x= self.power
        return x
    
    def get_power_to_bat(self):
        x=self.P_diff
        return x
    
    def calc_power(self,T,rad_ampl,rad_width):
        self.power = ([20,20,0,0,5,15,15,0,0,0,20,20,0,0,0,10,15,15,40,40,10,5,0,0])
        Sol=Solar()
        Sol.calc_Pmpp(N_cells,T,rad_ampl,rad_width)
        P, Pmpp=Sol.get_P_Pmpp()
        
        for i in range(np.size(self.power)):
            self.P_diff[i] = Pmpp[i]-self.power[i]
            
class Costs():
    def __init__(self):
        self.cost_per_kwh=0.3
        self.total_costs=np.zeros(d_len)
        self.total_costs_sol=np.zeros(d_len)
        self.solar_invest=200
        self.battery_invest=200
        
         
    def calc_costs(self,T,rad_ampl,rad_width):
        #100% grid supplly
        Cons=Consumer()
        Cons.calc_power(T,rad_ampl,rad_width)
        P_cons=Cons.get_power() #power req by consumer
        P_diff_cons_sol=Cons.get_power_to_bat() #difference between consumer and solar power
        
        costs_per_day=self.cost_per_kwh*sum(P_cons)
        for i in range(d_len):
            self.total_costs[i]=costs_per_day*(i+1)
        print (self.total_costs)
        print (costs_per_day)
        
        #costs with solar
        pow_from_grid=np.zeros(24) #power during day from grid if solar panel dont produce enough
        
        for i in range(np.size(P_diff_cons_sol)):
            if P_diff_cons_sol[i] <0:
                pow_from_grid[i]=abs(P_diff_cons_sol[i])
               
                
        costs_day_with_solar= self.cost_per_kwh*sum(pow_from_grid)
        for i in range(d_len):
            self.total_costs_sol[i]=costs_day_with_solar*(i+1)+self.solar_invest
        print(self.total_costs_sol)
            
            
            
        
    
#f = Figure(figsize=(8,4.5), dpi=100)
#a = f.add_subplot(224)
#b = f.add_subplot(222)
#c= f.add_subplot(221)
#d= f.add_subplot(223)
#f.tight_layout()
#
#f2 = Figure(figsize=(8,4.5), dpi=100)
#b2 = f2.add_subplot(111)
#
#
#def plot_Solargen(canvas):
#    Sol= Solar()
#    Sol.calc_Pmpp(N_cells)
#    U,I = Sol.get_U_I()
#    P,Pmpp= Sol.get_P_Pmpp()
#    
#    b2.clear()
#    b2.plot(U,I,'b')
#    canvas.draw()
#    
#
#
#
#def plot_battery(canvas):
#   # Battery.calc_SOC(t)
#    #SOC = Battery.get_SOC()
#    time(days)
#    Sol=Solar()
#    Sol.calc_Pmpp(N_cells) #Number of cells in brackets
#    Cons= Consumer()
#    Cons.calc_power()
#    Bat= Battery()
#    Bat.calc_SOC(t)
#    
#    #P,Pmpp= Sol.get_P_Pmpp()
#    U,I= Sol.get_U_I()
#    E= Sol.get_Rad()
#
#
#    P_store= Cons.get_power_to_bat()
#    SOC= Bat.get_SOC()
#    Unused= Bat.get_W_unused()
#    E_Batt= Bat.get_stored_energy()
    
    
    #print(Bat.get_W_unused())
    #print(Bat.get_SOC()[9])
    
    
    #a.clear()
    #b.clear()
#    c.clear()
#    d.clear()
#    #a.plot(t, W_unused)
#    #a.plot(U,I)
#    #b.plot(t,E, 'r', label= 'Radiation')
#    c.plot(t_ges, E_Batt, '#183A54', label='Stored Energy')
#    d.plot(t_ges, SOC, "#00A3E0", label='SOC')
#    
#    b.legend(loc=1,bbox_to_anchor=(1, 1.12))
#    c.legend(loc=1,bbox_to_anchor=(1, 1.12))
#    d.legend(loc=1,bbox_to_anchor=(1, 1.12))
#    
#    canvas.draw()
    
    
    
    
app = dash.Dash()

app.layout = html.Div([
        html.Div([html.H1(
                    'Solar Energy Calculator'),]),
        html.Div([
            dcc.Graph(id='graph-with-slider'),
            ],style={'width': '48%','display': 'inline-block'}),
        html.Div([
                    dcc.Graph(id='Main_graph'),
                    html.Label('Number of Days',id='days_label'),
                    dcc.Input(id='days', value='2', type='text'),
                    html.Label('Battery Capacity',id='cap_label'),
                    dcc.Input(id='capacity', value='100', type='text'),
                    ],style={'width': '48%','display': 'inline-block'}),
        html.Div([
            html.P('Ambient Temperature [K]'),
            dcc.Slider(
                id='Ambient_Temp',
                min=273,
                max=353,
                value=293,
                step=None,
                marks={i: str(i) for i in range(273,353,10)}
            ),
            html.P('Radiation Amplitude [W/m2]'),
            dcc.Slider(
                id='rad_ampl',
                min=0,
                max=1000,
                value=500,
                step=None,
                marks={str(i): str(i) for i in range(0,1000,100)}
                    ),
            html.P('Scaling factor [-]'),
            dcc.Slider(
                id='rad_width',
                min=20,
                max=80,
                value=50,
                #step=None,
                marks={str(i): str(i) for i in range(20,80,10)}
                    ),
        ],style={'width': '48%', 'display': 'inline-block'}),

#'display': 'inline-block' 
#style={'width': '48%', 'float': 'right'} 

        
    ],style={'width': '100%', 'display': 'inline-block'})



@app.callback(
    dash.dependencies.Output('graph-with-slider', 'figure'),
    [dash.dependencies.Input('Ambient_Temp', 'value'),
     dash.dependencies.Input('rad_ampl', 'value'),
     dash.dependencies.Input('rad_width', 'value')])
def update_figure(Temp,rad_ampl,rad_width):
    #filtered_df = df[df.year == selected_year]
    Tes=Costs()
    Tes.calc_costs(Temp,rad_ampl,rad_width)
    
    Sol= Solar()
    Sol.calc_Pmpp(N_cells,Temp,rad_ampl,rad_width)
    U,I = Sol.get_U_I()
    E=Sol.get_Rad(rad_ampl,rad_width)
    Cons=Consumer()
    Cons.calc_power(Temp,rad_ampl,rad_width)
    P_cons=Cons.get_power()
    print(Temp)
    P,Pmpp= Sol.get_P_Pmpp()
    
    traces = []
    trace1=(go.Scatter(
        x=t,
        y=E,
        name = 'Radiation',
        yaxis='y1',
        marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
                },
    ))
    trace2=(go.Scatter(
        x=t,
        y=P_cons,
        name='Consumption',
        yaxis='y2',
        marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'blue'}
                },
    ))
    
    traces=[trace1,trace2]

    return {
        'data': traces,
        'layout': go.Layout(
                title='Daily Radiation and Consumption',
                xaxis={'title': 'Time'},
                yaxis1={'title': 'Radiation [W/m2]'},
                yaxis2={'title':'Consumption [W]','overlaying':'y','side':'right'},
                legend=dict(x=-.1, y=1.2)
        )
    }
    
    
@app.callback(
    dash.dependencies.Output('Main_graph', 'figure'),
    [dash.dependencies.Input('days','value'),
     dash.dependencies.Input('capacity','value'),
     dash.dependencies.Input('Ambient_Temp', 'value'),
     dash.dependencies.Input('rad_ampl', 'value'),
     dash.dependencies.Input('rad_width', 'value')])
def update_Main(days_input,bat_cap,Temp,rad_ampl,rad_width):
    #filtered_df = df[df.year == selected_year]
    time(days_input)
    Bat= Battery()
    Bat.calc_SOC(t,Temp,rad_ampl,rad_width)
    #Bat.Wmax = Bat.set_Wmax(bat_cap)
    #print(Bat.Wmax)
    E_Batt= Bat.get_stored_energy()
    
    traces = []
    traces.append(go.Scatter(
        x=t_ges,
        y=E_Batt,
        marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
                },
    ))

    return {
        'data': traces,
        'layout': go.Layout(
            xaxis={'title': 'Time'},
            yaxis={'title': 'Stored Energy'}
        )
    }
    

    
    


if __name__ == '__main__':
    app.run_server()

    

#class SeaofBTCapp(tk.Tk):
#
#    def __init__(self, *args, **kwargs):
#        
#        tk.Tk.__init__(self, *args, **kwargs)
#        container = tk.Frame(self)
#
#        container.pack(side="top", fill="both", expand = True)
#
#        container.grid_rowconfigure(0, weight=1)
#        container.grid_columnconfigure(0, weight=1)
#        
#        
#
#        self.frames = {}
#
#        for F in (StartPage, PageOne, PageTwo, PageThree):
#            frame = F(container, self)
#            self.frames[F] = frame
#            frame.grid(row=0, column=0, sticky="nsew")
#            
#        self.show_frame(StartPage)
#
#    def show_frame(self, cont):
#
#        frame = self.frames[cont]
#        frame.tkraise()
#
#        
#class StartPage(tk.Frame):
#
#    def __init__(self, parent, controller):
#        tk.Frame.__init__(self,parent)
#        label = tk.Label(self, text="Start Page", font=LARGE_FONT)
#        label.grid(row=1, column= 10)
#        
#        button = ttk.Button(self, text= 'Visit Page 1', command=lambda: controller.show_frame(PageOne))
#        button.grid(row=5, column=5, sticky='WNSE')
#       
#        button2 = ttk.Button(self, text= 'Configure Solar Cells', command=lambda: controller.show_frame(PageTwo))
#        button2.grid(row=6, column=5, sticky='WNSE')
#       
#        button3 = ttk.Button(self, text= 'Visit Graph Page', command=lambda: controller.show_frame(PageThree))
#        button3.grid(row=7,column=5, sticky='NSEW')
#        
#class PageOne(tk.Frame):
##
#   def __init__(self, parent, controller):
#        tk.Frame.__init__(self,parent)
#        label = tk.Label(self, text="Page 1", font=LARGE_FONT)
#        label.grid(row=1,column=2, columnspan=3)
##        
#        button = ttk.Button(self, text= 'Visit Start Page', command=lambda: controller.show_frame(StartPage))
#        button.grid(row=2,column=5)
##        
#        button2 = ttk.Button(self, text= 'Configure Solar Cells', command=lambda: controller.show_frame(PageTwo))
#        button2.grid(row=3, column=5)
#        
#class PageTwo(tk.Frame):
#
#    def __init__(self, parent, controller):
#        global Isc
#        global Uoc
#        global ktemp
#        
#        tk.Frame.__init__(self,parent)
#        toolbar_frame= tk.Frame(self)
#        label = tk.Label(self, text="Configure Solar Cells", font=LARGE_FONT)
#        label.grid(row=1,column=2, columnspan=3)
#        
#        button = ttk.Button(self, text= 'Go to Graph Page', command=lambda: controller.show_frame(PageThree))
#        button.grid(row=2,column=1, sticky= 'WNSE')
#        
#        button2 = ttk.Button(self, text= 'Go to Start Page', width=20, command=lambda: controller.show_frame(StartPage))
#        button2.grid(row=3,column=1, sticky='NSEW')
#        
#        Isc= tk.StringVar(self, value='1')
#        input1=tk.Entry(self, textvariable=Isc)
#        input1.grid(row=5,column=1)
#        label1 = tk.Label(self, text="Isc")
#        label1.grid(row=5, sticky= 'W')
#        self.grid_rowconfigure(4,minsize=50)
#        
#        Uoc= tk.StringVar(self, value='0.8')
#        input2=tk.Entry(self, textvariable=Uoc)
#        input2.grid(row=6,column=1)
#        label2 = tk.Label(self, text="Uoc")
#        label2.grid(row=6, sticky= 'W')
#        
#        
#        
#        ktemp= tk.StringVar(self, value='0.3')
#        input3=tk.Entry(self, textvariable=ktemp)
#        input3.grid(row=7,column=1)
#        label3 = tk.Label(self, text="ktemp")
#        label3.grid(row=7, sticky= 'W')
#        
#        canvas= FigureCanvasTkAgg(f2, self)
#        canvas.show()
#        canvas.get_tk_widget().grid(row=6,column= 3)
#        # toolbar needs to bee in seperate frame to use grid method       
#        toolbar_frame.grid(row=7, column=3)
#        toolbar_frame.tkraise()
#        toolbar = NavigationToolbar2TkAgg(canvas, toolbar_frame)
#        toolbar.update()
#        
#        plotbutton=tk.Button(master=self, text="update", command=lambda: plot_Solargen(canvas), height = 3, width = 15)
#        plotbutton.grid(row=9,column=0)
#        
#        
#        
#        
#class PageThree(tk.Frame):
#
#    def __init__(self, parent, controller):
#        tk.Frame.__init__(self,parent)
#        toolbar_frame= tk.Frame(self)
#        label = tk.Label(self, text="Graph Page", font=LARGE_FONT)
#        label.grid(row=1,column=2, columnspan=3)
#        global Temp
#        global Rad_ampl
#        global Rad_width
#        global Input_capacity
#        global days
#        
#        
#        
#        button1 = ttk.Button(self, text= 'Back to Home', command=lambda: controller.show_frame(StartPage))
#        button1.grid(row=1)
#        
#        
#        # Temperature of solar panel
#        Temp= tk.Scale(self, from_= 273, to= 350)
#        Temp.grid(row=3, sticky = 'N')
#        label = tk.Label(self, text="Ambient Temperature")
#        label.grid(row=2)
#        
#        # changes amplitude of solar radiation     
#        Rad_ampl= tk.Scale(self, from_= 0, to= 1000)
#        Rad_ampl.grid(row=3, column=1, sticky = 'N')
#        label = tk.Label(self, text="Solar radiation")
#        label.grid(row=2,column=1)
#        
#        # changes width of solar radiation profile        
#        Rad_width= tk.Scale(self, from_= 16, to= 80)
#        Rad_width.grid(row=3, column=2, sticky = 'N')
#        label = tk.Label(self, text="Duration")
#        label.grid(row=2, column=2)
#        
#        # input capacity is taken in battery class
#        Input_capacity= tk.StringVar(self, value='200')
#        input1=tk.Entry(self, textvariable=Input_capacity)
#        input1.grid(row=4,column=1)
#        label1 = tk.Label(self, text="Battery Capacity [Wh]")
#        label1.grid(row=4)
#        
#        # global varialble days is input for time function
#        #changes viewed time range
#        days= tk.StringVar(self, value='2')
#        input2=tk.Entry(self, textvariable=days)
#        input2.grid(row=5,column=1)
#        label2 = tk.Label(self, text="Days to view")
#        label2.grid(row=5)
#        
#        
#        canvas= FigureCanvasTkAgg(f, self)
#        canvas.show()
#        canvas.get_tk_widget().grid(row=6,column= 3)
#        # toolbar needs to bee in seperate frame to use grid method       
#        toolbar_frame.grid(row=7, column=3)
#        toolbar_frame.tkraise()
#        toolbar = NavigationToolbar2TkAgg(canvas, toolbar_frame)
#        toolbar.update()
#        
#        
#        plotbutton=tk.Button(master=self, text="plot", command=lambda: plot_battery(canvas), height = 3, width = 15)
#        plotbutton.grid(row=6,column=0)
#        
#        
#            
#
#
#app = SeaofBTCapp()
#app.geometry("800x600")
##ani = animation.FuncAnimation(f,animate, interval = 1000)
#app.mainloop()
    
#a=Solar()
#a.calc_Pmpp()
#b,c=a.get_P_Pmpp()

#print(b)



    