"""
    Module Name: my_Indicator_Calculator.py
    
    This module calculates the network and resource indicators for a project
    
    THIS MODULE CONTAINS ALL INDICATOR CALCULATIONS 
    (BUT DUMMIES CAN BE A PROBLEM SO READ CAREFULLY THE NOTE FOR "calculate_network_topology_indicators")
    
    A. Network indicators: 
        Procedure: calculate_network_topology_indicators
            - calculate_levels_and_widths
            - calculate_serial_parallel_indicator
            - calculate_activity_distribution
            - calculate_length_of_arcs
            - calculate_topological_float
        Note: I have two versions of "calculate_network_topology_indicators" to show the "danger" of dummy start and end nodes
            Version 1. calculate_network_topology_indicators(activity_set, activity_dependencies, activity_names, ...)
                = Automatically creates a graph without dummies (correct calculations of the network indicators)
            Version 2. calculate_network_topology_indicators_two_phases(G):
               = Uses a graph G as input (Be careful: when it contains dummies, network calculations are wrong)!    
            
    B. Resource indicators:
        Procedure: calculate_resource_scarcity_indicators(parameters)
          with parameters: - activity_schedule: Output of the "calculate_critical_path" procedure
                                                So run "_,_,_,activity_schedule = calculate_critical_path()" first
                                                = necessary for the Resource Strength indicator that depends on the CPM schedule
                           - other data: activity_set, resource_requirements, resource_availability
                           
        # Two indicators measure the resource demand (1 value for each project):            
            - calculate_resource_use(activity_set, resource_requirements)
            - calculate_resource_factor(activity_set, resource_requirements)

        # Two indicators measure the resource availability (1 value for each resource):
            - calculate_resource_constrainedness
            - calculate_resource_strength
                using: calculate_maximum_resource_use_for_a_schedule
                
    C. Reference: Find a general introduction to project network and resource scarcity indicators in:
         Vanhoucke, M., 2024, 
         “A quest for projects with scarce resources: Seeking schedule intelligence through project data discovery” 
         Springer: 161 pages
"""    

from Python_Modules.my_CPM_Scheduler import *
import networkx as nx
import math

############################################################    
###         Calculate the network indicators             ###    
############################################################


def calculate_network_topology_indicators(activity_set, activity_dependencies, activity_names, writeOutput = False):
    
    '''
    This procedure calculates the network topology metrics with an automatically created network graph G WITHOUT the dummy nodes
        = the use of dummy nodes extends the network and biases the network topology indicators
        
    Compare this with the alternative approach in calculate_network_topology_indicators_two_phases which uses a graph G as input
        - When G contains no dummies: Correct results
        - When G contains dummies: Wrong results
    '''
    
    G = construct_activity_network(activity_set, activity_dependencies, activity_names, debugInfo=False, visualize=False, includeDummy=False)
    
    SP = calculate_serial_parallel_indicator(G)

    progressive_levels, regressive_levels, progressive_widths = calculate_levels_and_widths(G)
#    print("Progressive Levels:", progressive_levels)
#    print("Regressive Levels:", regressive_levels)
#    print("Width at each Progressive Level:", progressive_widths)

    AD = calculate_activity_distribution(progressive_widths)
    LA = calculate_length_of_arcs(G, progressive_levels, regressive_levels, progressive_widths) # STILL WRONG!
    TF = calculate_topological_float(progressive_levels, regressive_levels, progressive_widths)

    if writeOutput:
        print("Network Topology Indicators:")
        print(f"\tSerial/Parallel Indicator (SP): {SP:.2f}")
        print(f"\tActivity Distribution Indicator (AD): {AD:.2f}")
        print(f"\tLength of Arcs Indicator (LA): {LA:.2f}")
        print(f"\tTopological Float Indicator (TF): {TF:.2f}")
    return SP, AD, LA, TF


def calculate_network_topology_indicators_two_phases(G, writeOutput = False):
    
    '''
    Note that this procedure only works correctly when the graph G is created WITHOUT the dummy nodes
    = the use of dummy nodes extends the network and biases the network topology indicators
    
    - Wrong approach: The graph G constructed in "calculate_critical_path" automatically adds dummy nodes, so this cannot be used
    - Correct approach (in two phases): 
        = First construct a non-dummy network in "construct_activity_network" with includeDummy=False
    - Correct approach (easy)
        = Run the procedure "calculate_network_topology_indicators" that first automatically creates a graph without dummies
    '''
    
#   I could call the following procedure:
#.  def construct_activity_network(activity_set, activity_dependencies, activity_names,
#                               debugInfo=False, visualize=False, includeDummy=False):
    
