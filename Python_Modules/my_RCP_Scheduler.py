"""
    Module Name: my_RCP_Scheduler.py
    
    THIS MODULE CONTAINS ALL PROCEDURES FOR SOLVING THE RESOURCE-CONSTRAINED PROJECT SCHEDULING PROBLEM

    This python file contains the following procedures:
    
    A. Required before use: Network analysis:
       = the function "create_priority_list" makes use of "calculate_critical_path" and so from my_CPM_Scheduler import *

    B. RCP Scheduling:

        - Heuristic scheduling (Experiment 3):
            * create_priority_list(...)
                = using "get_all_successors" and "get_all_predecessors" as subprocedures

            * Schedule Generation Schemes (SGS)
                - Parallel SGS (time incrementation):
                    ° parallel_sgs(...)
                    ° backward_parallel_sgs(...)
                        = This backward approach is necessary to calculate resource slack for Monte Carlo simulations
                          with resources (cf. Critical chain analysis)
            
                - Serial SGS (activity incrementation):
                    ° serial_sgs(...)
                        = using "build_sorted_activities_by_predecessors" as suprocedure
                - backward_serial_sgs(...)
                        = I never used this procedure
                        = using "build_sorted_activities_by_successors" as suprocedure
        
        - Optimal scheduling (Experiment 4): 
            * resource_scheduler_optimizer(...)
                = Integer Programming model to solve the RCPSP
       
        - Critical chain analysis: 
            - Calculate the critical chain and the resource slack for a resource feasible schedule in the procedure
              Calculate_critical_chain_and_resource_slack(...)
                 ° Step 1. derive_resource_flow_dependencies: Compute the resource flow network
                 ° Step 2. compute_critical_chain
                           (if multiple chains exist, select the one with the most (least) precedence (resource) relations))
                 ° Step 2. compute_resource_slack: 
                           = Forward and backward scheduling to compute the different between the start times of both schedules

    C. Visualization
            plot_resource_profiles
                = using "get_color_for_activity" as subprocedure to make sure each activity has a different colour

    D. References: 
        * Find a general introduction to the resource constrained project scheduling problem in:    
            Vanhoucke, M., 2024, 
            “A quest for projects with scarce resources: Seeking schedule intelligence through project data discovery” 
            Springer: 161 pages
            
        * Find a detailed description about the resource-constrained project scheduling problem in:
            Vanhoucke, M., 2013, 
            "Project management with dynamic scheduling: Baseline scheduling, risk analysis and project control"
            Springer: 318 pages (2nd edition)            


"""    

from Python_Modules.my_CPM_Scheduler import *

import matplotlib.pyplot as plt
import numpy as np
import math
import random
import heapq
import copy


###############################################################
###             CRITICAL CHAIN ANALYSIS                     ###    
### Calculate_critical_chain_and_resource_slack             ###    
###    -    derive_resource_flow_dependencies               ###    
###    -    compute_critical_chain                          ###    
###    -    compute_resource_slack                          ###    
###############################################################
def derive_resource_flow_dependencies(activity_dependencies, resource_feasible_schedule):
    """
    Creates a copy of the given activity_dependencies and adds new precedence
    relations between activities I and J when the start time of J equals the
    end time of I in resource_feasible_schedule, if no such relation already exists.

    Parameters
    ----------
    activity_dependencies : dict
        Dictionary of the form {activity_id: ([predecessors], [successors])}
    resource_feasible_schedule : dict
        Dictionary of the form {activity_id: [(name, duration, cost, start, end, slack)]}

    Returns
    -------
    resource_flow_activity_dependencies : dict
        A new dictionary with added resource-flow-based precedence relations.
    """
    # Deep copy to avoid modifying the original dependencies
    resource_flow_activity_dependencies = copy.deepcopy(activity_dependencies)

    # Extract start and end times
    start_times = {a: resource_feasible_schedule[a][0][3] for a in resource_feasible_schedule}
    end_times   = {a: resource_feasible_schedule[a][0][4] for a in resource_feasible_schedule}

    # Iterate over all pairs of activities
    for i in resource_feasible_schedule.keys():
        for j in resource_feasible_schedule.keys():
            if i == j:
                continue  # skip same activity
            
            # Check if end(I) == start(J)
            if end_times[i] == start_times[j]:
                preds_i, succs_i = resource_flow_activity_dependencies[i]
                preds_j, succs_j = resource_flow_activity_dependencies[j]
                
                # Only add if no relation exists
                if j not in succs_i and i not in preds_j:
                    succs_i.append(j)
                    preds_j.append(i)
                    resource_flow_activity_dependencies[i] = (preds_i, succs_i)
                    resource_flow_activity_dependencies[j] = (preds_j, succs_j)

    return resource_flow_activity_dependencies

def compute_critical_chain(activity_dependencies, resource_flow_activity_dependencies, resource_feasible_schedule):
    """
    Computes the critical chain (longest path) in the resource-flow-augmented network,
    preferring technological precedence links when multiple longest paths exist.

    Parameters
    ----------
    activity_dependencies : dict
        Original technological dependencies {activity: ([preds], [succs])}
    resource_flow_activity_dependencies : dict
        Combined network (technological + resource flows)
    resource_feasible_schedule : dict
        {activity_id: [(name, duration, cost, start, end, slack)]}

    Returns
    -------
    critical_chain : list
        Ordered list of activity IDs forming the critical chain
    critical_chain_length : float
        Total duration of the chain
    """

    durations = {a: resource_feasible_schedule[a][0][1] for a in resource_feasible_schedule}
    successors = {a: resource_flow_activity_dependencies[a][1] for a in resource_flow_activity_dependencies}

    # Tag each edge as 'tech' or 'resource'
    tech_edges = set()
    for a, (_, succs) in activity_dependencies.items():
        for s in succs:
            tech_edges.add((a, s))

    # Compute in-degree for topological sort
    in_degree = {a: len(resource_flow_activity_dependencies[a][0]) for a in resource_flow_activity_dependencies}

    # Kahn’s algorithm for topological sorting
    topo_order = []
    zero_in = [a for a in in_degree if in_degree[a] == 0]
    while zero_in:
        node = zero_in.pop(0)
        topo_order.append(node)
        for succ in successors[node]:
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                zero_in.append(succ)

    # Longest path computation with precedence preference
    longest_distance = {a: 0 for a in topo_order}
    predecessor = {a: None for a in topo_order}
    tech_count = {a: 0 for a in topo_order}  # number of technological edges in path

    for a in topo_order:
        for succ in successors[a]:
            new_dist = longest_distance[a] + durations[a]
            new_tech_count = tech_count[a] + ((a, succ) in tech_edges)

            # Update if longer, or same length but more tech edges
            if (new_dist > longest_distance[succ]) or (
                new_dist == longest_distance[succ] and new_tech_count > tech_count[succ]
            ):
                longest_distance[succ] = new_dist
                predecessor[succ] = a
                tech_count[succ] = new_tech_count

    # Identify end node (max distance)
    end_node = max(longest_distance, key=longest_distance.get)
    critical_chain_length = longest_distance[end_node]

    # Reconstruct the path
    critical_chain = []
    while end_node is not None:
        critical_chain.insert(0, end_node)
        end_node = predecessor[end_node]

    return critical_chain, critical_chain_length


