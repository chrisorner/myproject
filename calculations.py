# -*- coding: utf-8 -*-
"""
Created on Thu Jan 17 06:24:43 2019

@author: chris
"""

import numpy as np
import requests
import numpy as np
import pandas as pd
from geopy.geocoders import Nominatim
# finally, we import the pvlib library
import pvlib
from pvlib import pvsystem
from pvlib.forecast import GFS, NAM, NDFD, HRRR, RAP

np.set_printoptions(threshold=np.nan)
from scipy.optimize import fsolve


class Solar:

    def __init__(self, rad):
        t_ges = len(rad)
        self.P_solar = np.zeros(t_ges)

    def calc_power(self, rad, area, cell):
        efficiency = cell.efficiency
        self.P_solar = [i*area*efficiency/100 for i in rad]
        return self.P_solar


class Solar2:

    def __init__(self):

        self.latitude = 48.8566101
        self.longitude = 2.3514992
        self.tz= 'CET'
        self.surface_tilt = 30
        self.surface_azimuth = 180
        self.sun_zen= 0
        self.air_mass= 0

    def get_location(self, city):
        geolocator = Nominatim(user_agent="Enefso")
        location = geolocator.geocode(city)
        self.longitude = location.longitude
        self.latitude = location.latitude


    def forecast(self, lat, long, start, end):
        fm = GFS()
        forecast_data = fm.get_processed_data(lat, long, start, end)
        return forecast_data

    def calc_irrad(self, times, lat, lon, tz, city):
        tus= pvlib.location.Location(lat, lon, tz=tz, altitude=0, name=city)
        ephem_data = tus.get_solarposition(times)
        irrad_data = tus.get_clearsky(times)
        self.sun_zen = ephem_data['apparent_zenith']
        self.air_mass = pvlib.atmosphere.get_relative_airmass(self.sun_zen)
        dni_et = pvlib.irradiance.get_extra_radiation(times.dayofyear)

        total = pvlib.irradiance.get_total_irradiance(
            self.surface_tilt, self.surface_azimuth,
            ephem_data['apparent_zenith'], ephem_data['azimuth'],
            dni=irrad_data['dni'], ghi=irrad_data['ghi'], dhi=irrad_data['dhi'],
            dni_extra=dni_et, airmass=self.air_mass,
            model='isotropic',
            surface_type='urban')

        return total

    def pv_system(self,times, irrad, module):

        wind= pd.Series(5,index= times)
        temp= pd.Series(20, index= times)
        pressure= 101325
        airmass = self.air_mass
        am_abs = pvlib.atmosphere.get_absolute_airmass(airmass, pressure)
        solpos = pvlib.solarposition.get_solarposition(times, self.latitude, self.longitude)
        pvtemp = pvsystem.sapm_celltemp(irrad['poa_global'], wind, temp)

        sandia_modules = pvsystem.retrieve_sam(name='SandiaMod')
        sandia_module = sandia_modules[module]
        #sandia_module= module
        #module_names = list(sandia_modules.columns)

        aoi = pvlib.irradiance.aoi(self.surface_tilt, self.surface_azimuth,
                                   solpos['apparent_zenith'], solpos['azimuth'])

        effective_irradiance = pvlib.pvsystem.sapm_effective_irradiance(
            irrad['poa_direct'], irrad['poa_diffuse'],
            am_abs, aoi, sandia_module)

        sapm_1 = pvlib.pvsystem.sapm(effective_irradiance, pvtemp['temp_cell'], sandia_module)

        return sapm_1['p_mp'].values


class Battery:

    def __init__(self, rad):
        t_ges = len(rad) + 1
        # maximum storage capacity in Wh
        # Wmax only initialized, input from gui
        self.w_max = 100
        self.stored_energy = np.zeros(t_ges)
        self.SOC = np.zeros(t_ges)
        self.from_grid = np.zeros(t_ges) # Power drawn from grid
        self.W_unused = np.zeros(t_ges) # Power that is fed into grid
        self.p_store = np.zeros(t_ges) # Power that goes into battery

    def get_soc(self):
        x = self.SOC
        return x

    def get_w_unused(self):
        # Energy which is not used or stored
        x = self.W_unused
        return x

    def get_stored_energy(self):
        x = self.stored_energy
        return x

    def get_from_grid(self):
        x = self.from_grid
        return x

    def calc_soc(self, rad, bat_capacity, cons_ener, cell_area, cell):
        t_len = int(len(rad))
        # Wmax input from GUI
        self.w_max = int(bat_capacity)
        sol = Solar(rad)
        p_mpp = sol.calc_power(rad, cell_area, cell)
        for i in range(np.size(cons_ener)):
            self.p_store[i] = p_mpp[i] / 1000 - cons_ener[i]


        for i in range(t_len):
            # battery is neither full nor empty and can be charged/discharged
            if (self.stored_energy[i - 1] + self.p_store[i] >= 0) and (
                    self.stored_energy[i - 1] + self.p_store[i] <= self.w_max):  # charge
                # Pmpp from solargen
                self.stored_energy[i] = self.stored_energy[i] + self.p_store[i]
                self.W_unused[i] = self.W_unused[i - 1]



            # battery empty and cannot be discharged
            elif self.stored_energy[i - 1] + self.p_store[i] < 0:
                self.stored_energy[i] = 0
                self.W_unused[i] = self.W_unused[i - 1]
                self.from_grid[i] = abs(self.p_store[i])
                # print(i)


            # battery full and cannot be charged
            elif self.stored_energy[i - 1] + self.p_store[i] > self.w_max:
                # print(self.Wmax-self.stored_energy[i-1])
                self.W_unused[i] = self.stored_energy[
                    i - 1] + self.p_store[i] - self.w_max
                self.stored_energy[i] = self.w_max

            self.SOC[i] = self.stored_energy[i] / self.w_max


