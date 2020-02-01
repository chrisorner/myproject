def set_parameters(numKids, yearly_cons, dist):

    with open('alpg/configs/example_external_inputs.py', 'r') as file:
        data = file.readlines()

    data[143] = 'numKids = ' + str(numKids) + '\n'
    data[144] = 'yearlyConsumption = ' + str(yearly_cons) + '\n'
    data[145] = 'distancetoWork = ' + str(dist) + '\n'


    with open('alpg/configs/example_external_inputs.py', 'w') as file:
        file.writelines(data)