def compute_resource_slack(
    activity_set,
    resource_flow_activity_dependencies,
    resource_requirements,
    resource_availability,
    resource_feasible_schedule
):
    """
    Computes resource-based slack times using a backward parallel SGS,
    based on the resource-flow-augmented dependency network.

    Parameters
    ----------
    activity_set : list
        List of all activity IDs (e.g., ['A1', 'A2', ..., 'A10'])
    resource_flow_activity_dependencies : dict
        Dictionary of the form {activity_id: ([predecessors], [successors])}
        including both technological and resource-flow relations.
    resource_requirements : dict
        Resource demand per activity (e.g., {'A1': {'R1': 2}, ...})
    resource_availability : dict
        Resource capacity (e.g., {'R1': 4})
    resource_feasible_schedule : dict
        {activity_id: [(name, duration, cost, start, end, slack)]}

    Returns
    -------
    resource_slack : dict
        {activity_id: resource_slack_value}
    """
    # Extract start and end times
    start_times = {a: resource_feasible_schedule[a][0][3] for a in resource_feasible_schedule}
    end_times   = {a: resource_feasible_schedule[a][0][4] for a in resource_feasible_schedule}

    # Priority list = end times
    priority_list = end_times.copy()

    # Project makespan derived from maximum end time
    project_makespan = max(end_times.values())

    # Run backward SGS
    updated_project_makespan, latest_start_times, latest_end_times, late_activity_schedule = backward_parallel_sgs(
        activity_set,
        resource_flow_activity_dependencies,
        resource_requirements,
        resource_availability,
        priority_list,
        project_makespan,
        debugInfo=False
    )

    # Compute resource slack
    resource_slack = {
        activity: latest_start_times[activity] - start_times[activity]
        for activity in activity_set
    }

    return resource_slack, late_activity_schedule


def Calculate_critical_chain_and_resource_slack(
    #activity_names, #Not necessary
    activity_set,
    activity_dependencies,
    resource_requirements,
    resource_availability,
    resource_feasible_schedule, # Resource feasible schedule from the RCPSP scheduler (optimal or priority rules)
    debugInfo = False
):
    
    """
    This procedure calculates for a given 'resource feasible schedule' the following 
        - the resource flow network
        - the critical chain 
        - the resource slack (using a backward parallel schedule generation scheme run)
    
    """
    
    # Step 1. Construct the resource flow network
    resource_flow_activity_dependencies = derive_resource_flow_dependencies(activity_dependencies,resource_feasible_schedule)

#    if debugInfo == True:
#        print("***** activity_dependencies = ", activity_dependencies)
#        print("***** resource_flow_activity_dependencies = ",resource_flow_activity_dependencies)

    # Step 2. Calculate the critical chain (optional, not necessary for Step 3)
    critical_chain, critical_chain_length = compute_critical_chain(
        activity_dependencies,
        resource_flow_activity_dependencies,
        resource_feasible_schedule
    )

    if debugInfo == True:    
        print("Critical Chain:", " → ".join(critical_chain))
        print("Critical Chain Length:", critical_chain_length)

    # Step 3. Compute the resource slack (backward scheduling with PSGS included)
    resource_slack, late_activity_schedule = compute_resource_slack(
        activity_set,
        resource_flow_activity_dependencies, # After calling the derive_resource_flow_dependencies
        resource_requirements,
        resource_availability,
        resource_feasible_schedule # The resource feasible schedule
    )
    
    if debugInfo == True:
        print("--- resource_slack = ",resource_slack)
    
    return critical_chain, resource_slack, late_activity_schedule




###############################################################
###             OPTIMAL IP MODEL FOR THE RCPSP              ###    
###############################################################


def resource_scheduler_optimizer(activity_names, activity_set, activity_dependencies, resource_availability, 
                                 resource_requirements, 
                                 priority_rule = "", # optional to determine the project time horizon (with priority rules)
                                 time_window = False, # optional to determine the time window of activities
                                 debugInfo = False):

    import pulp

    # Define the problem
    prob = pulp.LpProblem("RCPSP", pulp.LpMinimize)

    # Optional parameter "priority_rule"
    # = maximum time horizon (upper bound UB, variable = max_time)
    #     - The UB can be equal to a feasible solution found by priority rules (Experiment 3)
    #     - If no priority rule is chosen, the sum of the activity durations is taken
    #                                      (= worst-case duration if all activities run sequentially)
    priority_rules = ["SPT", "LPT", "MIS", "MTS", "LNRJ", "GRPW", "EST", "EFT", "LST", "LFT", "MSLK", "GRWC", "GCRWC"]
    if priority_rule in priority_rules:
        
        priority_list = create_priority_list(priority_rule, activity_names, activity_set, 
                                             activity_dependencies, resource_requirements, debugInfo = False)
    
        sorted_list = build_sorted_activities_by_predecessors(activity_set, activity_dependencies, priority_list)
        max_time, _, _ = serial_sgs(activity_names, activity_set, activity_dependencies,resource_requirements, 
                                    resource_availability, priority_list, debugInfo = False)
    else:
        max_time = sum(activity_set[a][0] for a in activity_set)# + 1
    #print("Upper bound T = ", max_time)    

    # Optional parameter "time_window"
    # = Defining the time windows for activities (reducing the number of decision variables)
    #     - The time window can be set equal to the complete time window between 0 and max_time (= no real time windows)
    #     - The time window can be set to the interval [earliest start time ES, latest start time LF]
    #           ° Earliest start times = forward calculations for critical path    
    #           ° Earliest start times = backward calculations for critical path (using max_time as project duration)
    #           Note: The code first calculates the critical path length (cpm)
    #                 The code then calculates the critical path schedule (cpm_schedule) with buffer = max_time - cpm
    #                 The cpm_schedule contains the ES and the LS = ES + slack)
    activity_range = {}
    if time_window == True:
        print("Restricting the time window to earliest start/finish for each activity")
        _, cpm, _, _ = calculate_critical_path(activity_set, activity_dependencies, activity_names)
        buffer = max_time - cpm
        _, max_ef, _, cpm_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, buffer)
        print("Critical path length = ", cpm)
        print("Upper bound (T) = ", max_ef)
        print("Buffer = ",buffer)
        for a, the_schedule in cpm_schedule.items():
            (_, duration, cost, es, ef, slack) = the_schedule[0]
            ls = es + slack   # latest start
            activity_range[a] = range(es, ls + 1) # store the valid range of start times (inclusive)
    else:
        # Use the full horizon for ALL activities
        for a in activity_set:
            activity_range[a] = range(0, max_time)
        
    # Decision variables: X[a, t] = 1 if activity a starts at time t
    X = {
        (a, t): pulp.LpVariable(f"X_{a}_{t}", cat='Binary')
        for a in activity_set
        for t in activity_range[a]        # <-- use feasible time window ONLY
    }

    # Makespan
    makespan = pulp.LpVariable("Makespan", lowBound=0, cat='Continuous')

    # Objective: minimize makespan
    prob += makespan


    # Each activity must start exactly once
    for a in activity_set:
        prob += pulp.lpSum(X[a, t] for t in activity_range[a]) == 1, f"StartOnce_{a}"


    # Precedence constraints
    for a, (predecessors, _) in activity_dependencies.items():
        for p in predecessors:
            duration_p = activity_set[p][0]
            prob += (
                pulp.lpSum(t * X[a, t] for t in activity_range[a])
                >=
                pulp.lpSum((t + duration_p) * X[p, t] for t in activity_range[p])
            ), f"Precedence_{p}_{a}"


    # Resource constraints
    for r_idx, resource in enumerate(resource_availability.keys()):
        # Determine global time horizon from all LS + durations
        all_times = set()
        for a in activity_set:
            es = min(activity_range[a])
        # get duration
            dur = activity_set[a][0]
            ls = max(activity_range[a])
            # activity may occupy time slots up to ls + dur - 1
            for tau in range(es, ls + dur):
                all_times.add(tau)

        for t in sorted(all_times):
            prob += pulp.lpSum(
                resource_requirements[a][r_idx] * X[a, ta]
                for a in activity_set
                for ta in activity_range[a]
                if ta <= t <= ta + activity_set[a][0] - 1   # occupancy condition
            ) <= resource_availability[resource], f"Resource_{resource}_at_{t}"


    # Makespan constraints
    for a in activity_set:
        duration_a = activity_set[a][0]
        prob += makespan >= pulp.lpSum(
            (t + duration_a) * X[a, t] for t in activity_range[a]
        ), f"Makespan_{a}"

    # Print the LP model
    if debugInfo:
        print(prob)

    print("Be a little patient... the problem you try to solve is NP-hard, so it can take a while...")
    print("(Even worse: it probably will take forever if your project is not small enough)")

    # Solve the problem
    prob.solve(pulp.PULP_CBC_CMD(msg=debugInfo))

    # Print results
    start_time_dict = {}
    end_time_dict = {}

    print(f"Optimal Project Makespan: {pulp.value(makespan)}")
    for a in activity_set:
        duration_a = activity_set[a][0]
        start_time = sum(t * pulp.value(X[a, t]) for t in activity_range[a])
        end_time = start_time + duration_a
        start_time_dict[a] = start_time
        end_time_dict[a] = end_time
        print(f"Start time of {a}: {start_time}")

    # Create activity_schedule dictionary and insert start times and end times
    # (= The returned output is similar to the CPM scheduler (except for the graph))
    total_cost = sum(cost for _, cost in activity_set.values())
    project_makespan = max(end_time_dict.values())