#    G = construct_activity_network

    SP = calculate_serial_parallel_indicator(G)

    progressive_levels, regressive_levels, progressive_widths = calculate_levels_and_widths(G)
#    print("Progressive Levels:", progressive_levels)
#    print("Regressive Levels:", regressive_levels)
#    print("Width at each Progressive Level:", progressive_widths)

    AD = calculate_activity_distribution(progressive_widths)
    LA = calculate_length_of_arcs(G, progressive_levels, regressive_levels, progressive_widths) # STILL WRONG!
    TF = calculate_topological_float(progressive_levels, regressive_levels, progressive_widths)

    if writeOutput:
        print("Network Topology Indicators:")
        print(f"\tSerial/Parallel Indicator (SP): {SP:.2f}")
        print(f"\tActivity Distribution Indicator (AD): {AD:.2f}")
        print(f"\tLength of Arcs Indicator (LA): {LA:.2f}")
        print(f"\tTopological Float Indicator (TF): {TF:.2f}")
    return SP, AD, LA, TF

def calculate_levels_and_widths(G):
    # Initialize dictionaries for progressive (forward) and regressive (backward) levels
    progressive_levels = {node: None for node in G.nodes()}
    regressive_levels = {node: None for node in G.nodes()}

    # Calculate progressive levels (forward levels)
    def calculate_progressive_level(node):
        if progressive_levels[node] is not None:
            return progressive_levels[node]
        
        if G.in_degree(node) == 0:  # If no predecessors, progressive level is 1
            progressive_levels[node] = 1
        else:
            # Otherwise, it is 1 + max of all the predecessors' progressive levels
            predecessors = list(G.predecessors(node))
            progressive_levels[node] = 1 + max(calculate_progressive_level(pred) for pred in predecessors)
        return progressive_levels[node]

    # Calculate regressive levels (backward levels)
    def calculate_regressive_level(node):
        if regressive_levels[node] is not None:
            return regressive_levels[node]
        
        if G.out_degree(node) == 0:  # If no successors, regressive level is len(progressive_widths)
            regressive_levels[node] = len(progressive_widths)
        else:
            # Otherwise, it is 1 + min of all the successors' regressive levels
            successors = list(G.successors(node))
            regressive_levels[node] = min(calculate_regressive_level(succ) - 1 for succ in successors)
        return regressive_levels[node]
    
    # Calculate the progressive level for all nodes
    for node in G.nodes():
        calculate_progressive_level(node)

    # Calculate width (number of activities at each progressive level)
    progressive_widths = {}
    for node in G.nodes():
        level = progressive_levels[node]
        if level not in progressive_widths:
            progressive_widths[level] = 0
        progressive_widths[level] += 1

    # Calculate the regressive level for all nodes (uses progressive_widths) 
    for node in G.nodes():
        calculate_regressive_level(node)      
        
    return progressive_levels, regressive_levels, progressive_widths


def calculate_serial_parallel_indicator(G):
    # Calculate the number of activities (n)
    n = len(G.nodes())
    
    # Find the longest path (m) (calculated as the number of edges, so + 1 to have the number of nodes)
    m = nx.dag_longest_path_length(G) + 1
    
#    print("m = ",m)
#    print("n = ",n)
    # Calculate the Serial/Parallel Indicator (SP)
    SP = (m - 1) / (n - 1)
    
    return SP

import numpy as np

def calculate_activity_distribution(progressive_widths):
    
    # m is the number of progressive levels
    m = len(progressive_widths)
    
    # n is the total number of activities, which is the sum of all widths
    n = sum(progressive_widths.values())

    # If m = 1 or n, return AD as 0
    if m == 1 or n == 1:
        return 0

    # Calculate average width
    average_width = np.mean(list(progressive_widths.values()))

    # Calculate the sum part of the formula
    AD_sum = 0
    for width in progressive_widths.values():
        AD_sum += abs(width - average_width)

    # Apply the formula for AD
    AD = AD_sum / (2 * (m - 1) * (average_width - 1))
    
    return AD

def calculate_length_of_arcs(graph, progressive_levels, regressive_levels, progressive_widths):

    # m is the number of progressive levels
    m = len(progressive_widths)
    
    # n is the total number of activities, which is the sum of all widths
    n = sum(progressive_widths.values())
    
#    print("progressive_widths = ",progressive_widths)
#    print("m = ",m)
#    print("n = ",n)
    
    # Calculate the width of level 1 (w1)
    w1 = progressive_widths[1]  
