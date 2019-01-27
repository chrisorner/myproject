# -*- coding: utf-8 -*-
"""
Created on Thu Jan 17 06:24:43 2019

@author: chris
"""

import numpy as np
np.set_printoptions(threshold=np.nan)
from scipy.optimize import fsolve


 # timestep for the SOC calculation
d_len=6
d_hours=np.arange(1,25,1)
t_len=np.size(d_hours)

#N_cells=1

#days are gui input
###setup time vectors dependend on days input
#def time(days):
#    global Input_days
#    global t_ges
#    global t_len
#    global d_len

    #days=days.get()
    #days=int(float(days))
    #Input_days=np.arange(0,days,1)
    #d_len=np.size(Input_days)
    #t_ges=np.arange(1,t_len*d_len+1,1)
t_ges=np.arange(1,t_len*d_len+1,1)   
    

class Solar():

    # Simple equivalent circuit model that is used to calculate U-I curve of solar cell
    def __init__(self):

        self.Uoc=0
        self.Isc=0
        self.ktemp= 0.3
        self.R= np.array([0.1,0.2,0.5, 0.6, 0.7, 0.8, 0.9, 1, 2, 3])
        self.I=np.zeros(np.size(self.R))
        self.U=np.zeros(np.size(self.R))
        self.I_plot=np.zeros(np.size(self.R))
        self.U_plot=np.zeros(np.size(self.R))


        self.P=np.zeros(np.size(self.R))
        self.Pmpp=np.zeros(np.size(t_ges))
        self.Pmax=0

    def solargen(self,I,R,Uoc,Isc,ktemp,E,T):
    
        k= 1.38*10**(-23)
        q=1.602*10**(-19)
        UT= k*T/q
        const= float(Isc)/1000


        Iph= E*const
        Uoc_T= self.Uoc+(-self.ktemp*0.01*(T-298))
        #print(Uoc_T)
        I0=self.Isc/(np.exp(Uoc_T/UT)-1)
        y=Iph-I0*(np.exp((I*R)/UT)-1)-I

        return y


    def get_Rad(self,rad_ampl,rad_width):
        # !! Not used anymore because radiation comes from API!!
        #Calculates radiation from GUI input
        a=rad_width
        y= rad_ampl
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


    def calc_Pmpp(self,N_cells,T,loc_rad,Isc,Uoc):
    # find the point on U-I curve with maximum power, mpp = maximum power point
        
        Umax=np.zeros(np.size(self.R))
        Imax=np.zeros(np.size(self.R))
        Pmax_vec=np.zeros(np.size(self.R))

       # Uoc and Isc must be between upper and lower bound for equation to work
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
        E= loc_rad
        
        
        for e in range(len(E)):
    
            k=0
            l=0
            #R is vector of resistances to get points on U-I curve
            for i in self.R:
                x= fsolve(self.solargen, 0.8, args=(i,self.Uoc,self.Isc,self.ktemp,E[e],T))
                
                self.I[k]=x
                self.U[k]=x*i

                # save I and U for the peak radiation to plot UI curve
                # This assumes that maximum power is obtained at 14:00
                if e == 14:
                    self.I_plot[l]=x
                    self.U_plot[l]=x*i
                    l+=1

                k+=1

            self.P=self.U*self.I*N_cells*corr_Isc*corr_Uoc
            self.Pmpp[e]=np.max(self.P)
         

        for i in range(np.size(self.R)):
            #Solves the solar cell model and returns the max power
            x= fsolve(self.solargen, 0.8, args=(self.R[i],self.Uoc,self.Isc,self.ktemp,1000,293))
            Imax[i]=x
            Umax[i]=x*self.R[i]
            Pmax_vec[i]=Umax[i]*Imax[i]*N_cells*corr_Isc*corr_Uoc
        self.Pmax=np.max(Pmax_vec)


class Battery():
    def __init__(self):
        # maximum storage capacity in Wh
        # Wmax only initialized, input from gui
        self.Wmax=100
        self.stored_energy=np.zeros(np.size(t_ges))
        self.SOC=np.zeros(np.size(t_ges))
        self.from_grid=np.zeros(np.size(t_ges))
        self.W_unused=np.zeros(np.size(t_ges))


    def get_SOC(self):
        x=self.SOC
        return x


    def get_W_unused(self):
        #Energy which is not used or stored
        x= self.W_unused
        return x

    def get_stored_energy(self):
        x=self.stored_energy
        return x

    def get_from_grid(self):
        x=self.from_grid
        return x


    def calc_SOC(self,Ncells,T,loc_rad,bat_capacity,Isc,Uoc,cons_ener):
        #Wmax input from GUI
        self.Wmax=int(bat_capacity)
        Cons=Consumer() #Energy that is consumed
        Cons.calc_power(Ncells,T,loc_rad,Isc,Uoc,cons_ener)
        P_store=Cons.get_power_to_bat() #Power that goes into battery
    
       

        for d in range(d_len):
            #print(d_len)
            #print(t_len)
            #t: hours 1-24
            #t_len: Number of days
            for i in range(t_len):
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
    # Energy that is used by consumer
    def __init__(self):
        self.power = np.zeros(np.size(t_ges))
        self.P_diff=np.zeros(np.size(t_ges))


    def get_power(self):
        x= self.power
        return x

    def get_power_to_bat(self):
        x=self.P_diff
        return x

    def calc_power(self,N_cells,Temp,loc_rad,Isc,Uoc,power):

        self.power= power
        Sol=Solar()
        Sol.calc_Pmpp(N_cells,Temp,loc_rad,Isc,Uoc)
        P, Pmpp=Sol.get_P_Pmpp()
        

        for i in range(np.size(self.power)):
            self.P_diff[i] = Pmpp[i]/1000-self.power[i]

class Costs():
    def __init__(self):
        self.total_costs=np.zeros(5000)
        self.total_costs_sol=np.zeros(5000)

    def battery_invest(self,capacity,cost_per_kwh):
        invest=float(cost_per_kwh)*float(capacity)
        return invest

    def solar_invest(self,power,cost_per_kwp):
        # solar power in W but price per kwp
        invest=float(power)/1000*float(cost_per_kwp)
        return invest



    def calc_costs(self,Ncells,T,rad_loc,num_d,cost_kwh,capacity,cost_bat,power,cost_per_kwp,Isc,Uoc,cons_ener):
        # cost calculated for 6 days without investmetn  costs using global d_len
        
        
        #calculate total cost battery + solar cells + energy from grid
        num_d=int(num_d)
        cost_kwh=float(cost_kwh)
        cost_battery=self.battery_invest(capacity,cost_bat)
        cost_solar=self.solar_invest(power,cost_per_kwp)
        Cons=Consumer()
        Cons.calc_power(Ncells,T,rad_loc,Isc,Uoc,cons_ener)
        P_cons=Cons.get_power() #power req by consumer
        
        Bat=Battery()
        Bat.calc_SOC(Ncells,T,rad_loc,capacity,Isc,Uoc,cons_ener)
        pow_from_grid=Bat.get_from_grid()

        costs_per_day=cost_kwh*sum(P_cons)
        for i in range(d_len):
            self.total_costs[i+1]=costs_per_day*(i+1)


        # only over one day so that each element in total costs represents 1 day
        cost_grid= cost_kwh*sum(pow_from_grid[0:24*6])
        for i in range(d_len+1):
            #self.total_costs_sol[i]=cost_grid*i+cost_solar+cost_battery
            self.total_costs_sol[i]=cost_grid*i #for short-term prediction without investment costs

## End of Calculations ###