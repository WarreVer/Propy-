"""
    Module Name: my_Project_Data.py
    
    THIS MODULE CONTAINS EXAMPLE DATA TO TEST THE PROCEDURES IN THE 10 EXPERIMENTS
    
    This python file contains the following procedures to read project data for the experiments:

        - Manually created data
            ° def get_project_data_pmkc_2016():
                = reads data from the book "Integrated project management sourcebook" 
                  (note that this book refers to the Project Management Knowledge Center, hence the abbreviation PMKC
            ° def get_project_data_1998_paper():
                = reads data from the paper 
                  "New computational results on the discrete time/cost trade-off problem in project networks"
            ° def get_project_data_ipmc_2014(projectID)
                = reads date from the book "Integrated project management and control"
            ° def get_project_data_ddpm_2018():
                = reads data from the book "The data-driven project manager"
            ° def get_project_data_ddpm_2018_extended():
                = reads and extends the data from the book "The data-driven project manager"
            ° def get_project_data_VMW():
                = read data for the VMW project from the book "Project management with dynamic scheduling"
        - Reading data from a data file (using the well-known Patterson format)
            ° read_patterson_file(filename)

        - Extra procedures:
            ° add_dummy_nodes_to_project_data: Cf. Important note below
            ° generate_random_activity_risk_classes(activity_names): 
                = Randomly generate risk classes to activities for schedule risk analysis (Monte Carlo simulations)

    Important note: Throughout all experiments, dummy start and dummy end nodes are added to the projects.
        - It is sometimes not necessary, but it is a good practice to always add them
        - Sometimes they are added automatically (e.g. Patterson files), sometimes not (e.g. manually created data)
        - Always run "add_dummy_nodes_to_project_data" with following parameters:
                    activity_set,
                    activity_names,
                    prl=None,                      # predecessors_list
                    sul=None,                      # successors_list
                    tct=None,                      # time_cost_trade_offs
                    arc=None,                      # activity_risk_classes
                    rr=None,                       # resource_requirements
                    debugInfo=False
        - This procedure must be called immediately after reading the data, 
              but BEFORE any other procedure (e.g. before "create_activity_network_dependencies")
        - The Dummy Start and Dummy End nodes are defined as follows:
                - An activity with activity_key equal to keyDummyStart or keyDummyEnd
                - An activity with activity_name equal to nameDummyStart or nameDummyEnd (TEST WHETHER THAT IS NECESSARY!)
                (that means that you can have other dummies that will not be seen as dummies)
    
        - Dummies already included:
            - read_patterson_file(filename)     : The Patterson files will always include a dummy start and dummy end node
            - get_project_data_1998_paper       : Manually created in my project data for Experiment 2
            
        - No dummies included 
        (in most manually created project data, I did not include dummies since the data are copy pasted from a software tool):
            get_project_data_pmkc_2016          : used in Experiment 5
            get_project_data_ipmc_2014          : used in Experiment 9
            get_project_data_ddpm_2018          : used in Experiments 1 and 6
            get_project_data_ddpm_2018_extended : used in Experiment 2
            get_project_data_VMW                : used in Experiment 2
        
    Note for Time/Cost optimisation (Experiment 2)
        - time_cost_trade_offs: The activity data is structured in a dictionary consisting of 
            - Keys: The dictionary keys ('A', 'B', 'C', etc.) represent activities
            - Values: The values are lists of tuples. 
                      Each tuple represents a pair of (duration, cost) for a specific option or trade-off.

    Reference: Find a general introduction to the generation of project data in:
        Vanhoucke, M., 2024, 
        “A quest for projects with scarce resources: Seeking schedule intelligence through project data discovery” 
        Springer: 161 pages
"""    

from Python_Modules.my_General_Functions import *
import random
import os