#    print("w1 = ", w1)
    
    # Calculate D: the sum of progressive_width_a * progressive_width_a+1 for progressive levels from 1 to m-1
    D = 0
    levels = list(progressive_widths.keys())  # Get the list of levels (keys)

    for i in range(len(levels) - 1):  # Summing up the product of widths of consecutive levels
        level_i = levels[i]
        level_i_plus_1 = levels[i + 1]
        D += progressive_widths[level_i] * progressive_widths[level_i_plus_1]

#    print("D =", D)

    # Calculate n'₁: the number of arrows (i,j) where PL_j = PL_i + 1 (i.e., short arcs with level difference = 1)
    n_prime_1 = sum(1 for (i, j) in graph.edges() if progressive_levels[j] - progressive_levels[i] == 1)
#    print("n_prime_1 = ",n_prime_1)
    
    # If D > n - w1, calculate LA based on the formula
    LA = 1
    if D > (n - w1):
        LA = (n_prime_1 - n + w1) / (D - n + w1)
        return LA
    
    # Otherwise, return LA = 1
    return 1

def calculate_topological_float(progressive_levels, regressive_levels, progressive_widths):

    # m is the number of progressive levels
    m = len(progressive_widths)
    
    # n is the total number of activities, which is the sum of all widths
    n = sum(progressive_widths.values())

    # Check if m = 1 or n = m, return 0 in this case
    if m == 1 or n == m:
        return 0
    
    print("progressive_levels = ",progressive_levels)
    print("regressive_levels = ",regressive_levels)    
    # Calculate the sum of the differences between regressive and progressive levels
    sum_diff = 0
    for activity in progressive_levels:
        prog_level = progressive_levels[activity]
        reg_level = regressive_levels.get(activity, float('inf'))  # Assuming regressive levels have been calculated
        
#        print("progressive_level = ",prog_level)
#        print("regressive_level = ",reg_level)
        sum_diff += (reg_level - prog_level)
    
    print("sum_diff = ",sum_diff)
    # Calculate the topological float (TF)
    TF = sum_diff / ((m - 1) * (n - m))
    
    return TF
 
############################################################    
###         Calculate the resource indicators            ###    
############################################################

def calculate_resource_scarcity_indicators(activity_schedule, activity_set, resource_requirements, resource_availability, writeOutput = False):

    #Resource demand:
    RU = calculate_resource_use(activity_set, resource_requirements)
    RF = calculate_resource_factor(activity_set, resource_requirements)

    # Resource availability:
    RC = calculate_resource_constrainedness(activity_set, resource_requirements, resource_availability)
    RS = calculate_resource_strength(activity_schedule, activity_set, resource_requirements, resource_availability)

    if writeOutput:
        print("Resource Scarcity Indicators:")
        print(f"\tResource Use (RU): {RU:.2f}")
        print(f"\tResource Factor (RF): {RF:.2f}")
        print("\tResource Constrainedness (RC):\n" + "\n".join(f"\t\t{r}: {v:.2f}" for r, v in RC.items()))
        print("\tResource Strength (RS):\n" + "\n".join(f"\t\t{r}: {v:.2f}" for r, v in RS.items()))
    return RU, RF, RC, RS


def calculate_resource_use(activity_set, resource_requirements):

    # Calculate resource use per activity
    resource_use_count = {}

    for activity, requirements in resource_requirements.items():
        count = sum(1 for r in requirements if r > 0)
        resource_use_count[activity] = count

    # Output result
#    print("Resource use count per activity:")
#    for activity, count in resource_use_count.items():
#        print(f"Activity {activity}: uses {count} resources")
        
    # Average resource use for activities with duration > 0 ---

    total_resource_use = 0
    count_activities = 0

    for activity_id, (duration, _) in activity_set.items():
        if duration > 0:
            resource_use = resource_use_count.get(activity_id, 0)
            total_resource_use += resource_use
            count_activities += 1

    average_resource_use = total_resource_use / count_activities if count_activities > 0 else 0

#    print(f"\nAverage resource use (for activities with duration > 0): {average_resource_use:.2f}")    
    return average_resource_use

def calculate_resource_factor(activity_set, resource_requirements):

    # Step 1: Filter valid activities (duration > 0)
    valid_activities = [act_id for act_id, (dur, _) in activity_set.items() if dur > 0]
    num_activities = len(valid_activities)
    num_resources = len(next(iter(resource_requirements.values())))  # assuming uniform length

    # Step 2: Count positive resource entries
    positive_entries = 0

    for act_id in valid_activities:
        requirements = resource_requirements[act_id]
        positive_entries += sum(1 for r in requirements if r > 0)

    # Step 3: Calculate resource factor
    denominator = num_activities * num_resources
    resource_factor = positive_entries / denominator if denominator > 0 else 0

