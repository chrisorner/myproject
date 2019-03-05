# -*- coding: utf-8 -*-
"""
Created on Thu Jan 17 06:24:43 2019

@author: chris
"""

import numpy as np

np.set_printoptions(threshold=np.nan)
from scipy.optimize import fsolve

# timestep for the SOC calculation
# d_len = 10
# d_hours = np.arange(1, 25, 1)
# t_len = np.size(d_hours)

# N_cells=1

# days are gui input
###setup time vectors dependend on days input

# t_ges = np.arange(1, t_len * d_len + 1, 1)


class Solar:

    def __init__(self, rad):
        t_ges = len(rad)
        self.P_solar = np.zeros(t_ges)

    def calc_power(self, rad):
        efficiency = 0.22
        self.P_solar = [i*efficiency for i in rad]
        return self.P_solar

    # todo change calculation of PV


class Battery:

    def __init__(self, rad):
        t_ges = len(rad) + 1
        # maximum storage capacity in Wh
        # Wmax only initialized, input from gui
        self.w_max = 100
        self.stored_energy = np.zeros(t_ges)
        self.SOC = np.zeros(t_ges)
        self.from_grid = np.zeros(t_ges)
        self.W_unused = np.zeros(t_ges)

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

    def calc_soc(self, rad, bat_capacity, cons_ener):
        d_len = int(len(rad) / 24)
        # Wmax input from GUI
        self.w_max = int(bat_capacity)
        cons = Consumer(rad)  # Energy that is consumed
        cons.calc_power(rad, cons_ener)
        p_store = cons.get_power_to_bat()  # Power that goes into battery

        for d in range(d_len):
            # print(d_len)
            # print(t_len)
            # t: hours 1-24
            # d_len: Number of days
            for i in range(24):
                # battery is neither full nor empty and can be charged/discharged
                if (self.stored_energy[i - 1 + 24 * d] + p_store[i] >= 0) and (
                        self.stored_energy[i - 1 + 24 * d] + p_store[i] <= self.w_max):  # charge
                    # Pmpp from solargen
                    self.stored_energy[i + 24 * d] = self.stored_energy[i - 1 + 24 * d] + p_store[i]
                    self.W_unused[i + 24 * d] = self.W_unused[i - 1 + 24 * d]



                # battery empty and cannot be discharged
                elif self.stored_energy[i - 1 + 24 * d] + p_store[i] < 0:
                    self.stored_energy[i + 24 * d] = 0
                    self.W_unused[i + 24 * d] = self.W_unused[i - 1 + 24 * d]
                    self.from_grid[i + 24 * d] = abs(p_store[i])
                    # print(i)


                # battery full and cannot be charged
                elif self.stored_energy[i - 1 + 24 * d] + p_store[i] > self.w_max:
                    # print(self.Wmax-self.stored_energy[i-1])
                    self.W_unused[i + 24 * d] = self.W_unused[i - 1 + 24 * d] + self.stored_energy[
                        i - 1 + 24 * d] + p_store[i] - self.w_max
                    self.stored_energy[i + 24 * d] = self.w_max

                self.SOC[i + 24 * d] = self.stored_energy[i + 24 * d] / self.w_max


class Consumer:
    # Energy that is used by consumer
    def __init__(self, rad):
        t_ges = len(rad) + 1
        self.power = np.zeros(t_ges)
        self.P_diff = np.zeros(t_ges)

    def get_power(self):
        x = self.power
        return x

    def get_power_to_bat(self):
        x = self.P_diff
        return x

    def calc_power(self, rad, power):
        self.power = power
        sol = Solar(rad)
        p_mpp = sol.calc_power(rad)


        for i in range(np.size(self.power)):
            self.P_diff[i] = p_mpp[i] / 1000 - self.power[i]


class Costs:
    def __init__(self, rad):
        d_len = int(len(rad) / 24)
        self.total_costs = np.zeros(d_len + 1)  # index 0 is always 0, costs start at index 1
        self.total_costs_sol = np.zeros(d_len + 1)

    def battery_invest(self, capacity, cost_per_kwh):
        invest = float(cost_per_kwh) * float(capacity)
        return invest

    def solar_invest(self, power, cost_per_kwp):
        # solar power in W but price per kwp
        invest = float(power) / 1000 * float(cost_per_kwp)
        return invest

    def calc_costs(self, rad, num_d, cost_kwh, capacity, cost_bat, power, cost_per_kwp, cons_ener):
        # cost calculated for 6 days without investmetn  costs using global d_len

        d_len = int(len(rad) / 24)

        # calculate total cost battery + solar cells + energy from grid
        num_d = int(num_d)
        cost_kwh = float(cost_kwh)
        cost_battery = self.battery_invest(capacity, cost_bat)
        cost_solar = self.solar_invest(power, cost_per_kwp)
        cons = Consumer(rad)
        cons.calc_power(rad,cons_ener)
        p_cons = cons.get_power()  # power req by consumer

        bat = Battery(rad)
        bat.calc_soc(rad, capacity, cons_ener)
        pow_from_grid = bat.get_from_grid()
        # print(P_cons)

        costs_per_day = cost_kwh * sum(p_cons)
        for i in range(d_len):
            self.total_costs[i + 1] = costs_per_day * (i + 1)

        # only over one day so that each element in total costs represents 1 day
        # cost_grid= cost_kwh*sum(pow_from_grid[0:24])
        # for i in range(d_len+1):
        # self.total_costs_sol[i]=cost_grid*i+cost_solar+cost_battery

        for i in range(d_len):
            cost_grid = cost_kwh * sum(pow_from_grid[i * 24:(i + 1) * 24 - 1])
            if len(rad) < 145:  # indicates forecast, then without investment
                self.total_costs_sol[i + 1] = self.total_costs_sol[
                                                  i] + cost_grid  # for short-term prediction without investment costs
            else:
                self.total_costs_sol[0] = cost_solar + cost_battery
                self.total_costs_sol[i + 1] = self.total_costs_sol[i] + cost_grid

## End of Calculations ###