def add_dummy_nodes_to_project_data(
        activity_set,
        activity_names,
        prl=None,                      #predecessors_list
        sul=None,                      #successors_list
        tct=None,                      #time_cost_trade_offs
        arc=None,                      #activity_risk_classes
        rr=None,                       #resource_requirements
        debugInfo=False
    ):
    """
    Add dummy start and end nodes to project data dictionaries/lists in place.
    Assumes keyDummyStart, keyDummyEnd, nameDummyStart, nameDummyEnd are global.
    Ordering is not important.
    """

    global keyDummyStart, keyDummyEnd, nameDummyStart, nameDummyEnd

    # Skip if dummy nodes already exist
    if keyDummyStart in activity_names.keys() and keyDummyEnd in activity_names.keys():
        if debugInfo:
            print("Dummy nodes already exist — skipping dummy node creation.")
        return

    # Add dummy nodes in place (ordering not important)
    activity_set[keyDummyStart] = (0, 0)
    activity_set[keyDummyEnd] = (0, 0)

    activity_names[keyDummyStart] = nameDummyStart
    activity_names[keyDummyEnd] = nameDummyEnd

    if debugInfo:
        print("activity_set inside =", activity_set)
        print("activity_names inside =", activity_names)

    # Add to time_cost_trade_offs
    print("time_cost_trade_offs inside 1 =", tct)
    if tct is not None:
        tct[keyDummyStart] = [(0, 0)]
        tct[keyDummyEnd] = [(0, 0)]

    print("time_cost_trade_offs inside 2 =", tct)    
    # Add to resource_requirements
    if rr is not None and len(rr) > 0:
        tuple_length = len(next(iter(rr.values())))
        zero_tuple = tuple(0 for _ in range(tuple_length))
        rr[keyDummyStart] = zero_tuple
        rr[keyDummyEnd] = zero_tuple

    # Add to activity_risk_classes under "No Risk"
    if arc is not None:
        if "No Risk" not in arc:
            arc["No Risk"] = []
        arc["No Risk"].extend([keyDummyStart, keyDummyEnd])

    # Update predecessors_list
    if prl is not None:
        all_activities = set(prl.keys()) | {pred for preds in prl.values() for pred in preds}
        for activity in all_activities:
            if activity not in prl:
                prl[activity] = [keyDummyStart]
        activities_with_successors = {pred for preds in prl.values() for pred in preds}
        activities_no_successor = all_activities - activities_with_successors
        prl[keyDummyEnd] = list(activities_no_successor)

    # Update successors_list
    if sul is not None:
        all_activities = set(sul.keys()) | {suc for sucs in sul.values() for suc in sucs}
        for activity in all_activities:
            if activity not in sul or not sul[activity]:
                sul[activity] = [keyDummyEnd]
        activities_with_predecessors = {suc for sucs in sul.values() for suc in sucs}
        activities_no_predecessor = all_activities - activities_with_predecessors
        sul[keyDummyStart] = list(activities_no_predecessor)


def generate_random_activity_risk_classes(activity_names):

    # Define empty risk class categories
    activity_risk_classes = {
        "No Risk": [],
        "Variation": [],
        "Foreseen Uncertainty": [],
        "Unforeseen Uncertainty": []
    }
    # Extract risk class names
    risk_classes = list(activity_risk_classes.keys())

    # Randomly assign each activity to a risk class
    for activity in activity_names.keys():
        chosen_class = random.choice(risk_classes)
        activity_risk_classes[chosen_class].append(activity)

    # Print the result
    return activity_risk_classes


def read_patterson_file(filename):
    
    """
    The Patterson format is used a lot for the RCPSP, but can also be used for CPM scheduling (by ignoring resources)
        - nract = number of activities, including the dummy start and dummy end
        - The file only contains integer numbers, but this reading procedure transforms them as follows: 
            - Dummy Start: key = keyDummyStart and name = nameDummyStart
            - Dummy End: key = keyDummyEnd and name = nameDummyEnd
            - All other activities: Key = A1, A2, ..., A_nract-
            - Example Patterson files can be found at www.projectmanagement.ugent.be/research/data
    """

    # Initialize an empty dictionary
    activity_dict = {}
    dependencies_dict = {}
    activity_names = {}
    resource_requirements = {}
    resource_availability = {}

    if os.path.exists(filename):
        print("File successfully found")
    else:
        print(f"The file {filename} does not exist.")
    
    with open(filename, 'r') as file:
    
    # Read the Patterson file
        lines = list(filter(None, (line.strip() for line in file)))
    
        #lines = file.readlines()

        # The first line usually contains the number of activities and something else (not used in this case)
        first_line = lines[0].strip()
        values = list(map(int, first_line.strip().split()))

        nract = values[0]
        nrres = values[1]
     
        second_line = lines[1].strip()
        resource_data = list(map(int, second_line.split()))  # Convert to list of integers

        for i in range(1, nrres + 1):
            resource_availability["Resource " + str(i)] = resource_data[i - 1]  # Use i-1 to index resource_data


        # Iterate through each subsequent line
        for index, line in enumerate(lines[2:], start=0):  # Start at 0 for keys

            # Split the line into integers
            values = tuple(map(int, line.strip().split()))
            