#    import math    
#    project_makespan = math.ceil(pulp.value(makespan))
    slack = 0 #Slack is not calculated here!
    # Create activity_schedule dictionary and insert start times and end times
    activity_schedule = {
        activity: [(activity_names[activity], duration, cost, start_time_dict.get(activity, 0), 
                    start_time_dict.get(activity, 0) + duration, 0)]  # Default slack
        for activity, (duration, cost) in activity_set.items()
    }            
    return project_makespan, total_cost, activity_schedule    

def resource_scheduler_optimizer_old(activity_names, activity_set, activity_dependencies, resource_availability, 
                                 resource_requirements, 
                                 priority_rule = "", # optional to determine the time horizon (with priority rules)
                                 time_window = False,
                                 debugInfo = False):

    import pulp

    # Define the problem
    prob = pulp.LpProblem("RCPSP", pulp.LpMinimize)

    # Maximum time horizon (upper bound UB) 
    #     The UB can be equal to a feasible solution found by priority rules (Experiment 3)
    #     If no priority rule is chosen, take the sum of the activity durations 
    #                                         (= worst-case duration if all activities run sequentially)
    priority_rules = ["SPT", "LPT", "MIS", "MTS", "LNRJ", "GRPW", "EST", "EFT", "LST", "LFT", "MSLK", "GRWC", "GCRWC"]
    if priority_rule in priority_rules:
        
        priority_list = create_priority_list(priority_rule, activity_names, activity_set, 
                                             activity_dependencies, resource_requirements, debugInfo = False)
    
        sorted_list = build_sorted_activities_by_predecessors(activity_set, activity_dependencies, priority_list)
        max_time, _, _ = serial_sgs(activity_names, activity_set, activity_dependencies,resource_requirements, 
                                    resource_availability, priority_list, debugInfo = False)
    else:
        max_time = sum(activity_set[a][0] for a in activity_set)# + 1

    print("Upper bound T = ", max_time)    
    
    # Under construction: Time windows for activities (reducing the number of decision variables)
    # activity_range 
    if time_window == True:
        print("Restricting the time window to earliest start/finish for each activity")
        _, cpm, _, activity_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names)
        buffer = max_time - cpm
        _, max_ef, _, activity_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, buffer)
        print("Critical path length = ", cpm)
        print("Upper bound (T) = ", max_ef)
        print("Buffer = ",buffer)
    
    # Decision variables: Binary variables X[a][t] (1 if activity 'a' starts at time t)
    X = {
        (a, t): pulp.LpVariable(f"X_{a}_{t}", cat='Binary')
        for a in activity_set
        for t in range(max_time)
    }

    # Makespan variable (time when last activity finishes)
    makespan = pulp.LpVariable("Makespan", lowBound=0, cat='Continuous')

    # Objective: Minimize the makespan
    prob += makespan

    # Each activity must start exactly once
    for a in activity_set:
        prob += pulp.lpSum(X[a, t] for t in range(max_time)) == 1, f"StartOnce_{a}"

    # Precedence constraints
    for a, (predecessors, _) in activity_dependencies.items():
        for p in predecessors:
            duration_p = activity_set[p][0]
            prob += pulp.lpSum(t * X[a, t] for t in range(max_time)) >= pulp.lpSum((t + duration_p) * X[p, t] for t in range(max_time - duration_p)), f"Precedence_{p}_{a}"

    # Resource constraints: At each time t, total resource use ≤ available resources
    for r_idx, resource in enumerate(resource_availability.keys()):
        for t in range(max_time):
            prob += pulp.lpSum(
                resource_requirements[a][r_idx] * X[a, ta]
                for a in activity_set
                    # from t - dur_a + 1 (inclusive) to t + 1 (exclusive, so to t)
                for ta in range(max(0, t - activity_set[a][0] + 1), t + 1) 
            ) <= resource_availability[resource], f"Resource_{resource}_at_{t}"

    # Makespan constraints: The project completion time is determined by the latest finishing activity
    for a in activity_set:
        duration_a = activity_set[a][0]
        prob += makespan >= pulp.lpSum((t + duration_a) * X[a, t] for t in range(max_time)), f"Makespan_{a}"

    # Print the LP model
    if debugInfo:
        print(prob)

    print("Be a little patient... the problem you try to solve is NP-hard, so it can take a while...")
    print("(Even worse: it probably will take forever if your project is not small enough)")

    # Solve the problem
    prob.solve(pulp.PULP_CBC_CMD(msg=debugInfo))

    # Print results
    start_time_dict = {}
    end_time_dict = {}

    print(f"Optimal Project Makespan: {pulp.value(makespan)}")
    for a in activity_set:
        duration_a = activity_set[a][0]
        start_time = sum(t * pulp.value(X[a, t]) for t in range(max_time))
        end_time = start_time + duration_a
        start_time_dict[a] = start_time
        end_time_dict[a] = end_time
        print(f"Start time of {a}: {start_time}")

    # Create activity_schedule dictionary and insert start times and end times
    # (= The returned output is similar to the CPM scheduler (except for the graph))
    total_cost = sum(cost for _, cost in activity_set.values())
    project_makespan = max(end_time_dict.values())
#    import math    
#    project_makespan = math.ceil(pulp.value(makespan))
    slack = 0 #Slack is not calculated here!
    # Create activity_schedule dictionary and insert start times and end times
    activity_schedule = {
        activity: [(activity_names[activity], duration, cost, start_time_dict.get(activity, 0), 
                    start_time_dict.get(activity, 0) + duration, 0)]  # Default slack
        for activity, (duration, cost) in activity_set.items()
    }            
    return project_makespan, total_cost, activity_schedule    


###############################################################
###             PRIORITY RULE CALCULATIONS                  ###    
###############################################################