class Costs:
    def __init__(self, rad, inp_years, cost_kwh, power):
        self.t_len = int(len(rad))
        if len(rad) < 145:
            time_frame = self.t_len
        else:
            time_frame = inp_years

        self.cost_energy_inc = 0.01
        self.cost_basic = 100
        self.cost_kwh = float(cost_kwh)
        years = np.arange(inp_years)
        self.cost_var = self.cost_kwh * (1 + self.cost_energy_inc) ** years  # variable cost for energy
        self.cost_fix = power # Fix costs
        cost_dep = 5 * power / 1000 # cost depending on power consumption
        # Operational costs incl repair
        self.cost_operate = self.cost_fix + cost_dep
        self.inflation= 0.02
        self.feedInTariff = 0.1147 #€/kwh

        self.cons_year = np.zeros(self.t_len + 1)  # index 0 is always 0, costs start at index 1
        self.total_costs = np.zeros(time_frame + 1)
        self.total_costs_sol = np.zeros(time_frame + 1)
        self.cons_sol_year = np.zeros(self.t_len+1)
        self.feedIn_year = np.zeros(self.t_len+1)

    @property
    def cost_fix(self):
        return self.__cost_fix

    @cost_fix.setter
    def cost_fix(self, power):
        # Operational costs incl repair. For solar system above 8kW additional 21€/a for production counter is required
        if power/1000 > 8:
            self.__cost_fix = 148+21
        else:
            self.__cost_fix = 148


    def battery_invest(self, capacity, cost_per_kwh):
        invest = float(cost_per_kwh) * float(capacity)
        return invest

    def solar_invest(self, power, cost_per_kwp):
        # solar power in W but price per kwp
        # 𝐼𝑛𝑣𝑒𝑠𝑡𝑚𝑒𝑛𝑡 𝑐𝑜𝑠𝑡𝑠:𝑃𝑎𝑛𝑒𝑙𝑠, 𝐶𝑜𝑢𝑛𝑡𝑒𝑟, 𝑖𝑛𝑠𝑡𝑎𝑙𝑙𝑎𝑡𝑖𝑜𝑛, 𝑝𝑜𝑤𝑒𝑟 𝑒𝑙𝑒𝑐𝑡𝑟𝑜𝑛𝑖𝑐𝑠 (Average Germany)
        p_kw = (float(power) / 1000)
        invest_per_kw= float(cost_per_kwp)

        invest = p_kw**(-0.16) * p_kw * invest_per_kw * (1+0.19)
        return invest

    def calc_costs(self, rad, inp_years, capacity, cost_bat, power, cost_per_kwp, cons_ener, panel_area, cell):
        # cost calculated for 6 days without investmetn  costs using global d_len

        cost_battery = self.battery_invest(capacity, cost_bat)
        cost_solar = self.solar_invest(power, cost_per_kwp)

        p_cons = cons_ener  # power req by consumer

        bat = Battery(rad)
        bat.calc_soc(rad, capacity, cons_ener, panel_area, cell)
        pow_from_grid = bat.get_from_grid()
        pow_sell = bat.get_w_unused()


        if len(rad) < 145:  # indicates forecast, then without investment
            for i in range(self.t_len):
                cost_grid = self.cost_kwh * pow_from_grid
                # index 0 is 0
                self.total_costs[i + 1] = p_cons[i]*self.cost_kwh
                self.total_costs_sol[i + 1] = self.total_costs_sol[
                                              i] + cost_grid[i]  # for short-term prediction without investment costs
        else:
            self.total_costs_sol[0] = -cost_solar - cost_battery


            # calc the costs for the energy required from the grid (with solar panels)
            for i in range(self.t_len):

                # calc the daily costs without solar panels (1 year)
                self.cons_year[i + 1] = self.cons_year[i] + p_cons[i]
                # calc the daily costs with solar panels (1 year)
                self.cons_sol_year[i + 1] = self.cons_sol_year[i]+pow_from_grid[i]
                self.feedIn_year[i + 1] = self.feedIn_year[i] + pow_sell[i]


            # calculate the slope of the cost function with and without solar panels
            slope1 = self.cons_year[-1] / 365
            slope = self.cons_sol_year[-1]/365
            slope2 = self.feedIn_year[-1]/365
            for i in range(inp_years):
                # extrapolate the costs over the desired number of years
                # Barwertmethode
                self.total_costs[i+1] = self.total_costs[i]-(slope1*365*self.cost_var[i] +
                                                             self.cost_basic)*(1+self.inflation)**(-(i+1))
                self.total_costs_sol[i+1] = self.total_costs_sol[i]-(slope*365*self.cost_var[i] +
                                                self.cost_operate + self.cost_basic - slope2*365*self.feedInTariff) * \
                                                (1+self.inflation)**(-(i+1))


## End of Calculations ###
