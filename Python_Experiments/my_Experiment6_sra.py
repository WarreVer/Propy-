#############################################################################
### Example experiment 6: Schedule Risk Analysis (SRA) without resources
###
###    Note: This is the schedule risk analysis for projects WITHOUT resources
###          = The experiment uses the CPM schedule as a point of reference
###
###   The experiment replicates the Monte Carlo simulation runs of the following book:
###      - Title: The Data-Driven Project Manager: A Statistical Battle Against Project Obstacles
###      - Author: Mario Vanhoucke
###      - Year: 2018
###      - Publisher: Apress Berkeley, CA
###      - Source: https://doi.org/10.1007/978-1-4842-3498-3
###
###   The project progress is simulated manually using the data of 10 simulation runs from the book and the output

###      - The project is an artificial tennis stadium construction project managed by Emily Reed and her team (that is the story of the book)
###      - Important: 
###         ° The baseline schedule is a critical path schedule (no resources are taken into account)
###          (Note that inn Experiment 7, the CPM schedule will be replaced by a resource-feasible schedule)
###      - Not all data could be 100% exactly replicated due to the randomness of the simulated data
###         ° Activity network: Figure 3.1
###         ° The risk classes are described in Figures 3.2, 3.4, 3.5, 3.6, and 3.9, 
###           and Table 3.1 shows the classes that are used (with small changes) in this experiment
###         ° Description of Monte Carlo simulations for risk analysis: Figure 3.8
###         ° Sensitivity metrics: 
###           * Three sensitivity metrics (CI, SI and SSI) are explained in Chapter 3
###           * The use of these sensitivity metrics for control efficiency is explained in Figure 6.5
###
###    Summary details:
###      - The code generates the following sensitivity metrics (identical to Experiment 5):
###         ° Criticality Index (CI): Measures the probability of an activity lying on the critical path
###         ° Sensitivity Index (SI): Indicates how an activity’s duration affects the project’s total duration
###         ° Schedule Sensitivity Index (SSI): Combines CI and SI to assess an activity’s overall risk to the schedule
###         ° Cruciality Index (CRI(t)): Measures the correlation between activity duration variability and project duration variability
###
###    Download the summary file "Summary_Experiment_6.pdf" or print on screen
###
#############################################################################

print_summary_file(Infofolder, 6)

##############################################################################
### Step 1. Get the project data and construct a CPM schedule
##############################################################################

# Read the project from DDPM
activity_names, activity_set, predecessors_list, _, activity_risk_classes = get_project_data_ddpm_2018()

add_dummy_nodes_to_project_data(activity_set,activity_names,prl=predecessors_list)

# Construct the network dependency matrix (with predecessors_list as input)
activity_dependencies = create_activity_network_dependencies(predecessors_list,{},activity_names, debugInfo = False)

# Construct the CPM schedule
graph, PD, BAC, cpm_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, False)
print('Planned duration (PD) = ', PD)
print('Budget at completion (BAC) = ', BAC)

# Visualize the network graph (created in the "calculate_critical_path" function)
visualize_network(graph, activity_names,showDummy = True)

# Draw a Gantt chart
show_gantt_chart(cpm_schedule)  

##############################################################################
### Step 2. Define activity uncertainty (on the durations) (risk classes)
###      Note: There is no need to define them, since the procedure "get_project_data_ddpm_2018" already did
###      But: The code below shows how you can change them (manually, or automatically randomly generated)
##############################################################################

# These are the risk classes from "get_project_data_ddpm_2018". 
# They are not completely in line with Table 3.1 of the book (range is not the same), only approximately
activity_risk_classes = {
    "No Risk": ["DS", "DE", "B", "E", "I"],
    "Variation": ["H", "M", "P"],
    "Foreseen Uncertainty": ["A", "L"],
    "Unforeseen Uncertainty": ["C", "D", "F", "G", "J", "K", "N", "O"]
}

# The risk classes can be generated randomly
#generate_random_activity_risk_classes(activity_names)

##############################################################################
### Step 3. Run a Monte Carlo simulation 
###         (don't put the number of runs too high, since it can take some time)
##############################################################################

#print("Activity set = ", activity_set)

print("activity_risk_classes = ", activity_risk_classes)
nrRuns = 1000
simulated_schedules = perform_monte_carlo_simulation(
    nrRuns, activity_names, activity_dependencies, cpm_schedule,  
    "LOW", "CLASS", "CPM", 
    activity_risk_classes, resource_requirements=None, resource_availability=None, 
    debugInfo=True)

#print("simulated_schedules = ", simulated_schedules)
# Display the first few rows but full column content
#with pd.option_context('display.max_columns', None, 'display.max_colwidth', None):
#    print(simulated_schedules.head())


##############################################################################
### Step 4. Simulation output
###         - Simulated activity durations and activity costs (graphs)
###         - Simulated project duration and cost
###         - Sensitivity metrics
###             * Time sensitivity    
###               ° Criticality index CI
###               ° Significance index SI
###               ° Schedule sensitivity index SSI
###               ° Cruciality index CRI(t) 
###             * Cost sensitivity    
###               ° Cruciality index CRI(c) 
##############################################################################

# Show the graphs for activity durations and costs
#visualize_simulated_activity_data(simulated_schedules,"T")
#visualize_simulated_activity_data(simulated_schedules,"C") ### SOMETHING IS NOT WORKING HERE!!

# Show the graphs for the total project duration and cost
visualize_simulated_project_data(simulated_schedules,legend_size = 14)

### Step 4. Calculate the sensitivity metrics
CI, SI, SSI, CRIt, CRIc = calculate_sensitivity_metrics(simulated_schedules, False)

#print("CI = ", CI)
#print("SI = ", SI)
#print("SSI = ", SSI)
#print("CRIt = ", CRIt)
#print("CRIc = ", CRIc)

# Show the sensitivity graphs
create_horizontal_sensitivity_graph(CI,"CI")
create_horizontal_sensitivity_graph(SI,"SI")
create_horizontal_sensitivity_graph(SSI,"SSI")
create_horizontal_sensitivity_graph(CRIt,"CRI(t)")
create_horizontal_sensitivity_graph(CRIc,"CRI(c)")