def get_all_successors(activity_id, activity_dependencies):
    # Initialize a set to store all unique successors (direct and indirect)
    all_successors = set()
    
    # Helper function to recursively find successors
    def find_successors(current_activity):
        for succ in activity_dependencies.get(current_activity, ([], []))[1]:  # Get the successors
            if succ not in all_successors:
                all_successors.add(succ)
                find_successors(succ)  # Recurse to find successors of this successor
    
    # Start by finding all successors of the given activity_id
    find_successors(activity_id)
    
    return all_successors

def get_all_predecessors(activity_id, activity_dependencies):
    # Initialize a set to store all unique predecessors (direct and indirect)
    all_predecessors = set()
    
    # Helper function to recursively find predecessors
    def find_predecessors(current_activity):
        for pred in activity_dependencies.get(current_activity, ([], []))[0]:  # Get the predecessors
            if pred not in all_predecessors:
                all_predecessors.add(pred)
                find_predecessors(pred)  # Recurse to find predecessors of this predecessor
    
    # Start by finding all predecessors of the given activity_id
    find_predecessors(activity_id)
    
    return all_predecessors

def create_priority_list(priority_rule, activity_names, activity_set, activity_dependencies, resource_requirements, debugInfo = False):

    """
    Determine the priority list for each activity based on the specified priority rule.

    Parameters:
    - priority_rule: The abbreviated name of the priority rule to apply
    - activity_names: xxxxx
    - activity_set: Dictionary with activity durations and costs
    - activity_dependencies: Dictionary with activity key and tuple with (predecessors, successors)
    - resource_requirements: Dictionary with activity key and tuple of resource requirements for each resource
    - debugInfo: True or False

    Note: Some of the priority rules based on schedule information require CPM information, such as
    - earliest_start_times: Earliest activity start in the CPM schedule (ignoring resources)
    - latest_start_times: Latest activity start in the CPM schedule (ignoring resources)
    - Slack: Activity slack in the CPM schedule (ignoring resources)
    and that is why the "calculate_critical_path" procedure is called in this funtion

    Returns:
    - A numerical value representing the activity's priority (lower values indicate higher priority).
    
    Reference: The x rules come from the book TODO
    http://www.pmknowledgecenter.be/dynamic_scheduling/baseline/optimizing-regular-scheduling-objectives-priority-rule-calculations
    """
    # Define an empty priority list
    priority_list = []

    # Construct a CPM schedule: Necessary for the required data for the scheduling rules
    _, _, _, activity_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, False)

    # Loop over the activities
    for activity_id, (duration, cost) in activity_set.items():
        
        # Required data for the activity rules
        duration, cost = activity_set[activity_id]
        
        _, successors = activity_dependencies.get(activity_id, ([], []))  # Extract successors list
        successors_duration = sum(activity_schedule.get(succ, [(None, 0)])[0][1] for succ in successors)
        grpw = duration + successors_duration

        # Required data for the network rules
        #num_successors = len(activity_dependencies[activity_id][1])
        num_successors = len(successors)
        total_successors = get_all_successors(activity_id, activity_dependencies) # returning a set
        total_predecessors = get_all_predecessors(activity_id, activity_dependencies)

        #predecessors, successors = activity_dependencies.get(activity_id, ([], []))   
        all_activities = set(activity_dependencies.keys()) # Get all other activity IDs
        not_in_predecessors_or_successors = all_activities - total_successors - total_predecessors - {activity_id}
        count_nonrelated = len(not_in_predecessors_or_successors)
        
        if debugInfo == True:
            print("Activity ID =", activity_id)
            print("Set of total_successors = ", total_successors)
            print("Set of total_predecessors = ", total_predecessors)        
            print("Non-related = ",not_in_predecessors_or_successors)
        
        # Required data for the scheduling rules (given the activity_schedule from CPM)
        activity_data = activity_schedule.get(activity_id)
        activity_name, time, cost, earliest_start, end, slack = activity_data[0]
        latest_start = earliest_start + slack

        # Required data for the resource rules
        # TODO work_content = duration * sum or max (resource requirements)
        total_resources = sum(resource_requirements.get(activity_id, (0, 0, 0, 0)))
        workload = duration * total_resources
    
        # Loop over successors and compute their workloads
        cum_workload = workload
        for succ in successors:
            succ_duration = activity_schedule.get(succ, [(None, 0)])[0][1]  # Extract successor's duration
            succ_resources = sum(resource_requirements.get(succ, (0, 0, 0, 0)))  # Sum resources for successor
            cum_workload += succ_duration * succ_resources  # Add successor's workload

        # Activity rules
        if priority_rule == "SPT":  # Shortest Processing Time
            value = duration
        elif priority_rule == "LPT":  # Longest Processing Time
            value = -duration
        elif priority_rule == "min_cost":
            value = cost
        elif priority_rule == "max_cost":
            value = -cost

        # Network rules
        elif priority_rule == "MIS":  # Most Immediate Successors
            value = -num_successors
        elif priority_rule == "MTS":  # Most Total Successors
            value = -len(total_successors)
        elif priority_rule == "LNRJ":  # Least Non-Related Jobs
            value = count_nonrelated
        elif priority_rule == "GRPW":  # Greatest Rank Positional Weight
            value = -grpw

        # Scheduling rules (CPM)
        elif priority_rule == "EST":  # Earliest Start Time
            value = earliest_start
        elif priority_rule == "EFT":  # Earliest Finish Time
            value = earliest_start + duration
        elif priority_rule == "LST":  # Latest Start Time
            value = latest_start
        elif priority_rule == "LFT":  # Latest Finish Time
            value = latest_start + duration
        elif priority_rule == "MSLK":  # Minimum Slack
            value = slack

        # Resource rules
        elif priority_rule == "GRWC":  # Greatest Resource Work Content
            value = -workload #TODO
        elif priority_rule == "GCRWC":  # Greatest Cumulative Resource Work Content
            value = -cum_workload #TODO

        # Random rule
        else:
            value = random.random()

        priority_list.append((activity_id, value))
    
    return priority_list


###############################################################
###             SCHEDULE GENERATION SCHEMES                 ###    
###############################################################

def build_sorted_activities_by_successors(activity_set, activity_dependencies, priority_list):
    # Initialize the list of sorted activities
    sorted_activities = []
    
    # Create a dictionary for easy lookup of priorities
    priority_dict = {activity: priority for activity, priority in priority_list}
    
    # Keep track of the remaining activities to be scheduled
    remaining_activities = set(activity_set.keys())
    no_successors = [activity for activity in remaining_activities if not activity_dependencies.get(activity, ([], []))[1]]
    
    # Step 1: Start the process of scheduling activities
    while remaining_activities:
        
#        print("no_successors = ", no_successors)
        # Sort the activities with no successors by priority (descending order)
#        no_successors.sort(key=lambda activity: priority_dict.get(activity, float('inf')))
        no_successors.sort(key=lambda activity: priority_dict.get(activity, float('inf')), reverse=True)

        # Add the highest-priority activity with no successors to the sorted list
        current_activity = no_successors.pop(0)  # Select the first one with the highest priority
        sorted_activities.append(current_activity)
        remaining_activities.remove(current_activity)
#        print("current_activity = ", current_activity)
        
        # Step 2: Update no_successors by checking activities whose predecessors are all scheduled
        for remaining_activity in list(remaining_activities):
            if remaining_activity not in no_successors:
                successors = activity_dependencies.get(remaining_activity, ([], []))[1]
                # If all successors are in the sorted list, add the activity to no_successors
                if all(suc in sorted_activities for suc in successors):
                    no_successors.append(remaining_activity)
            
    return sorted_activities


