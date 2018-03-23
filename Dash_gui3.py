# -*- coding: utf-8 -*-
"""
Created on Sat Nov  4 09:58:33 2017

@author: Christian Orner
"""


#from matplotlib import style
#from matplotlib.figure import Figure
import numpy as np
np.set_printoptions(threshold=np.nan)
from scipy.optimize import fsolve

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

#style.use('ggplot')
LARGE_FONT= ("Verdana", 12)

 # timestep for the SOC calculation
t_step=1
d_hours=np.arange(0,24,t_step)
t_len=np.size(d_hours)

N_cells=1

#days are gui input
def time(days):
    global Input_days
    global t_ges
    global t_len
    global d_len
    
    #days=days.get()
    days=int(float(days))
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
        self.Uoc=0
        self.Isc=0
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
        self.Pmpp=np.zeros(np.size(d_hours))
        self.Pmax=0
#E= 600
#T= 350

    def solargen(self,I,R,Uoc,Isc,ktemp,E,T):
        #R=4        
        k= 1.38*10**(-23)
        q=1.602*10**(-19)
        UT= k*T/q
        const= float(Isc)/1000 
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
        Rad= np.zeros(np.size(d_hours))
        for i in range(np.size(d_hours)):        
            Rad[i]= (-a)*(d_hours[i]-14)**2+y
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
    
    def get_Pmax(self):
        x=self.Pmax
        return x

    
    def calc_Pmpp(self,N_cells,T,rad_ampl,rad_width,Isc,Uoc):
        Umax=np.zeros(np.size(self.R))
        Imax=np.zeros(np.size(self.R))
        Pmax_vec=np.zeros(np.size(self.R))
        
        #T= self.get_Temp()
        if float(Uoc)>0.7:
            self.Uoc=0.7
            corr_Uoc=Uoc/0.7
        else:
            self.Uoc=float(Uoc)
            corr_Uoc=1
        
        if float(Isc)>1:
            self.Isc=1
            corr_Isc=float(Isc)/1
        else:
            self.Isc=float(Isc)
            corr_Isc=1
            
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
        
            self.P=self.U*self.I*N_cells*corr_Isc*corr_Uoc
            self.Pmpp[e]=np.max(self.P)
        #print(self.Pmpp)
        
        for i in range(np.size(self.R)):
            x= fsolve(self.solargen, 0.8, args=(self.R[i],self.Uoc,self.Isc,self.ktemp,1000,T))
            Imax[i]=x
            Umax[i]=x*self.R[i]
            Pmax_vec[i]=Umax[i]*Imax[i]*N_cells*corr_Isc*corr_Uoc    
       # print(Pmax_vec)
        self.Pmax=np.max(Pmax_vec)
            
    
class Battery():
    def __init__(self):
        # maximum storage capacity in Wh
        # input from gui
#        C=Input_capacity.get()
        self.Wmax=100
        #self.stored_energy=np.zeros(np.size(t_ges))
        self.stored_energy=np.zeros(np.size(t_ges))
        self.SOC=np.zeros(np.size(t_ges))
        self.from_grid=np.zeros(np.size(t_ges))
        
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
    
    def get_from_grid(self):
        x=self.from_grid
        return x
        
        
    def calc_SOC(self,t,T,rad_ampl,rad_width,bat_capacity,Isc,Uoc):
        
        #k=0
        # time counting after SOC=1
        #t_lost=1
        #Pmpp=calc_Pmpp(Uoc, Isc, ktemp, E)
        self.Wmax=int(bat_capacity)
        Cons=Consumer()
        Cons.calc_power(T,rad_ampl,rad_width,Isc,Uoc)
        P_store=Cons.get_power_to_bat()
       # P, Pmpp=Solar.get_P_Pmpp()
        #consumer=0.8*Pmpp
        
        for d in Input_days:  
            for i in t:
                # battery is neither full nor empty and can be charged/discharged
                if (self.stored_energy[i-1+t_len*d]+P_store[i]>=0) and (self.stored_energy[i-1+t_len*d]+P_store[i]<=self.Wmax): #charge
                #Pmpp from solargen
                    self.stored_energy[i+t_len*d] = self.stored_energy[i-1+t_len*d] + P_store[i]
                    self.W_unused[i+t_len*d]=self.W_unused[i-1+t_len*d]
                    
                    
                
                # battery empty and cannot be discharged
                elif self.stored_energy[i-1+t_len*d]+P_store[i]<0:
                    self.stored_energy[i+t_len*d] = 0
                    self.W_unused[i+t_len*d]=self.W_unused[i-1+t_len*d]
                    self.from_grid[i+t_len*d]=abs(P_store[i])
                    #print(i)
                    
                    
                # battery full and cannot be charged    
                elif self.stored_energy[i-1+t_len*d]+P_store[i]>self.Wmax:
                    #print(self.Wmax-self.stored_energy[i-1])
                    self.W_unused[i+t_len*d] = self.W_unused[i-1+t_len*d] + self.stored_energy[i-1+t_len*d]+P_store[i]-self.Wmax
                    self.stored_energy[i+t_len*d] = self.Wmax
                    
                self.SOC[i+t_len*d]=self.stored_energy[i+t_len*d]/self.Wmax
                
                