#            print(values)

            # Add the values to the dictionary (using the index as key)
            activity_id = index
            activity_duration = values[0]
            if (activity_duration == 0): 
                activity_cost = 0 
            else: 
                activity_cost = random.randint(100, 500)
                
            resource_data = values[1:nrres+1]  # The rest of the values are associated data
        
            nr_suc = values[nrres+1]
            successors = values[nrres+2:]
            successors = ["A"+str(num-1) if num != nract else keyDummyEnd for num in successors]

            # assign dummy keys for start and end
            if activity_id == 0:
                key = keyDummyStart
                name = nameDummyStart
            elif activity_id == nract - 1:
                key = keyDummyEnd
                name = nameDummyEnd
            else:
                key = "A" + str(activity_id)
                name = "Activity " + str(activity_id)

            # now assign values to the dicts using the correct key
            activity_dict[key] = (activity_duration, activity_cost)
            activity_names[key] = name    
            
            dependencies_dict[key] = successors 
            resource_requirements[key] = resource_data

      
    # Generate additional data (necessary for the Jupyter notebook)
    # Generate additional data that is necessary for using the procedures in the Jupyter notebook
    #    - time_cost_trade_offs: Contains time/cost trade-offs, but here only one time/cost combination
    #    - activity_risk_classes: Each activity randomly assigned to the activity classes
        
    # Step 1. Transform the activity dictionary "activity_dict" from having single tuples (time/costs) 
    #         as values to having lists containing those tuples in "time_cost_trade_offs" 
    # (iterate through the original dictionary and wrap each tuple in a list)
    time_cost_trade_offs = activity_dict 
    time_cost_trade_offs = {key: [value] for key, value in time_cost_trade_offs.items()}
        
    # Step 2. Randomly add the activities into activity_risk_classes
    activity_risk_classes = generate_random_activity_risk_classes(activity_names)

    return time_cost_trade_offs, activity_dict, dependencies_dict, activity_names, resource_requirements, resource_availability, activity_risk_classes
    

def get_project_data_pmkc_2016():
    
    """
    Source: This example project is taken from the book 
        "Vanhoucke, M., 2016, 
        "Integrated project management sourcebook: A technical guide to project scheduling, risk and control”, 
        Springer: 287 pages."
    
    Note: 
        - The activity names have been changed from numbers (1, 2, ...) to characters (A, B, ...)
        - The costs have been multiplied by a factor 100
        
    Used in:
        - Example experiment 5
        
    """   
   
    activity_set = {
        'A': (20, 0),
        'B': (30, 0),
        'C': (10, 0),
        'D': (10, 0),
        'E': (20, 0),
        'F': (20, 0),
        'G': (10, 0),
        'H': (20, 0),
    }

    # Define the dependencies between activities (predecessors)
    predecessors_list = {
        'B': ['A'],
        'C': ['A'],
        'D': ['B'],
        'E': ['B', 'C'],
        'F': ['C'],
        'G': ['F'],
        'H': ['D', 'E', 'G'],
    }

    activity_names = {
        'A': 'Activity A',
        'B': 'Activity B',
        'C': 'Activity C',
        'D': 'Activity D',
        'E': 'Activity E',
        'F': 'Activity F',
        'G': 'Activity G',
        'H': 'Activity H',
    }

#    activity_risk_classes = {
#        "Variation": ["A", "B",],
#        "Foreseen Uncertainty": ["C", "E"],
#        "Unforeseen Uncertainty": ["D"]
#    }
    
    return activity_names, activity_set, predecessors_list


def get_project_data_1998_paper():
    
    """
    Source: This example project is an old one, since I used it for a study in my PhD.
        - It originally comes from my very first paper ever published in 1998 (figure 4)
        - I later used the example project again in my book "Dynamic Scheduling" (Figure 3.2)
    
    Note: 
        - The optimal solution with a project deadline of 14 is 34 euro as shown in Figure 6 of the paper
        - Remark: In the study, I use an activity-on-the-arc format, but I changed it into an activity-on-the-node format here

    Used in:
        - Example experiment 2: DTCTP and complete time/cost profile
        
    References: 
        - Book: 
            Vanhoucke, M., 2013, "Project management with dynamic scheduling: Baseline scheduling, risk analysis
            and project control", Springer: 318 pages (2nd edition) (https://doi.org/10.1007/978-3-642-40438-2)
        - Paper:
            Demeulemeester, E., De Reyck, B., Foubert, B., Herroelen, W. and Vanhoucke, M., 1998, 
            "New computational results on the discrete time/cost trade-off problem in project networks", 
            Journal of the Operational Research Society, 49(11), 1153–1163 (doi:10.1057/palgrave.jors.2600634).
    """   
    
  
    # Define the activities (nodes)
 
    time_cost_trade_offs = {
        keyDummyStart: [(0, 0)],  # (duration, cost)
        'A': [(11, 10), (5, 18)],
        'B': [(10, 3), (6, 7), (3, 8), (1, 15)],
        'C': [(5, 5)],
        'D': [(10, 2), (8, 5), (6, 6), (4, 8)],
        keyDummyEnd: [(0, 0)],
    }

    # Define the dependencies between activities (predecessors)
    predecessors_list = {
        'A': [keyDummyStart],
        'B': [keyDummyStart],
        'C': ['A'],
        'D': ['A', 'B'],
        keyDummyEnd: ['C', 'D'],
    }

    # Activity names
    activity_names = {
        keyDummyStart: nameDummyStart,
        'A': 'Activity A',
        'B': 'Activity B',
        'C': 'Activity C',
        'D': 'Activity D',
        keyDummyEnd: nameDummyEnd
    }

    # Activity risk classes
    activity_risk_classes = {
        "No Risk": [keyDummyStart, keyDummyEnd],
        "Variation": ["A"],
        "Foreseen Uncertainty": ["B", "D"],
        "Unforeseen Uncertainty": ["C"]
    }
    
    # Make activity_set with zero durations and costs
    activity_set = {key: (0, 0) for key in activity_names.keys()}
    
    return activity_set, time_cost_trade_offs, predecessors_list, activity_names, activity_risk_classes

