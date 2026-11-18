#############################################################################
### Example experiment 1: Network Analysis and Critical Path Method 
### = Learn which activities are critical and how delays impact the project
###
###   The experiment uses the project data of the book mentioned below (reference 1), as follows:
###      - The network analysis includes:
###        ° The Design Structure Matrix (DSM): Table 2.1 of the book 
###        ° The project network: Figure 3.1
###        ° Network topology indicators
###          * Serial/Parallel (SP) indicator
###          * Activity Distribution (AD) indicator
###          * Length of Arcs (LA) indicator
###          * Topological Float (TF) indicator
###      - The CPM scheduling includes:
###        ° Gantt chart: Figure 5.1
###        ° Planned Value line: Figure 5.1
###        ° The regularity index: See reference 2
###
###   Note:
###      - The procedure "create_activity_network_dependencies" can creates a network, as follows 
###             - In most project data, either a predecessors_list or a successors_list for the project
###             - Note that in this experiment, both are available, but for most other project data files 
###               (in all other experiments), only one list is available, and the other will be then created automatically 
### 
###   References:
###      1. Book
###      - Title: The Data-Driven Project Manager: A Statistical Battle Against Project Obstacles
###      - Author: Mario Vanhoucke
###      - Year: 2018
###      - Publisher: Apress Berkeley, CA
###      - Source: https://doi.org/10.1007/978-1-4842-3498-3
###
###      2. Paper
###      - Title: Project regularity: Development and evaluation of a new project characteristic
###      - Author: Jordy Batselier and Mario Vanhoucke
###      - Year: 2017
###      - Publisher: Journal of Systems Science and Systems Engineering, 26(1), 100–120
###      - Source: https://doi.org/10.1007/s11518-016-5312-6
###
###    Download the summary file "Summary_Experiment_1.pdf" or print on screen
###
#############################################################################

print_summary_file(Infofolder, 1)

#############################################################################
### Step 1. Read the project data of the book "The data-driven project manager"   
#############################################################################

# Choose which list (successors or predecessors) you want to use 
#        (here both are available, but that is not always the case)
read_file_with_successors = True

# Read the project data
activity_names, activity_set, predecessors_list, successors_list, _ = get_project_data_ddpm_2018()
add_dummy_nodes_to_project_data(activity_set, activity_names, prl=predecessors_list, sul=successors_list)
#print("activity_set = ", activity_set)
#print("activity_names = ", activity_names) 
#print("predecessors_list = ", predecessors_list)
#print("successors_list = ", successors_list)
   
#############################################################################
### Step 2. Construct the design structure matrix                
###         (based on either activity predecessors or successors)
#############################################################################

if read_file_with_successors:
    # Construct the network dependency matrix (assuming only the successors_list was read by "get_project_data_ddpm_2018")
    print("Analyse the project data assuming only the successors are given for each activity")
    activity_dependencies = create_activity_network_dependencies({},successors_list,activity_names, debugInfo = False)
else:
    # Construct the network dependency matrix (assuming only the predecessors_list was read by "get_project_data_ddpm_2018")
    print("Analyse the project data assuming only the predecessors are given for each activity")
    activity_dependencies = create_activity_network_dependencies(predecessors_list,{},activity_names, debugInfo = False)

show_design_structure_matrix(activity_dependencies, showDummy = True)
show_design_structure_matrix(activity_dependencies,xlabel_size=16,ylabel_size=16,xtick_size=15,title_size=12,showDummy = False)

#############################################################################
### Step 3. Construct the project network (no critical path will be shown)
#############################################################################

graph = construct_activity_network(activity_set, activity_dependencies, activity_names,
                                              debugInfo=False, visualize=False, includeDummy=True)
visualize_network(graph, activity_names, xtick_size=20, ytick_size=20, showDummy=False)

#############################################################################
### Step 4. Calculate the network topology indicators
###    Warning: To get the correct values of the network topology indicators, 
###             the parameter "graph" should have been constructed with showDummy=False 
###             (or it can be automatically generated without dummies)      
#############################################################################

# Calculate the network indicators with a graph with dummies --> wrong values
print("Run 1 using a graph with dummies (ERROR): ")
graph = construct_activity_network(activity_set, activity_dependencies, activity_names,includeDummy=True)
SP, AD, LA, TF = calculate_network_topology_indicators_two_phases(graph, writeOutput = True)

# Calculate the network indicators with a graph without dummies --> correct values
print("Run 2 using a graph without dummies (CORRECT): ")
graph = construct_activity_network(activity_set, activity_dependencies, activity_names,includeDummy=False)
SP, AD, LA, TF = calculate_network_topology_indicators_two_phases(construct_activity_network(activity_set,activity_dependencies,activity_names,includeDummy=False), writeOutput = True)

# Calculate the network indicators with an automatically calculated graph without dummies --> correct values
print("Run 3 with an automatically created graph without dummies (CORRECT AND EASY): ")
SP, AD, LA, TF = calculate_network_topology_indicators(activity_set, activity_dependencies, activity_names, writeOutput = True)

# Critical Path Analysis (not necessary, just for illustrative purposes)
graph, PD, BAC, cpm_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, False)

## Visualize the network with/without dummy nodes and critical path highlighted)
visualize_network(graph, activity_names,showDummy = True, showCP = False)
visualize_network(graph, activity_names,showDummy = False)

#############################################################################
### Step 5. Construct a CPM schedule (earliest start schedule) 
#############################################################################

# Construct the CPM schedule
graph, PD, BAC, planned_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, False)
print("Critical Path Schedule:")
print(f"\tPlanned Duration (PD): {PD:.0f} weeks")
print(f"\tBudget at Completion (BAC): {BAC:.2f} EURO")

# Visualize the network as a graph (created in the "calculate_critical_path" function)
visualize_network(graph, activity_names,showDummy = True)
visualize_network(graph, activity_names,showDummy = False)

# Visualize the CPM schedule as a Gantt chart
show_gantt_chart(planned_schedule, xlabel_size = 20, ylabel_size = 20, xtick_size = 15, ytick_size = 15, showCost = False)
#show_gantt_chart(planned_schedule, showName = False, showDummy = True)

# Visualize the CPM schedule as the planned value line (PV) (interesting for Earned Value Management)
PV, _, _, _, AT, _, _, _, _, _, _ = calculate_evm_key_metrics(planned_schedule, planned_schedule)

#plot_selected_EVM_metrics(AT, show_values = False, PV=PV)
plot_selected_EVM_metrics(AT, show_values = False, default_value=None, default_title=None,
                              xlabel_size=20, ylabel_size=20,
                              xtick_size = 15, ytick_size = 15, 
                              legend_size=0,
                              title_size=20, 
                              thous_sep=True,
                              PV=PV)


# Calculate the regularity index RI
RI = calculate_regularity_index(PD, BAC, PV, AT)
print("Planned Value Indicator:")
print(f"\tRegularity Index (RI): {RI:.2f}")