class Consumer():
    
    def __init__(self):
        self.power = np.zeros(np.size(d_hours))
        self.P_diff=np.zeros(np.size(d_hours))
        
        
    def get_power(self):
        x= self.power
        return x
    
    def get_power_to_bat(self):
        x=self.P_diff
        return x
    
    def calc_power(self,T,rad_ampl,rad_width,Isc,Uoc):
        self.power = ([20,20,0,0,5,15,15,0,0,0,20,20,0,0,0,10,15,15,40,40,10,5,0,0])
        Sol=Solar()
        Sol.calc_Pmpp(N_cells,T,rad_ampl,rad_width,Isc,Uoc)
        P, Pmpp=Sol.get_P_Pmpp()
        
        for i in range(np.size(self.power)):
            self.P_diff[i] = Pmpp[i]-self.power[i]
            
class Costs():
    def __init__(self):
        #self.total_costs=np.zeros(d_len+1) # Costs must start at 0
        self.total_costs=np.zeros(5000)
        self.total_costs_sol=np.zeros(5000)
        # self.battery_invest=100
        
    def battery_invest(self,capacity,cost_per_wh):
        invest=float(cost_per_wh)*float(capacity)
        return invest
    
    def solar_invest(self,power,cost_per_wp):
        invest=float(power)*float(cost_per_wp)
        print(power,'power')
        return invest
    
   # def solar_invest(self,cost_power,power):
        
        
        
         
    def calc_costs(self,T,rad_ampl,rad_width,num_d,cost_kwh,capacity,cost_bat,power,cost_per_wp,Isc,Uoc):
        #100% grid supplly
        num_d=int(num_d)
        cost_kwh=float(cost_kwh)
        cost_battery=self.battery_invest(capacity,cost_bat)
        cost_solar=self.solar_invest(power,cost_per_wp)
        print(cost_solar,'cost solar')
        Cons=Consumer()
        Cons.calc_power(T,rad_ampl,rad_width,Isc,Uoc)
        P_cons=Cons.get_power() #power req by consumer
        #P_diff_cons_sol=Cons.get_power_to_bat() #difference between consumer and solar power
        Bat=Battery()
        Bat.calc_SOC(d_hours,T,rad_ampl,rad_width,capacity,Isc,Uoc)
        pow_from_grid=Bat.get_from_grid()
        
        costs_per_day=cost_kwh*sum(P_cons)
        for i in range(num_d):
            self.total_costs[i+1]=costs_per_day*(i+1)
        #print (self.total_costs,'total costs')
        
        
        
        #for i in range(np.size(P_diff_cons_sol)):
           # if P_diff_cons_sol[i] <0:
           #     pow_from_grid[i]=abs(P_diff_cons_sol[i])
          
               
        # only over one day so that each element in total costs represents 1 day        
        cost_grid= cost_kwh*sum(pow_from_grid[0:24])
        for i in range(num_d+1):
            self.total_costs_sol[i]=cost_grid*i+cost_solar+cost_battery
            #print(self.total_costs_sol[i],'with sol')
        
            
            
            

    
    
    
app = dash.Dash()