def get_project_data_for_Lucy():
    
    """
    Source: This example project is not incorporated in my book 
            "Data-Driven Project Management with Python:
             Optimizing Schedules, Simulating Risk and Analyzing Project Performance through 10 Example Experiments"
        - This file was added only later, for my follow-up book (see reference below)
    
    Used in:
        - This project is not used in any experiment, but you can add to to Experiment 2 to optimize time/cost trade-offs
        
    References: 
        - Book: 
            Data-Driven Project Management: The Science and Stories Behind Project Decisions, Lannoo
    """   
    
  
    # Define the activities (nodes)
 
    time_cost_trade_offs = {
        keyDummyStart: [(0, 0)],  # (duration, cost)
        'A': [(5, 2500)],
        'B': [(4, 2700), (2, 3900)],
        'C': [(5, 2150), (3, 2500), (2, 2950), (1, 3600)],
        'D': [(3, 900), (2, 1000), (1, 1500)],
        'E': [(6, 2050), (4, 2250), (3, 3200), (2, 3700)],
        'F': [(4, 600)],        
        keyDummyEnd: [(0, 0)],
    }

    # Define the dependencies between activities (predecessors)
    predecessors_list = {
        'A': [keyDummyStart],
        'B': ['A'],
        'C': ['A'],
        'D': ['B'],
        'E': ['B', 'C'],
        'F': ['D', 'E'],
        keyDummyEnd: ['F'],
    }

    # Activity names
    activity_names = {
        keyDummyStart: nameDummyStart,
        'A': 'Activity 1',
        'B': 'Activity 2',
        'C': 'Activity 3',
        'D': 'Activity 4',
        'E': 'Activity 5',
        'F': 'Activity 6',        
        keyDummyEnd: nameDummyEnd
    }

    # Activity risk classes
    activity_risk_classes = {
        "No Risk": [keyDummyStart, keyDummyEnd],
        "Variation": ["A"],
        "Foreseen Uncertainty": ["B", "D"],
        "Unforeseen Uncertainty": ["C", "E", "F"]
    }
    
    # Make activity_set with zero durations and costs
    activity_set = {key: (0, 0) for key in activity_names.keys()}
    
    return activity_set, time_cost_trade_offs, predecessors_list, activity_names, activity_risk_classes


def get_project_data_ipmc_2014(projectID):
    
#    
#Project 1. Cost information system
    if projectID == 1:
        real_duration = (1, 3, 3, 3, 5, 3, 4, 2, 1, 1, 3, 1, 2, 1, 3, 2, 1)

        activity_names = {
            'A1': 'Kick-off meeting',
            'A2': 'Define database specifications',
            'A3': 'Define user interface specifications',
            'A4': 'Develop maintenance cost database',
            'A5': 'Develop improvement cost database',
            'A6': 'Develop production time database',
            'A7': 'Develop IT department user interface',
            'A8': 'Develop accounting department user interface',
            'A9': 'Develop management user interface',
            'A10': 'Develop factory floor user interface',
            'A11': 'Database integration',
            'A12': 'End user feedback IT department',
            'A13': 'End user feedback accounting department',
            'A14': 'End user feedback management',
            'A15': 'End user feedback factory floor',
            'A16': 'Full product integration',
            'A17': 'Project evaluation'
        }

        activity_set = {
            'A1': (1, 1000),
            'A2': (2, 15000),
            'A3': (2, 15000),
            'A4': (4, 6000),
            'A5': (3, 3900),
            'A6': (3, 3900),
            'A7': (3, 2700),
            'A8': (2, 2000),
            'A9': (1, 1500),
            'A10': (1, 1500),
            'A11': (2, 6000),
            'A12': (1, 1000),
            'A13': (1, 1000),
            'A14': (1, 1000),
            'A15': (1, 1000),
            'A16': (2, 4000),
            'A17': (1, 5000),
        }

        predecessors_list = {
            'A2': ['A1'],
            'A3': ['A1'],
            'A4': ['A2'],
            'A5': ['A2'],
            'A6': ['A2'],
            'A7': ['A3'],
            'A8': ['A3'],
            'A9': ['A3'],
            'A10': ['A3'],
            'A11': ['A4', 'A5', 'A6'],
            'A12': ['A7'],
            'A13': ['A8'],
            'A14': ['A9'],
            'A15': ['A10'],
            'A16': ['A11', 'A12', 'A13', 'A14', 'A15'],
            'A17': ['A11', 'A12', 'A13', 'A14', 'A15'],
        }