def build_sorted_activities_by_predecessors(activity_set, activity_dependencies, priority_list):
    # Initialize the list of sorted activities
    sorted_activities = []
    
    # Create a dictionary for easy lookup of priorities
    priority_dict = {activity: priority for activity, priority in priority_list}
    
    # Keep track of the remaining activities to be scheduled
    remaining_activities = set(activity_set.keys())
    no_predecessors = [activity for activity in remaining_activities if not activity_dependencies.get(activity, ([], []))[0]]
    
    # Step 1: Start the process of scheduling activities
    while remaining_activities:
        
#        print("no_predecessors = ", no_predecessors)
        # Sort the activities with no predecessors by priority (ascending order, i.e. lower value = highest priority)
        no_predecessors.sort(key=lambda activity: priority_dict.get(activity, float('inf')))
        
        # Add the highest-priority activity with no predecessors to the sorted list
        current_activity = no_predecessors.pop(0)  # Select the first one with the highest priority
        sorted_activities.append(current_activity)
        remaining_activities.remove(current_activity)
#        print("current_activity = ", current_activity)
        
        # Step 2: Update no_predecessors by checking successors
        for remaining_activity in list(remaining_activities):
            if remaining_activity not in no_predecessors:
                predecessors = activity_dependencies.get(remaining_activity, ([], []))[0]
                # If all predecessors are in the sorted list, add the activity to no_predecessors
                if all(pred in sorted_activities for pred in predecessors):
                    no_predecessors.append(remaining_activity)
            
    return sorted_activities




def serial_sgs(activity_names, activity_set, activity_dependencies, resource_requirements, resource_availability, priority_list, debugInfo=False):

    """
    This procedure constructs a resource-feasible schedule using a Serial Schedule Generation Scheme (SSGS) with a given priority rule.
        = activity-incremented scheduling scheme
        = The algorithm iterates over the activities in the priority list, one activity at a time, 
        following the priority order while ensuring precedence constraints and resource feasibility.
        
    Parameters:
    - activity_set: Dictionary {activity: (duration, cost)}
    - activity_dependencies: Dictionary {activity: (predecessors, successors)}
    - resource_requirements: Dictionary {activity: (R1, R2, R3, ...)}
    - resource_availability: Dictionary {resource: max_available}
    - priority_list: List of tuples [(activity, priority_value)]
    
    Returns:
    - project_makespan: Total project duration
    - total_cost: Total project cost
    - activity_schedule: Dictionary {activity: [(name, duration, cost, start, end, slack)]}
        
    References: 
    - BOOK DS
    - Article at PM Knowledge Center: http://www.pmknowledgecenter.com/dynamic_scheduling/baseline/optimizing-regular-scheduling-objectives-schedule-generation-schemes
    """

    # Initialize data structures
    start_times = {}
    end_times = {}

    # Upper bound on project duration = sum of all activity durations
    max_time = sum(duration for duration, _ in activity_set.values())
    available_resources = {t: resource_availability.copy() for t in range(max_time + 1)}  # Dynamically allocated timeline

    # Convert priority list to dictionary
    priority_dict = dict(priority_list)

    # Sort activities based on priority (lower value = higher priority)
#    sorted_activities = sorted(activity_set.keys(), key=lambda act: priority_dict.get(act, float('inf')))
#    print("sorted_activities (before) = ", sorted_activities)
    
    sorted_activities = build_sorted_activities_by_predecessors(activity_set, activity_dependencies, priority_list)
#    print("sorted_activities (after) = ", sorted_activities)

    # Scheduling loop (one activity at a time)
    for activity in sorted_activities:
        if debugInfo == True:
            print("Activity ID = ", activity)
        # Find the earliest start time when all predecessors are finished (put earliest start default to 0 for activities without predecessors)
        predecessors = activity_dependencies.get(activity, ([], []))[0]
        earliest_start = max((end_times[pred] for pred in predecessors if pred in end_times), default=0) 
        
        duration, cost = activity_set[activity]
        required = resource_requirements[activity]

        # Find the first available time slot where resource constraints are met
        start_time = earliest_start
        while True:
            if all(available_resources[t][r] >= required[i] for i, r in enumerate(resource_availability) for t in range(start_time, start_time + duration)):
                break  # Found feasible start time
            start_time += 1  # Delay start time if resources are insufficient

        # Schedule the activity
        start_times[activity] = start_time
        end_times[activity] = start_time + duration

        # Reserve resources for the activity duration
        for t in range(start_time, start_time + duration):
            for i, r in enumerate(resource_availability):
                available_resources[t][r] -= required[i]

        if debugInfo:
            print(f"Scheduled Activity {activity}: Start = {start_time}, End = {end_times[activity]}, Required Resources = {required}")

    # Compute total cost and makespan
    total_cost = sum(cost for _, cost in activity_set.values())
    project_makespan = max(end_times.values())

    # Construct activity schedule
    slack = 0  # TODO: Compute slack
    activity_schedule = {
        activity: [(activity_names[activity], duration, cost, start_times[activity], end_times[activity], slack)]
        for activity, (duration, cost) in activity_set.items()
    }
    
    return project_makespan, total_cost, activity_schedule