app.layout = html.Div([
        html.Div([html.H1(
                    'Solar Energy Calculator')]),
        html.Div([
            html.Div([
                dcc.Dropdown(
                        id='select_Graph',
                        options=[
                                {'label':'Radiation & Consumption', 'value':'rad_graph'},
                                {'label':'Energy Overview', 'value':'power_graph'},
                                {'label':'Costs', 'value':'cost_graph'}
                                ]
                        ),
                
                dcc.Graph(id='graph-with-slider'),
                    ],style={'width': '48%','height':'500px', 'display':'table-cell','verticalAlign': 'top'}),
        
             html.Div([
                    html.Div([
                                html.Div([
                                        html.H4('Some Parameter')],style=dict(dispaly='block')),
    
                                html.Div([
                                        html.Div([
                                                html.Label('Number of Days',id='days_label'),
                                                dcc.Input(id='days', value='2', type='text')],style=dict(display='table-cell')),
                                        html.Div([
                                                html.Label('Battery Capacity [kWh]',id='cap_label'),
                                                dcc.Input(id='capacity', value='100', type='text')],style=dict(display='table-cell'))                   
                                ],style={'display': 'table', })
                            ],style={'padding':'10px', 'border': 'thin solid grey'}),
                    html.Div([
                                html.Div([
                                        html.H4('Costs')],style=dict(dispaly='block')),
                                html.Div([
                                        html.Div([
                                                html.Label('Battery [EUR/kWh]',id='cost_label'),
                                                dcc.Input(id='cost_bat', value='10', type='text')],style={'width':'30%','display':'table-cell'}),
                                        html.Div([
                                                html.Label('Grid supply [EUR/kWh]',id='cost_label2'),
                                                dcc.Input(id='cost_kwh', value='0.3', type='text')],style={'width':'30%','display':'table-cell'}),
                                        html.Div([
                                                html.Label('Solar Panels [EUR/kWp]',id='cost_label3'),
                                                dcc.Input(id='cost_wp', value='200', type='text')],style={'width':'30%','display':'table-cell'}),
                                        ],style={'display': 'table'}),
                            ],style={'padding':'10px','border': 'thin solid grey'}),
                            
                    html.Div([
                                html.Div([
                                        html.H4('Data Sheet Solar Panel')],style=dict(dispaly='block')),
                                html.Div([
                                        html.Div([
                                                html.Label('Short Circuit Current [A]',id='Isc_label'),
                                                dcc.Input(id='Isc', value='1', type='text')],style={'width':'30%','display':'table-cell'}),
                                        html.Div([
                                                html.Label('Open Circuit Voltage [V]',id='Uoc_label'),
                                                dcc.Input(id='Uoc', value='0.6', type='text')],style={'width':'30%','display':'table-cell'}),
                                        html.Div([
                                                html.Label('Number of cells',id='N_cells_label'),
                                                dcc.Input(id='N_cells', value='1', type='text')],style={'width':'30%','display':'table-cell'}),
    
                                        ],style={'display': 'table'}),
                              ],style={'padding':'10px','border': 'thin solid grey'}),   
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
                                    value=1000,
                                    step=None,
                                    marks={str(i): str(i) for i in range(0,1100,100)}
                                        ),
                                html.P('Scaling factor [-]'),
                                dcc.Slider(
                                    id='rad_width',
                                    min=20,
                                    max=80,
                                    value=50,
                                    #step=None,
                                    marks={str(i): str(i) for i in range(20,80,10)}
                                        )],style={'padding': '20px','display': 'block'}
                                )],style={'width': '48%', 'display':'table-cell','verticalAlign': 'top'}
                        )],style=dict(display='table')
                ),
    
    
        

#'display': 'inline-block' 
#style={'width': '48%', 'float': 'right'} 

        
    ],style={'width': '100%', 'display': 'inline-block'})

    
    