#Project 2. Patient transport system
    elif projectID == 2:
        real_duration = (1, 2, 4, 1, 4, 2, 3, 1, 2, 5, 4, 3, 5, 5, 3, 5, 2)

        activity_names = {
            'A1': 'Staff needs survey',
            'A2': 'ICT committee meeting',
            'A3': 'Requirements study',
            'A4': 'Request transport system supplier proposals',
            'A5': 'Negotiate best transport system offer',
            'A6': 'Request database supplier proposals',
            'A7': 'Negotiate best database offer',
            'A8': 'Kick-off meeting with staff',
            'A9': 'Installation of transport system',
            'A10': 'Installation of server',
            'A11': 'PC training for nursing staff',
            'A12': 'Code list creation',
            'A13': 'Filling the database',
            'A14': 'Practical training for nursing staff',
            'A15': 'Final check',
            'A16': 'Live pilot period',
            'A17': 'Project evaluation'
        }

        activity_set = {
            'A1': (1, 5000),
            'A2': (1, 2500),
            'A3': (3, 2100),
            'A4': (2, 3000),
            'A5': (2, 10000),
            'A6': (2, 3000),
            'A7': (2, 10000),
            'A8': (1, 6500),
            'A9': (4, 24000),
            'A10': (5, 2500),
            'A11': (3, 3300),
            'A12': (3, 5700),
            'A13': (4, 2400),
            'A14': (5, 45000),
            'A15': (1, 1500),
            'A16': (5, 500),
            'A17': (2, 10000),
        }

        predecessors_list = {
            'A2': ['A1'],
            'A3': ['A2'],
            'A4': ['A3'],
            'A5': ['A4'],
            'A6': ['A3'],
            'A7': ['A6'],
            'A8': ['A5', 'A7'],
            'A9': ['A8'],
            'A10': ['A8'],
            'A11': ['A8'],
            'A12': ['A8'],
            'A13': ['A8'],
            'A14': ['A9', 'A10', 'A11', 'A12', 'A13'],
            'A15': ['A13'],
            'A16': ['A14', 'A15'],
            'A17': ['A14', 'A15'],
        }

#Project 3. Old carriage house renovation
    elif projectID == 3:
        real_duration = (2, 3, 5, 2, 6, 1, 2, 1, 1, 1, 2, 2, 2, 1, 2, 1, 1)

        activity_names = {
            'A1': 'Demolition phase 1: roof & utilities',
            'A2': 'Demolition phase 2: masonry & floor',
            'A3': 'Structural work & sewage',
            'A4': 'Facade renovation',
            'A5': 'Roofing',
            'A6': 'Exterior joinery',
            'A7': 'Electricity',
            'A8': 'Plumbing',
            'A9': 'Heating & ventilation',
            'A10': 'Floor insulation & screed',
            'A11': 'Plasterboard',
            'A12': 'Devices & connections',
            'A13': 'Suspended ceiling',
            'A14': 'Interior joinery',
            'A15': 'Painting',
            'A16': 'Linoleum flooring',
            'A17': 'Furniture & cleanup'
        }

        activity_set = {
            'A1': (2, 20000),
            'A2': (2, 20000),
            'A3': (4, 120000),
            'A4': (3, 30000),
            'A5': (4, 80000),
            'A6': (1, 25000),
            'A7': (1, 10000),
            'A8': (1, 15000),
            'A9': (1, 25000),
            'A10': (1, 5000),
            'A11': (3, 12000),
            'A12': (2, 20000),
            'A13': (1, 10000),
            'A14': (1, 15000),
            'A15': (2, 6000),
            'A16': (1, 10000),
            'A17': (1, 20000),
        }

        predecessors_list = {
            'A2': ['A1'],
            'A3': ['A2'],
            'A4': ['A3'],
            'A5': ['A4'],
            'A6': ['A5'],
            'A7': ['A6'],
            'A8': ['A6'],
            'A9': ['A6'],
            'A10': ['A7', 'A8', 'A9'],
            'A11': ['A10'],
            'A12': ['A11'],
            'A13': ['A10'],
            'A14': ['A13'],
            'A15': ['A12', 'A14'],
            'A16': ['A15'],
            'A17': ['A16'],
        }

    else:
        print("No valid project ID")

    return activity_names, activity_set, predecessors_list