def parallel_sgs(activity_names, activity_set, activity_dependencies, resource_requirements, 
                 resource_availability, priority_list, debugInfo = False):
    
    """
    This procedure constructs a resource-feasible schedule using a Parallel Schedule Generation Scheme (PSGS) with a given priority rule.
        = time-incremented scheduling scheme
        = The algorithm iterates over time and schedules all eligible activities in parallel as long as the precedence and resource constraints allow
        
    - Priority rule
        * This procedure requires a priority list which is created in "create_priority_list"
    
    This procedure constructs a resource-feasible schedule using a serial schedule generation scheme (SGS)
    with a given priority rule.
    
    Parameters:
    - activity_set: Dictionary {key: value} = {activity: (duration, cost)}
    - activity_dependencies: Dictionary {key: value} =  {activity: (predecessors, successors)}
    - resource_requirements: Dictionary {key: value} =  {activity: (R1, R2, R3, R4, ...)}
    - resource_availability: Dictionary {key: value} =  {resource: max_available}
    - priority_rule: String specifying the priority rule (obtained from "create_priority_list")
    
    Returns:
    - start_times: Dict {activity: start_time}
    - end_times: Dict {activity: end_time}
    - project_makespan = project makespan (or project duration)
    
    References: 
    - BOOK DS
    - Article at PM Knowledge Center: http://www.pmknowledgecenter.com/dynamic_scheduling/baseline/optimizing-regular-scheduling-objectives-schedule-generation-schemes
    """
    
    # Count the number of predecessors for each activity (will be decreases for every predecessor that is finished)
    remaining_predecessors = {a: len(activity_dependencies.get(a, [])[0]) for a in activity_set}

    # eligible activities ready to schedule: Activities without predecessors
    ready_activities = [a for a in activity_set if remaining_predecessors[a] == 0]
    
    # Make a dictionary of the list
    priority_dict = dict(priority_list)
    
    # Activity start and finish times (dictionary)
    start_times = {}
    end_times = {}

    # Resource availability per time unit
    time = 0
    ongoing_activities = []
    available_resources = {t: resource_availability[t] for t in resource_availability}

    # Schedule activities
    while ready_activities or ongoing_activities:
        # Sort ready activities by priority (ascending order, i.e. lower value = higher priority)
        ready_activities.sort(key=lambda act: priority_dict.get(act, float('inf')))  

        if debugInfo == True:
            print("Eligible activities = ",ready_activities)
            print("Ongoing activities = ",ongoing_activities)
        

        # Try to schedule the eligible activities at time (as long as no resource conflict occurs)
        new_ready = []
        for activity in ready_activities[:]:  # Iterate over a copy of the list (since it is changed in the loop)
            duration, cost = activity_set[activity]
            required = resource_requirements[activity]
            
            if debugInfo == True:            
                print(f"Activity {activity}: Duration = {duration}, Cost = {cost}, Required Resources = {required}")
                print("available_resources = ", available_resources)

            # Check if resource availability is high enough (no resource conflict) with i = index and r = resource name
            if all(available_resources[r] >= required[i] for i, r in enumerate(resource_availability)):
                # Schedule activity
                start_times[activity] = time
                end_times[activity] = time + duration
                
                if debugInfo == True:
                    print(f"  >> Schedule activity {activity} (start = {time})")

                # Reserve resources
                for i, r in enumerate(resource_availability):
                    available_resources[r] -= required[i]

                # Add to ongoing activities: heapq = min-heap
                    # the activity with the earliest end time will always be at the top of the heap. 
                    # If multiple activities have the same end time, they will be ordered by their activity identifier.
                heapq.heappush(ongoing_activities, (end_times[activity], activity))
                ready_activities.remove(activity)

        # Increase the time pointer to the smallest finish time of the ongoing activities
        if ongoing_activities:
            # Get the lowest time value (the root element of the heap)
            lowest_time = ongoing_activities[0][0]

            # List to store finished activities with the same lowest time
            finished_activities = []

            # Pop all activities with the same lowest time
            while ongoing_activities and ongoing_activities[0][0] == lowest_time:
                time, finished_activity = heapq.heappop(ongoing_activities)
                finished_activities.append((time, finished_activity))

            if debugInfo == True:
                print("New time pointer = ", time)

            # Initialize new_ready as an empty list to hold the new eligible activities
            new_ready = []

            # Process the finished activities
            for time, finished_activity in finished_activities:

                # Release resources again
                for i, r in enumerate(resource_availability):
                    available_resources[r] += resource_requirements[finished_activity][i]

                # Add new eligible activities
                for a in activity_set:
                    # Check if the finished activity is a predecessor of activity 'a'
                    if finished_activity in activity_dependencies.get(a, [])[0]:
                        remaining_predecessors[a] -= 1
                        if remaining_predecessors[a] == 0:
                            new_ready.append(a)       

            if debugInfo == True:
                print("New eligible activities = ", new_ready)
                            
        ready_activities.extend(new_ready)
    

    # Create activity_schedule dictionary and insert start times and end times
    # (= The returned output is similar to the CPM scheduler (except for the graph))
    total_cost = sum(cost for _, cost in activity_set.values())
    project_makespan = max(end_times.values())   
    
    # Calculate the resource slack 
    # Resource slack - Method 1. compute_resource_slack --> no longer used due to disadvantage
        # Disadvantage: Does not work in fractional values for activity start times which is problematic for the Monte Carlo simulations
    #resource_slack, latest_start_times, latest_end_times = compute_resource_slack(activity_set, activity_dependencies, resource_requirements, resource_availability, start_times, end_times, project_makespan)        

    # Resource slack - Method 2. backward_parallel_sgs
        # It uses the finish times of the forward approach as priority list for the backward approach (and reduce the project makespan)
        # Advantage. Works with integers and fractional values so can be used in the simulations
        # Note that I cannot do this for serial_sgs since that only works for integers (due to the time pointer in the resource profile)
        
    ##### NEW CODE SINCE OKTOBER 2025        
        
    # Construct the resource feasible schedule (forward or early schedule)
    early_activity_schedule = {
        activity: [(activity_names[activity], duration, cost, start_times.get(activity, 0), 
                    end_times.get(activity, 0), 0)]
        for activity, (duration, cost) in activity_set.items()
    }
        
    # Analyse the simulated resource feasible schedule (early_activity_schedule): 
        # - Calculate the resource flow network
        # - Identify the critical chain 
        # - Compute the resource slack 
        #   (using a backward parallel schedule generation scheme with end times of the schedule as priority values)
    critical_chain, resource_slack, late_activity_schedule = Calculate_critical_chain_and_resource_slack(
    #    #activity_names, #Not necessary
        activity_set,
        activity_dependencies,
        resource_requirements,
        resource_availability,
        early_activity_schedule,
        debugInfo = False
    )
      
    # Update the resource feasible schedule with the resource slack
    early_activity_schedule = {
        activity: [(activity_names[activity], duration, cost, start_times.get(activity, 0), 
                    end_times.get(activity, 0), resource_slack.get(activity, 0))]
        for activity, (duration, cost) in activity_set.items()
    }

    # Show the simulated schedules
#    plot_resource_profiles(early_activity_schedule, resource_availability, resource_requirements)    
#    print("Critical Chain:", " → ".join(critical_chain))

    
    return project_makespan, total_cost, early_activity_schedule, late_activity_schedule, None
    
        
    ##### OLD CODE BEFORE OKTOBER 2025    
        
    priority_list = end_times
    updated_project_makespan, latest_start_times, latest_end_times = backward_parallel_sgs(
        activity_set, activity_dependencies, resource_requirements, 
        resource_availability, priority_list, project_makespan, debugInfo=False)
    resource_slack = {activity: latest_start_times[activity] - start_times[activity] for activity in activity_set}
    
    #### I THINK THE RESOURCE_SLACK NEED TO BE ADAPTED IF THE PROJECT DOES NOT START AT 0 (and check whether resource slack can be lower than zero after this adaptation (yes it can!) so max(0,slack))
    
    # Check whether the backward approach could find an improvement
    epsilon = 0.1
    schedule_improvement = max(0, project_makespan - updated_project_makespan) if abs(project_makespan - updated_project_makespan) >= epsilon else 0
        
    # Print the start and finish times and resource slack
    if debugInfo == True:
        print("Project duration", project_makespan)
        print("Updated_project duration", updated_project_makespan)
        print("Earliest Start Times:", start_times)
        print("Earliest End Times:", end_times)
        print("Latest Start Times:", latest_start_times)
        print("Latest End Times:", latest_end_times)
        print("Resource slack = ",resource_slack)
    
    # Construct the schedule (earliest start)
    early_activity_schedule = {
        activity: [(activity_names[activity], duration, cost, start_times.get(activity, 0), 
                    end_times.get(activity, 0), resource_slack.get(activity, 0))]
        for activity, (duration, cost) in activity_set.items()
    }
    if debugInfo == True:
        print("early_activity_schedule  :", *[value[0][3] for value in early_activity_schedule.values()])
        
    # Construct the schedule (latest start) --> don't know whether we need this, and resource slack is not valid anymore
    late_activity_schedule = {
        activity: [(activity_names[activity], duration, cost, latest_start_times.get(activity, 0), 
                    latest_end_times.get(activity, 0), resource_slack.get(activity, 0))]
        for activity, (duration, cost) in activity_set.items()
    }

    if debugInfo == True:
        print("late_activity_schedule  :", *[value[0][3] for value in late_activity_schedule.values()])

    
    return project_makespan, total_cost, early_activity_schedule, late_activity_schedule, schedule_improvement

import heapq