@app.callback(
    dash.dependencies.Output('graph-with-slider', 'figure'),
    [dash.dependencies.Input('select_Graph','value'),
     dash.dependencies.Input('cost_bat','value'),
     dash.dependencies.Input('capacity','value'),
     dash.dependencies.Input('Ambient_Temp', 'value'),
     dash.dependencies.Input('rad_ampl', 'value'),
     dash.dependencies.Input('rad_width', 'value'),
     dash.dependencies.Input('days','value'),
     dash.dependencies.Input('cost_kwh', 'value'),
     dash.dependencies.Input('cost_wp', 'value'),
     dash.dependencies.Input('Isc', 'value'),
     dash.dependencies.Input('Uoc', 'value'),
     dash.dependencies.Input('N_cells', 'value')])
def update_cost(sel_graph, cost_bat,cap_bat, Temp, rad_ampl, rad_width, days_input,cost_kwh,cost_wp,Isc,Uoc,Ncells):
    global N_cells
    N_cells=float(Ncells)
    days_input=float(days_input)
    if days_input > 5 and sel_graph=='power_graph':
        days_input = 5

    time(days_input)
    
    Cost=Costs()
    Sol=Solar()
    Ncells=float(Ncells)
    Sol.calc_Pmpp(Ncells,Temp,rad_ampl,rad_width,Isc,Uoc)
    P,P_sol=Sol.get_P_Pmpp()
    print(Ncells)
    sol_power=Sol.get_Pmax()
    print(sol_power,'power2')
    Cost.calc_costs(Temp,rad_ampl,rad_width,days_input,cost_kwh, cap_bat, cost_bat,sol_power,cost_wp,Isc,Uoc)
    grid_costs=Cost.total_costs
    solar_costs=Cost.total_costs_sol
    
    Bat=Battery()
    Bat.calc_SOC(d_hours,Temp,rad_ampl,rad_width,cap_bat,Isc,Uoc)
    E_Batt= Bat.get_stored_energy()
    E_grid=Bat.get_from_grid()
    
    E=Sol.get_Rad(rad_ampl,rad_width)
    Cons=Consumer()
    Cons.calc_power(Temp,rad_ampl,rad_width,Isc,Uoc)
    P_cons=Cons.get_power()
    #print(days_input,'days')
    
    
    
    traces = []
    trace1=(go.Scatter(
        x=np.arange(0,int(days_input)+1,1),
        y=grid_costs,
        name='Without Solar Panels',
    ))
    
    trace2=(go.Scatter(
        x=np.arange(0,int(days_input)+1,1),
        y=solar_costs,
        name='With Solar Panels',
    ))
    
    trace3=(go.Scatter(
        x=t_ges,
        y=E_Batt,
        name='W_stored',
        marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
                },
    ))
    trace4=(go.Scatter(
        x=d_hours,
        y= P_sol,
        name='W_solar',
        marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'blue'}
                },
    ))
    trace5=(go.Scatter(
        x=t_ges,
        y= E_grid,
        name='W_grid',
        marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'green'}
                },
    ))
    trace6=(go.Scatter(
        x=d_hours,
        y=E,
        name = 'Radiation',
        yaxis='y1',
        marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
                },
    ))
    trace7=(go.Scatter(
        x=d_hours,
        y=P_cons,
        name='Consumption',
        yaxis='y2',
        marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'blue'}
                },
    ))
    
    
    
    
    traces=[trace1,trace2,trace3, trace4, trace5, trace6, trace7]
    
    if sel_graph=='cost_graph':
        return {
            'data': traces[0:2],
            'layout': go.Layout(
                title='Cost Estimation',
                xaxis={'title': 'Days'},
                yaxis={'title': 'Costs [Eur]'},
                legend=dict(x=-.1, y=1.2)
            )
        }
        
    elif sel_graph=='power_graph':
        return {
        'data': traces[2:5],
        'layout': go.Layout(
            title='Energy Overview',
            xaxis={'title': 'Time'},
            yaxis={'title': 'Energy [Wh]'},
            legend=dict(x=-.1, y=1.1, orientation = 'h')
        )
    }
    else:
        return {
        'data': traces[5:7],
        'layout': go.Layout(
                title='Daily Radiation and Consumption',
                xaxis={'title': 'Time'},
                yaxis1={'title': 'Radiation [W/m2]', 'range':[0,1000]},
                yaxis2={'title':'Consumption [W]','overlaying':'y','side':'right','range':[0,100]},
                legend=dict(x=-.1, y=1.2)
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



    