def get_project_data_ddpm_2018():

    activity_set = {
        'A': (6, 18000),
        'B': (2, 6000),
        'C': (8, 24000),
        'D': (14, 63000),
        'E': (12, 54000),
        'F': (4, 18000),
        'G': (4, 18000),
        'H': (12, 72000),
        'I': (13, 78000),
        'J': (4, 12000),
        'K': (4, 24000),
        'L': (8, 24000),
        'M': (4, 12000),
        'N': (5, 15000),
        'O': (4, 12000),
        'P': (3, 4500),
    }

    # Define the dependencies between activities 
    #(Only one list is neccessary, either predecessors_list or successors_list)
    predecessors_list = {
        'B': ['A'],
        'C': ['B'],
        'D': ['C'],
        'E': ['D'],
        'F': ['B'],
        'G': ['F'],
        'H': ['G'],
        'I': ['H'],
        'J': ['I'],
        'K': ['G'],
        'L': ['K'],
        'M': ['L'],
        'N': ['L'],
        'O': ['L'],
        'P': ['J', 'M', 'N', 'O'],
    }

    successors_list = {
        'A': ['B'],
        'B': ['C', 'F'],
        'C': ['D'],
        'D': ['E'],
        'E': [],
        'F': ['G'],
        'G': ['H', 'K'],
        'H': ['I'],
        'I': ['J'],
        'J': ['P'],
        'K': ['L'],
        'L': ['M', 'N', 'O'],
        'M': ['P'],
        'N': ['P'],
        'O': ['P'],
        'P': []
    }


    activity_names = {
        'A': 'Clearing the site',
        'B': 'Removal of trees',
        'C': 'Subsurface drainage',
        'D': 'Filling playing field/track',
        'E': 'Installation of artificial playing turf',
        'F': 'Excavation',
        'G': 'Pouring concrete footings',
        'H': 'Pouring supports for seat galleries',
        'I': 'Erecting pre-cast galleries',
        'J': 'Pouring seats',
        'K': 'Steel structure',
        'L': 'Roof',
        'M': 'Dressing rooms',
        'N': 'Painting',
        'O': 'Lights',
        'P': 'Scoreboard'
    }

    # This is not completely in line with Table 3.1 of the book (range is not the same) but approximately
    activity_risk_classes = {
        "No Risk": ["B", "E", "I"],
        "Variation": ["H", "M", "P"],
        "Foreseen Uncertainty": ["A", "L"],
        "Unforeseen Uncertainty": ["C", "D", "F", "G", "J", "K", "N", "O"]
    }
    return activity_names, activity_set, predecessors_list, successors_list, activity_risk_classes


def get_project_data_ddpm_2018_extended():
    # The input data with multiple time/cost combinations for each activity 
    # Define the activities (nodes)

    time_cost_trade_offs = {
        'A': [(6, 18000), (4, 22000)],
        'B': [(2, 6000)],
        'C': [(8, 24000), (10, 18000), (12, 12000)],
        'D': [(14, 63000)],
        'E': [(12, 54000), (19, 37000)],
        'F': [(4, 18000)],
        'G': [(4, 18000), (5, 16000), (7, 11000)],
        'H': [(12, 72000), (17, 55000)],
        'I': [(13, 78000), (11,82000)],
        'J': [(4, 12000)],
        'K': [(4, 24000)],
        'L': [(8, 24000), (6, 28000), (5, 32000)],
        'M': [(4, 12000), (6, 8000)],
        'N': [(5, 15000)],
        'O': [(4, 12000)],
        'P': [(3, 4500)],
    }

    # Define the dependencies between activities (predecessors)
    predecessors_list = {
        'B': ['A'],
        'C': ['B'],
        'D': ['C'],
        'E': ['D'],
        'F': ['B'],
        'G': ['F'],
        'H': ['G'],
        'I': ['H'],
        'J': ['I'],
        'K': ['G'],
        'L': ['K'],
        'M': ['L'],
        'N': ['L'],
        'O': ['L'],
        'P': ['J', 'M', 'N', 'O'],
    }


    activity_names = {
        'A': 'Clearing the site',
        'B': 'Removal of trees',
        'C': 'Subsurface drainage',
        'D': 'Filling playing field/track',
        'E': 'Installation of artificial playing turf',
        'F': 'Excavation',
        'G': 'Pouring concrete footings',
        'H': 'Pouring supports for seat galleries',
        'I': 'Erecting pre-cast galleries',
        'J': 'Pouring seats',
        'K': 'Steel structure',
        'L': 'Roof',
        'M': 'Dressing rooms',
        'N': 'Painting',
        'O': 'Lights',
        'P': 'Scoreboard'
    }

    activity_names = {
        'A': 'Desk research',
        'B': 'On site visit at best locations',
        'C': 'Brief staff on project goals',
        'D': 'Nurse training',
        'E': 'Scanner operator training',
        'F': 'Changes to scanner room',
        'G': 'Changes to waiting room experience',
        'H': 'Changes based on patient feedback',
        'I': 'Changes based on nurse feedback',
        'J': 'Changes based on physician feedback',
        'K': 'Select eligible candidates',
        'L': 'Identify candidates willing to participate',
        'M': 'Testing in age group 0-3 years old',
        'N': 'Testing in age group 4-8 years old',
        'O': 'Testing in age group 9-12 years old',
        'P': 'Evaluate patient experience'
    }

    activity_names = {
        'A': 'Research and development',
        'B': 'Tendering',
        'C': 'Identify high risk',
        'D': 'Flora explorations',
        'E': 'Fauna explorations',
        'F': 'Tendering hardware',
        'G': 'Select model aircraft',
        'H': 'Test compass and altimeter',
        'I': 'Test video camera',
        'J': 'Test photo camera',
        'K': 'Select autopilot chipset',
        'L': 'Select operating system',
        'M': 'Navigation software',
        'N': 'Pattern recognition software',
        'O': 'Mapping software',
        'P': 'Test flights'
    }

    activity_risk_classes = {
        "No Risk": [],
        "Variation": ["A", "B", "F", "J", "K", "M", "O", "P"],
        "Foreseen Uncertainty": ["C", "E", "G", "L", "N"],
        "Unforeseen Uncertainty": ["D", "H", "I"]
    }
    
    # Make activity_set with zero durations and costs
    activity_set = {key: (0, 0) for key in activity_names.keys()}

    return activity_set, time_cost_trade_offs, predecessors_list, activity_names, activity_risk_classes