def backward_serial_sgs(activity_set, activity_dependencies, resource_requirements, 
                          resource_availability, priority_list, project_makespan, debugInfo=False):
    # Initialize data structures
    start_times = {}
    end_times = {}

    # Upper bound on project duration = sum of all activity durations
    #max_time = sum(duration for duration, _ in activity_set.values())
    max_time = project_makespan
    available_resources = {t: resource_availability.copy() for t in range(max_time + 1)}

    # Convert priority list to dictionary
    priority_dict = dict(priority_list)

    # Sort activities based on priority (lower value = higher priority)
#    sorted_activities = sorted(activity_set.keys(), key=lambda act: priority_dict.get(act, float('inf')), reverse=True)
#    print("sorted_activities (before) = ", sorted_activities)
    
    sorted_activities = build_sorted_activities_by_successors(activity_set, activity_dependencies, priority_list)
#    print("sorted_activities (after) = ", sorted_activities)

    # Scheduling loop (one activity at a time, backward)
    for activity in sorted_activities:
        if debugInfo:
            print("Activity ID =", activity)

        # Find the latest finish time when all successors are scheduled
        successors = activity_dependencies.get(activity, ([], []))[1]
        latest_finish = min((start_times[succ] for succ in successors if succ in start_times), default=max_time)

        duration, cost = activity_set[activity]
        required = resource_requirements[activity]

        # Find the latest feasible start time where resources are available
        end_time = latest_finish
        while True:
            start_time = end_time - duration
            if start_time < 0:
                raise ValueError("Schedule is infeasible with given constraints.")
            if all(available_resources[t][r] >= required[i] for i, r in enumerate(resource_availability) for t in range(start_time, end_time)):
                break  # Found feasible time window
            end_time -= 1

        # Schedule the activity
        start_times[activity] = start_time
        end_times[activity] = end_time

        # Reserve resources for the activity duration
        for t in range(start_time, end_time):
            for i, r in enumerate(resource_availability):
                available_resources[t][r] -= required[i]

        if debugInfo:
            print(f"Scheduled Activity {activity}: Start = {start_time}, End = {end_time}, Required Resources = {required}")

    # Compute total cost and makespan
    total_cost = sum(cost for _, cost in activity_set.values())
    project_makespan = max(end_times.values())

    # Construct activity schedule
    slack = 0  # TODO: Compute slack
    activity_schedule = {
        activity: [(activity, duration, cost, start_times[activity], end_times[activity], slack)]
        for activity, (duration, cost) in activity_set.items()
    }
    
    # Compute project makespan (earliest start time of any activity)
    total_cost = sum(cost for _, cost in activity_set.values())
    makespan_reduction = min(start_times.values())
    updated_project_makespan = project_makespan - makespan_reduction


    return updated_project_makespan, total_cost, activity_schedule


def backward_parallel_sgs(activity_set, activity_dependencies, resource_requirements, 
                          resource_availability, priority_list, project_makespan, debugInfo=False):
    """
    Constructs a resource-feasible schedule using a Backward Parallel Schedule Generation Scheme (PSGS).
    The algorithm starts from the project duration and schedules all eligible activities in reverse order.
    
    Parameters:
    - activity_set: Dictionary {activity: (duration, cost)}
    - activity_dependencies: Dictionary {activity: (predecessors, successors)}
    - resource_requirements: Dictionary {activity: (R1, R2, R3, R4, ...)}
    - resource_availability: Dictionary {resource: max_available}
    - priority_list: List of tuples [(activity, priority)]
    - project_makespan: Total duration of the project
    
    Returns:
    - start_times: Dict {activity: start_time}
    - end_times: Dict {activity: end_time}
    - updated_project_makespan
    """

    # Count the number of successors for each activity (decreases when a successor is scheduled)
    remaining_successors = {a: len(activity_dependencies.get(a, [])[1]) for a in activity_set}

    # Eligible activities (activities without successors)
    ready_activities = [a for a in activity_set if remaining_successors[a] == 0]
    
    # Convert priority list to dictionary
    priority_dict = dict(priority_list)
    
    # Initialize start and finish times
    start_times = {}
    end_times = {}

    # Initialize resource availability per time unit
    time = project_makespan
    ongoing_activities = []
    available_resources = {r: resource_availability[r] for r in resource_availability}

    # Schedule activities in a backward manner
    while ready_activities or ongoing_activities:
        # Sort ready activities by priority (descending order, i.e. higher value = higher priority)
        # (descending order since the end times of the forward_parallel_sgs are given as priority, and high values must be scheduled first)
        ready_activities.sort(key=lambda act: priority_dict.get(act, float('-inf')), reverse=True)

        if debugInfo == True:
            print("Eligible activities:", ready_activities)
            print("Ongoing activities:", ongoing_activities)

        # Schedule eligible activities at the current time
        new_ready = []
        for activity in ready_activities[:]:  # Iterate over a copy of the list
            duration, cost = activity_set[activity]
            required = resource_requirements[activity]

            if debugInfo == True:
                print(f"Activity {activity}: Duration = {duration}, Cost = {cost}, Required Resources = {required}")
                print("Available resources:", available_resources)

            # Check if resources are available for scheduling
            if all(available_resources[r] >= required[i] for i, r in enumerate(resource_availability)):
                # Assign latest start and finish times
                end_times[activity] = time
                start_times[activity] = time - duration

                if debugInfo == True:
                    print(f"  >> Schedule activity {activity} (end = {time}, start = {start_times[activity]})")

                # Reserve resources for the duration of the activity
                for i, r in enumerate(resource_availability):
                    available_resources[r] -= required[i]
              
                # Add to ongoing activities: heapq = min-heap to track latest start times
                    # the activity with the latest start time will always be at the top of the heap: -start_times 
                    # If multiple activities have the same end time, they will be ordered by their activity identifier.
                heapq.heappush(ongoing_activities, (-start_times[activity], activity))
                ready_activities.remove(activity)


        # Move time backward to the latest start time of the ongoing activities
        if ongoing_activities:
            # Get the lowest time value (the root element of the heap) (this is the highest start time since stored as negative value)
            lowest_time = ongoing_activities[0][0]

            # List to store finished activities with the same lowest time
            finished_activities = []

            # Pop all activities with the same lowest time
            while ongoing_activities and ongoing_activities[0][0] == lowest_time:
                time, finished_activity = heapq.heappop(ongoing_activities)
                time = -time #restore the original time since negative values are stored
                finished_activities.append((time, finished_activity))

            if debugInfo == True:
                print("New time pointer = ", time)

            # Initialize new_ready as an empty list to hold the new eligible activities
            new_ready = []

            # Process the finished activities
            for time, finished_activity in finished_activities:

                # Release resources again
                for i, r in enumerate(resource_availability):
                    available_resources[r] += resource_requirements[finished_activity][i]

                # Add new eligible activities
                for a in activity_set:
                    # Check if the finished activity is a predecessor of activity 'a'
                    if finished_activity in activity_dependencies.get(a, [])[1]:
                        remaining_successors[a] -= 1
                        if remaining_successors[a] == 0:
                            new_ready.append(a)       

            if debugInfo == True:
                print("New eligible activities = ", new_ready)
                
        ready_activities.extend(new_ready)

    # Compute project makespan (earliest start time of any activity)
    total_cost = sum(cost for _, cost in activity_set.values())
    makespan_reduction = min(start_times.values())
    updated_project_makespan = project_makespan - makespan_reduction
    
    # Construct the backward schedule (i.e. the latest resource-feasible start schedule)
    slack = 0  # Slack has no meaning here
    late_activity_schedule = {
        activity: [(activity, duration, cost, start_times[activity], end_times[activity], slack)]
        for activity, (duration, cost) in activity_set.items()
    }
    
    # Adjust start_times and end_times to start from time 0 --> No, don't do it here!!
    #start_times = {a: start_times[a] - makespan_reduction for a in start_times}
    #end_times = {a: end_times[a] - makespan_reduction for a in end_times}

    # Print debug info
    if debugInfo == True:
        print("Start Times:", start_times)
        print("End Times:", end_times)

    return updated_project_makespan, start_times, end_times, late_activity_schedule


