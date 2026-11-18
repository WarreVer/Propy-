"""
    Module Name: my_TCT_Optimizer.py
    
    THIS MODULE CONTAINS ALL PROCEDURES FOR THE TIME/COST TRADE-OFF PROBLEM IN PROJECT SCHEDULING

    This python file contains the following procedures

        - select_minimum_activity_durations(time_cost_trade_offs, debugInfo = True)
        - select_maximum_activity_durations(time_cost_trade_offs, debugInfo = True)
        - time_cost_optimizer(time_cost_trade_offs, activity_dependencies, activity_names, deadline, debugInfo = False)
            = Integer Programming model for minimizing the total cost for a given deadline using the parameters
                - time_cost_trade_offs: Time/Cost values for activities
                - activity_dependencies
                - activity_names
                - deadline: value between select_minimum_activity_durations and select_maximum_activity_durations
        
        Reference: Find a general introduction to the discrete time/cost trade-off problem in:
            Vanhoucke, M., 2013, 
            "Project management with dynamic scheduling: Baseline scheduling, risk analysis and project control"
            Springer: 318 pages (2nd edition)
"""    

import pulp


# Select the minimum and maximum durations for each activity from "time_cost_trade_offs" dictionary
# Return an activity_set dictionary with "key: (time, cost)" with single tuple for each activity

def select_minimum_activity_durations(time_cost_trade_offs, debugInfo=False):

    # Step 1: Extract the minimum duration from each activity
    activities_min_duration = {}
    for activity, options in time_cost_trade_offs.items():
        # Find the option with the minimum duration
        min_option = min(options, key=lambda x: x[0])
#        min_duration = min(options, key=lambda x: x[0])[0]  # x[0] is the duration
#        min_cost = min(options, key=lambda x: x[0])[1]  # x[0] is the duration
        activities_min_duration[activity] = min_option  # Store the (duration, cost) tuple

    # Print results
    if (debugInfo == True):
        print("Activities with minimum durations:")
        for activity, (duration, cost) in activities_min_duration.items():
            print(f"{activity}: {duration} {cost}")

    return activities_min_duration

def select_maximum_activity_durations(time_cost_trade_offs, debugInfo=False):

    # Step 1: Extract the minimum duration from each activity
    activities_max_duration = {}
    for activity, options in time_cost_trade_offs.items():
        # Find the minimum duration for each activity
        max_option = max(options, key=lambda x: x[0])
        activities_max_duration[activity] = max_option

    # Print results
    if (debugInfo == True):
        print("Activities with maximum durations:")
        for activity, (duration, cost) in activities_max_duration.items():
            print(f"{activity}: {duration} {cost}")

    return activities_max_duration



def time_cost_optimizer(time_cost_trade_offs, activity_dependencies, activity_names, deadline, debugInfo = False):

    """
    Ths procedures solves the time/cost trade-off problem using integer programming (with PuLP)
    --> Inputs: 
            - time_cost_trade_offs (input data)
            - activity_dependencies
            - activity_names
            - deadline
            - (optional) debugInfo
    --> Output:
        - An "activity_schedule" dictionary "key: (activity name, time, cost, start, end, slack)" 
                                                      (slack is put to zero, not calculated here)
        - The minimum total project cost (model objective)
    """
    
    global predecessors_list
    
    # Create a linear programming problem to minimize cost
    problem = pulp.LpProblem("CriticalPathOptimization", pulp.LpMinimize)

    # Define decision variables for selecting duration and cost options for each activity
    duration_cost_vars = {}
    start_times = {}
    completion_times = {}

    for activity, options in time_cost_trade_offs.items():
        # Decision variable to choose which option is selected for each activity
        for i, (duration, cost) in enumerate(options):
            var_name = f"{activity}_{i+1}"
            duration_cost_vars[var_name] = pulp.LpVariable(var_name, cat='Binary')
    
        # Start time and completion time for each activity
        start_times[activity] = pulp.LpVariable(f"{activity}_start", lowBound=0)
        completion_times[activity] = pulp.LpVariable(f"{activity}_end", lowBound=0)

    # Objective function: Minimize total cost
    problem += pulp.lpSum([duration_cost_vars[f"{activity}_{i+1}"] * cost
                           for activity, options in time_cost_trade_offs.items()
                           for i, (_, cost) in enumerate(options)]), "Total_Cost"

    # Constraints: Ensure only one option is selected for each activity
    for activity in time_cost_trade_offs.keys():
        problem += pulp.lpSum([duration_cost_vars[f"{activity}_{i+1}"]
                               for i in range(len(time_cost_trade_offs[activity]))]) == 1, f"Select_one_duration_for_{activity}"

    # Dependency constraints and completion time constraints merged: 
    # Make sure that the start of a prodecessor + the selection duration is smaller/equal to start of activity
    for activity, (predecessors, _) in activity_dependencies.items():
        # Check if the activity is in time_cost_trade_offs
        if activity in time_cost_trade_offs:
            for predecessor in predecessors:
                problem += (
                    start_times[activity] >= start_times[predecessor] + 
                    sum(duration_cost_vars[f"{predecessor}_{i+1}"] * duration 
                        for i, (duration, _) in enumerate(time_cost_trade_offs[predecessor])),
                    f"Dependency_{predecessor}_to_{activity}"
                )            
                
    # Add the deadline constraint: The project must finish before the specified deadline
    project_duration = pulp.LpVariable("Project_Duration", lowBound=0)

    # Constraint: The project duration must be greater than or equal to the completion time of every activity
    for activity, options in time_cost_trade_offs.items():
        # Check if the activity has no successors by using the 'successors' list from activity_dependencies
        if len(activity_dependencies.get(activity, ([], []))[1]) == 0:  # No successors
            problem += (
                project_duration >= start_times[activity] + 
                sum(duration_cost_vars[f"{activity}_{i+1}"] * duration 
                    for i, (duration, _) in enumerate(options)),
                f"Completion_time_{activity}"
            )

    # Add the deadline constraint: The project must finish before or on the project deadline
    problem += project_duration <= deadline, "Project_Deadline"

    # Print the LP model
    if debugInfo == True:
        print(problem)

    # Solve the problem
    problem.solve(pulp.PULP_CBC_CMD(msg=False))

    # Output the results
    if debugInfo == True: 
        print("Status:", pulp.LpStatus[problem.status])

    selected_options = {}
    for activity in time_cost_trade_offs.keys():
        for i in range(len(time_cost_trade_offs[activity])):
            var_name = f"{activity}_{i+1}"
            if duration_cost_vars[var_name].varValue == 1:
                selected_options[activity] = time_cost_trade_offs[activity][i]
                break

    # Output selected activities and their duration/cost
    if debugInfo == True: 
        for activity, (duration, cost) in selected_options.items():
            print(f"Activity: {activity}, Duration: {duration}, Cost: {cost}, Start Time: {pulp.value(start_times[activity])}, End Time: {pulp.value(completion_times[activity])}")

    # Total cost
    total_cost = pulp.value(problem.objective)
    if debugInfo == True: 
        print("Total Cost:", total_cost)
  
    #### Collect the optimal solution of this problem (as a list containing a single tuple per activity) ####

    activity_schedule = {}
    for activity, (duration, cost) in selected_options.items():
        start = pulp.value(start_times[activity])
        end = pulp.value(completion_times[activity])
        # Use a tuple (activity name, duration, cost, start, end, slack) with slack = irrelevant
        activity_schedule[activity] = [(activity_names[activity], duration, cost, start, end, 0)]
        
    return total_cost, activity_schedule