def get_project_data_VMW():
    
    time_cost_trade_offs = {
    '1': [(7, 2000)],
    '2': [(13, 1000)],
    '3': [(10, 7970), (11, 7650), (12, 7400), (13, 7200), (14, 7036), (15, 6900), (16, 6784), (17, 6684)],
    '4': [(13, 6066), (14, 5580), (15, 5400), (16, 5246)],
    '5': [(31, 38064), (33, 36968)],
    '6': [(2, 1300), (3, 966)],
    '7': [(12, 8000), (14, 7822), (15, 7600), (16, 7500), (19, 7332), (20, 7262), (21, 7200), (22, 7142)],
    '8': [(20, 7500), (21, 7352), (22, 7222)],
    '9': [(14, 17570), (15, 17332), (16, 17124), (17, 16940), (19, 16630)],
    '10': [(22, 1500)],
    '11': [(11, 100908), (12, 93332), (13, 86922), (14, 81428), (15, 76666)],
    '12': [(17, 20764), (18, 20110), (19, 19526)],
    '13': [(10, 40000), (11, 38180), (13, 35384), (14, 34284), (15, 33332), (16, 32500)],
    '14': [(15, 39332), (16, 37250), (17, 35410), (18, 33776), (19, 32314), (20, 31000), (21, 29808), (22, 28726), (23, 27738), (24, 26832)],
    '15': [(11, 15544), (12, 15166), (13, 14846), (14, 14570), (15, 14232), (16, 14124)],
    '16': [(13, 63460), (14, 60714), (15, 58332), (16, 56250), (17, 54410), (18, 52776), (19, 51314)],
    '17': [(15, 7500)],
    '18': [(28, 70000), (29, 68274), (30, 66666), (31, 65160), (32, 63750), (33, 62424), (34, 61176), (35, 60000), (36, 58888), (37, 57836), (38, 56842), (39, 55896), (40, 55000), (41, 54146)],
    '19': [(3, 1932), (4, 1600), (5, 1400)],
    '20': [(3, 4000)],
    '21': [(2, 1300), (3, 966)],
    '22': [(17, 12822), (18, 12666), (19, 12526), (20, 12284)],
    '23': [(11, 9818), (12, 9410), (13, 9230), (14, 9000), (15, 8800), (16, 8624), (17, 8479), (18, 8332)],
    '24': [(8, 16000), (9, 15332), (10, 14800), (11, 14362), (12, 14000), (14, 13482), (15, 13200), (16, 13000), (17, 12822), (18, 12666)],
    '25': [(9, 24888), (10, 24400), (11, 24000), (12, 23666), (13, 23384), (14, 23142), (15, 22932), (16, 22750), (17, 22588), (18, 22444)],
    '26': [(1, 300)],
    '27': [(13, 18538), (14, 18284), (15, 18066), (16, 17874), (17, 17704), (18, 17554), (19, 17420), (20, 17300), (21, 17190), (22, 17090)],
    '28': [(15, 14532), (16, 14374), (18, 14110), (19, 14000), (20, 13900), (21, 13808)],
    '29': [(14, 15142), (15, 15000), (16, 14870), (17, 14764), (18, 14666), (19, 14578), (20, 14500), (21, 14428), (22, 14362)],
    '30': [(16, 21750), (17, 21528), (18, 21332), (20, 21000), (21, 20856), (23, 20608)],
    '31': [(15, 18400), (16, 18250)],
    '32': [(12, 25832), (13, 25384), (14, 25000), (16, 24374), (18, 23888), (19, 23684)],
    '33': [(13, 13152), (14, 13000), (15, 12866), (16, 12750), (17, 12646), (18, 12554), (19, 12472), (20, 12400), (21, 12332)],
    '34': [(14, 27284), (15, 27066), (16, 26874), (17, 26704), (18, 26554)],
    '35': [(12, 19832), (15, 19266), (17, 19000)],
    '36': [(9, 14888), (10, 14600), (11, 14362), (12, 14166), (13, 14000), (14, 13856), (15, 13732), (16, 13624), (17, 13528), (18, 13444)],
    '37': [(15, 50000), (16, 48750), (17, 47646)],
    '38': [(16, 15124), (17, 14940), (18, 14776)],
    '39': [(12, 18166), (14, 17570), (16, 17124), (18, 16776), (20, 16500), (21, 16380)],
    '40': [(14, 7856), (15, 7732), (16, 7624), (17, 7528), (18, 7444), (19, 7374), (20, 7300)],
    '41': [(15, 18666), (17, 17882), (18, 17554), (19, 17262), (21, 16760), (22, 16544)],
    '42': [(16, 32374), (17, 32116), (18, 31888), (19, 31684), (20, 31500)],
    '43': [(17, 14940), (18, 14776), (19, 14630), (20, 14500), (21, 14380), (22, 14272)],
    '44': [(10, 1200)],
}
    
    predecessors_list = {
    '1': [],
    '2': [],
    '3': [],
    '4': ['1', '2', '3'],
    '5': [],
    '6': [],
    '7': ['5', '6'],
    '8': ['4', '7'],
    '9': ['6'],
    '10': [],
    '11': [],
    '12': ['8', '9', '10', '11'],
    '13': [],
    '14': ['13'],
    '15': ['13'],
    '16': ['15'],
    '17': ['15'],
    '18': ['15'],
    '19': ['16', '17', '18'],
    '20': ['19'],
    '21': ['19'],
    '22': ['14', '20', '21'],
    '23': ['12', '22'],
    '24': ['23'],
    '25': ['23'],
    '26': ['24', '25'],
    '27': ['13'],
    '28': ['27'],
    '29': ['28'],
    '30': ['28'],
    '31': ['28'],
    '32': ['29', '30', '31'],
    '33': ['28'],
    '34': ['32', '33'],
    '35': ['34'],
    '36': ['27'],
    '37': ['36'],
    '38': ['37'],
    '39': ['37'],
    '40': ['37'],
    '41': ['38', '39', '40'],
    '42': ['37'],
    '43': ['41', '42'],
    '44': ['43'],
    }

    activity_names = {
        '1': 'Obtain building license for architecture',
        '2': 'Find contractor for architecture',
        '3': 'Obtain environmental license',
        '4': 'Execution of architectural work',
        '5': 'Design equipment',
        '6': 'Negotiations high voltage cabine (HVC)',
        '7': 'Specification/Public tender/Fabrication',
        '8': 'Execution',
        '9': 'Additional work on cables for HVC',
        '10': 'Updating existing high pressure room',
        '11': 'Constructing pipes between installations',
        '12': 'Coming into operation',
        '13': 'First draft design',
        '14': 'Find permission/contractor and construction pipeline',
        '15': 'Design',
        '16': 'Find permission',
        '17': 'Connection electricity',
        '18': 'Specification equipment',
        '19': 'Delivery equipment',
        '20': 'Execution',
        '21': 'Fitting in communication system',
        '22': 'Coming into operation',
        '23': 'Design for connection electricity',
        '24': 'Connection electricity',
        '25': 'Design/specification/delivery',
        '26': 'Execution/coming into operation',
        '27': 'First draft design',
        '28': 'Design',
        '29': 'License request',
        '30': 'Specification and public tender',
        '31': 'Environmental license and notification VLAREM',
        '32': 'Realisation',
        '33': 'Design/specification and request offer',
        '34': 'Execution',
        '35': 'Coming into operation',
        '36': 'First draft design',
        '37': 'Design',
        '38': 'File constructing license',
        '39': 'Specification',
        '40': 'File environmental license',
        '41': 'Realisation',
        '42': 'Design',
        '43': 'Execution',
        '44': 'Coming into operation',
    }
    
    # Make activity_set with zero durations and costs
    activity_set = {key: (0, 0) for key in activity_names.keys()}
    
    activity_risk_classes = generate_random_activity_risk_classes(activity_names)
    
    return activity_set, time_cost_trade_offs, predecessors_list, activity_names, activity_risk_classes