###############################################################
###             RESOURCE PROFILE VISUALIZATIONS             ###    
###############################################################

import hashlib

# Ensure a fixed order of colors for activities (avoiding random selection)
def get_color_for_activity(activity_id, color_names):
    # Use a hash function to ensure the same ID always maps to the same color
    hash_value = int(hashlib.md5(activity_id.encode('utf-8')).hexdigest(), 16)
    color_index = hash_value % len(color_names)  # Ensure it wraps around the color list
    return color_names[color_index]

      
def plot_resource_profiles(activity_schedule, resource_availability, resource_requirements, showName=True,
                                        xlabel_size=None, ylabel_size=None,
                                        xtick_size=None, ytick_size=None,
                                        legend_size=None,
                                        title_size=None):

#    global Value_xlabel_size, Value_ylabel_size, Value_xtick_size, Value_ytick_size, Value_title_size

    # Apply global defaults if parameters are None
    xlabel_size = xlabel_size if xlabel_size is not None else Value_xlabel_size
    ylabel_size = ylabel_size if ylabel_size is not None else Value_ylabel_size
    xtick_size = xtick_size if xtick_size is not None else Value_xtick_size
    ytick_size = ytick_size if ytick_size is not None else Value_ytick_size
    legend_size = legend_size if legend_size is not None else Value_legend_size
    title_size = title_size if title_size is not None else Value_title_size

    
    max_end = max(activity[0][4] for activity in activity_schedule.values())
    project_makespan=(math.ceil(max_end))

    #project_makespan=(math.ceil(project_makespan))
    # Define the time range for plotting
    max_time = project_makespan + 1 # You can adjust this based on the project duration
    time_range = np.arange(0, max_time)

    # Initialize resource usage over time
    resource_usage = {resource: np.zeros(max_time) for resource in resource_availability.keys()}
    
    """
    Generate different colors for activities like in:
    activity_colors = {
        'A': 'blue',
        'B': 'green',
        'C': 'orange',
        'D': 'red',
        'E': 'purple',
        'F': 'yellow'
    }
    """
    
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors

    # Get all named colors from Matplotlib
    color_names = list(mcolors.CSS4_COLORS.keys())  # 148 named colors
    
    activity_colors = {}

    # Iterate over the activities and add their resource usage
    for activity, schedule in activity_schedule.items():
        activity_name, duration, cost, start_time, end_time, slack = schedule[0]
        
        # Assign colors to activities (two options)
        # Option 1. Assign the color to the activity at random (choose this when you want other colors)
#        color=random.choice(color_names),  # Pick a random color from 148 named colors

        # Option 2. Assign the color to the activity (assuring that each activity ID always uses the same color
        color = get_color_for_activity(activity, color_names)
        
        activity_colors[activity] = color

        
        # Get resource requirements for the current activity
        if activity in resource_requirements:
            resource_reqs = resource_requirements[activity]  # We use the whole tuple here (not just the first option)

            # Add resource usage to the corresponding time intervals
            for t in range(int(start_time), int(end_time)):
                for i, resource in enumerate(resource_availability.keys()):
                    resource_usage[list(resource_availability.keys())[i]][t] += resource_reqs[i]

#    print("activity_colors = ", activity_colors)

#    max_usage = max(resource_usage[resource]) for resource in resource_availability

                    
    # Plot the resource profiles
    for i, resource in enumerate(resource_availability.keys()):
        plt.figure(figsize=(10, 6))

        # Plot the resource usage as a stepwise function (horizontal segments)
#        plt.step(time_range, resource_usage[resource], label=f'{resource} Usage', color='black', lw=2, where='post')
        plt.step(time_range, resource_usage[resource], 
                 label=f'{resource} Usage' if showName else 'Usage',
                 color='black', lw=2, where='post')

        # Plot the resource availability as a horizontal line across the entire time range:
#        plt.step(time_range, np.full_like(time_range, resource_availability[resource]), label=f'{resource} Availability', color='black', lw=2, where='post')       
#        plt.step(time_range, np.full_like(time_range, resource_availability[resource]),label=f'{resource} Availability', color='red', lw=2, where='post', linestyle='--')
        plt.step(time_range,np.full_like(time_range, resource_availability[resource]),
            label=f'{resource} Availability' if showName else 'Availability',
            color='red',lw=2,where='post',linestyle='--')
        
        # Track the bottom position for stacked rectangles
        bottom_position = np.zeros(max_time)

        # Draw activity rectangles for the current resource
        for activity, schedule in activity_schedule.items():
            activity_name, duration, cost, start_time, end_time, slack = schedule[0]
            
#            print("Activity name = ", activity_name)

            # Get resource requirements for the current activity
            if activity in resource_requirements:
                resource_reqs = resource_requirements[activity]

                #print(activity, start_time, end_time)
                # Create a rectangle for each activity showing resource use
                for t in range(int(start_time), int(end_time)):
                    # Adjust the bottom position to avoid overlaps
                    bottom_position[t] += resource_reqs[i]

                    # Plot the activity as a rectangle (bar)
#                    plt.bar(t+0.5, resource_reqs[i], width=1, bottom=bottom_position[t] - resource_reqs[i], 
#                            color=activity_colors[activity], alpha=0.6, label=activity_name if t == int(start_time) else "")

                    # Plot the activity as a rectangle (bar) (and put in the legend only when they use the resource)
#                    if resource_reqs[i] > 0:
#                        plt.bar(t + 0.5, resource_reqs[i], width=1, bottom=bottom_position[t] - resource_reqs[i], 
#                            color=activity_colors[activity], alpha=0.6, 
#                            label=activity_name if t == int(start_time) and activity_name not in plt.gca().get_legend_handles_labels()[1] else "")
                
                
                    if resource_reqs[i] > 0:
                        label_value = (activity_name if showName else activity)
                        # Only add the label once per activity
                        if t == int(start_time) and label_value not in plt.gca().get_legend_handles_labels()[1]:
                            label = label_value
                        else:
                            label = ""
    
                        plt.bar(
                            t + 0.5, resource_reqs[i], width=1, 
                            bottom=bottom_position[t] - resource_reqs[i], 
                            color=activity_colors[activity], alpha=0.6, 
                            label=label
                        )


        # Adjust the y-axis limit to stop at resource_availability[resource] + 1
        #plt.ylim(0, resource_availability[resource] + 1)
        
        # Set x-axis to start at zero and y-axis to stop at resource_availability[resource] + epsilon (e.g. 0.1 or 0.5)
        epsilon = 0.5
        plt.xlim(0, max_time)
        #plt.ylim(0, resource_availability[resource] + epsilon)
        plt.ylim(0, max(np.max(resource_usage[resource]), np.max(resource_availability[resource])) + epsilon)

        # Labels and title
        plt.xlabel('Time', fontsize=xlabel_size)
        plt.ylabel('Resource Usage', fontsize=ylabel_size)
        plt.title(f'Resource Profile for {resource}', fontsize=title_size)
        plt.xticks(fontsize=xtick_size)
        plt.yticks(fontsize=ytick_size)
        
        #plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        if legend_size > 0:
            plt.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=legend_size)
        plt.grid(True)
        plt.show()