#    print(f"Resource Factor: {resource_factor:.4f}")
    return resource_factor

def calculate_resource_constrainedness(activity_set, resource_requirements, resource_availability):
    # Step 1: Prepare
    valid_activities = [act_id for act_id, (dur, _) in activity_set.items() if dur > 0]
    num_resources = len(resource_availability)
    resource_names = list(resource_availability.keys())  # ['Resource 1', 'Resource 2', ...]

    # Initialize accumulators
    total_requirements = [0] * num_resources
    count_using_resource = [0] * num_resources

    # Step 2: Accumulate resource use over valid activities
    for act_id in valid_activities:
        requirements = resource_requirements[act_id]
        for i, req in enumerate(requirements):
            if req > 0:
                total_requirements[i] += req
                count_using_resource[i] += 1

    # Step 3: Compute constrainedness
    resource_constrainedness = {}

    for i, resource in enumerate(resource_names):
        if count_using_resource[i] > 0:
            avg_use = total_requirements[i] / count_using_resource[i]
        else:
            avg_use = 0  # Avoid division by zero

        availability = resource_availability[resource]
        constrainedness = avg_use / availability if availability > 0 else 0
        resource_constrainedness[resource] = constrainedness

    # Step 4: Output
#    print("\nResource Constrainedness:")
#    for resource, value in resource_constrainedness.items():
#        print(f"{resource}: {value:.4f}")
    # Compute average resource constrainedness
    average_constrainedness = (
        sum(resource_constrainedness.values()) / len(resource_constrainedness)
        if resource_constrainedness else 0
    )

#    print(f"\nAverage Resource Constrainedness: {average_constrainedness:.4f}")
    return resource_constrainedness #, average_constrainedness

def calculate_maximum_resource_use_for_a_schedule(activity_schedule, activity_set, resource_requirements, resource_availability):

    max_end = max(activity[0][4] for activity in activity_schedule.values())
    max_time=(math.ceil(max_end))#+1
   
    # Initialize resource usage over time
    resource_usage = {resource: np.zeros(max_time) for resource in resource_availability.keys()}

    # Iterate over the activities and add their resource usage
    for activity, schedule in activity_schedule.items():
        activity_name, duration, cost, start_time, end_time, slack = schedule[0]
               
        # Get resource requirements for the current activity
        if activity in resource_requirements:
            resource_reqs = resource_requirements[activity]  # We use the whole tuple here (not just the first option)

            # Add resource usage to the corresponding time intervals
            for t in range(int(start_time), int(end_time)):
                for i, resource in enumerate(resource_availability.keys()):
                    resource_usage[list(resource_availability.keys())[i]][t] += resource_reqs[i]
                    
    # Compute maximum usage per resource over time
    max_resource_usage = {}

    for resource, usage_over_time in resource_usage.items():
        max_usage = np.max(usage_over_time)
        max_resource_usage[resource] = max_usage

    # Output result
#    print("\nMaximum Resource Usage Over Time:")
#    for resource, usage in max_resource_usage.items():
#        print(f"{resource}: {usage}")
    return max_resource_usage    

def calculate_resource_strength(activity_schedule, activity_set, resource_requirements, resource_availability):

    # Calculate the maximum resource usage for the CPM schedule (activity_schedule)
    req_max = calculate_maximum_resource_use_for_a_schedule(activity_schedule, activity_set, resource_requirements, resource_availability)

    resource_strength = {}

    # Transpose resource requirements to process by resource index
    for i, resource in enumerate(resource_availability):
        # Get max requirement for this resource across valid activities
        max_req = max(
            (resource_requirements[act_id][i]
             for act_id in activity_set
             if activity_set[act_id][0] > 0),
            default=0
        )

        availability = resource_availability[resource]
        max_possible = req_max.get(resource, max_req)  # You can default to max_req if req_max not given

        # Avoid division by zero
        denominator = max_possible - max_req
        strength = (availability - max_req) / denominator if denominator != 0 else 1.0  # or float('inf') if you prefer

        resource_strength[resource] = strength

    # Output
#    print("\nResource Strength:")
#    for resource, value in resource_strength.items():
#        print(f"{resource}: {value:.4f}")    

    # Compute average resource strength
    average_resource_strength = (
        sum(resource_strength.values()) / len(resource_strength)
        if resource_strength else 0
    )

#    print(f"\nAverage Resource Strength: {average_resource_strength:.4f}")
    return resource_strength #, average_resource_strength

