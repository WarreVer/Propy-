#############################################################################
### Example experiment 5: Schedule Risk Analysis (SRA) with manual simulations 
### = Simulate artifical project progress starting with a CPM schedule and 10 predefined runs
###
###   The experiment replicates project data graphs written in the following book:
###      - Title: Integrated Project Management Sourcebook: A Technical Guide to Project Scheduling, Risk and Control
###      - Author: Mario Vanhoucke
###      - Year: 2016
###      - Publisher: Springer
###      - Source: https://doi.org/10.1007/978-3-319-27373-0
###
###   The project progress is simulated manually using the data of 10 simulation runs from the book and the output
###   correspond to the following figures/table:
###      - Activity network: Figure 7.8
###      - 10 simulation runs: Table 7.1
###      - Criticality Index (CI): Figure 7.9
###      - Cruciality Index (CRI(t)): Figure 7.10
###      - Sensitivity Index (SI): Figure 7.13
###      - Schedule Sensitivity Index (SSI): Figure 7.14
###
###    Summary details:
###      - The code generates the following sensitivity metrics:
###         ° Criticality Index (CI): Measures the probability of an activity lying on the critical path
###         ° Sensitivity Index (SI): Indicates how an activity’s duration affects the project’s total duration
###         ° Schedule Sensitivity Index (SSI): Combines CI and SI to assess an activity’s overall risk to the schedule
###         ° Cruciality Index (CRI(t)): Measures the correlation between activity duration variability and project duration variability
###
###    Download the summary file "Summary_Experiment_5.pdf" or print on screen
###
#############################################################################

import pandas as pd

print_summary_file(Infofolder, 5)

##############################################################################
### Step 1. Read the project data and construct a CPM network (reference point)
##############################################################################

# Read the project of Figure 7.8
activity_names, activity_set, predecessors_list = get_project_data_pmkc_2016()

# Add dummies since the project from get_project_data_pmkc_2016 doesn't have any
add_dummy_nodes_to_project_data(activity_set,activity_names,prl=predecessors_list)

# Construct the network dependency matrix (with predecessors_list as input)
activity_dependencies = create_activity_network_dependencies(predecessors_list,{},activity_names, debugInfo = False)

# Construct the CPM schedule
graph, PD, BAC, planned_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, False)
print("Baseline schedule:")
print('  - Planned duration (PD) = ', PD)
#print('  - Budget at completion (BAC) = ', BAC)

# Visualize the network graph (created in the "calculate_critical_path" function)
visualize_network(graph, activity_names,showDummy = True, ProgLevelHierarchy = False)

# Draw a Gantt chart
show_gantt_chart(planned_schedule)  


##############################################################################
### Step 2. Define activity uncertainty (on the durations)
###         = manual simulation using the values of Table 7.1
###         (the first and last value are 0 for the dummy start and end nodes)
##############################################################################

real_durations = [
    {'DS': 0, 'A': 4,  'B': 12, 'C': 1,  'D': 4,  'E': 5,  'F': 4,  'G': 7,  'H': 8,  'DE': 0}, # Run 1
    {'DS': 0, 'A': 22, 'B': 23, 'C': 14, 'D': 5,  'E': 28, 'F': 26, 'G': 5,  'H': 29, 'DE': 0}, # Run 2
    {'DS': 0, 'A': 25, 'B': 38, 'C': 12, 'D': 15, 'E': 24, 'F': 20, 'G': 13, 'H': 22, 'DE': 0}, # Run 3
    {'DS': 0, 'A': 25, 'B': 25, 'C': 15, 'D': 13, 'E': 25, 'F': 25, 'G': 13, 'H': 10, 'DE': 0}, # Run 4
    {'DS': 0, 'A': 21, 'B': 42, 'C': 12, 'D': 7,  'E': 30, 'F': 21, 'G': 14, 'H': 23, 'DE': 0}, # Run 5
    {'DS': 0, 'A': 28, 'B': 44, 'C': 7,  'D': 9,  'E': 15, 'F': 20, 'G': 10, 'H': 22, 'DE': 0}, # Run 6
    {'DS': 0, 'A': 19, 'B': 21, 'C': 14, 'D': 13, 'E': 23, 'F': 24, 'G': 14, 'H': 28, 'DE': 0}, # Run 7
    {'DS': 0, 'A': 12, 'B': 36, 'C': 14, 'D': 9,  'E': 19, 'F': 17, 'G': 7,  'H': 24, 'DE': 0}, # Run 8
    {'DS': 0, 'A': 28, 'B': 35, 'C': 7,  'D': 12, 'E': 28, 'F': 27, 'G': 13, 'H': 28, 'DE': 0}, # Run 9
    {'DS': 0, 'A': 27, 'B': 44, 'C': 6,  'D': 5,  'E': 30, 'F': 10, 'G': 11, 'H': 28, 'DE': 0}  # Run 10
]

#real_cost = [(0, 0, 0, 1, 4, 5, 4, 7, 8)] # Same for all runs, costs are irrelevant in this experiment

##############################################################################
### Step 3. Manual simulation using 10 runs 
###         = This manual simulation is only for illustrative purposes
### Note: A real simulation can be done with "perform_monte_carlo_simulation"
###       (= This is shown in Example Experiments x and x)
##############################################################################

sampled_activity_set = {}
list_simulated_schedules = []

print("*** Run 10 Monte Carlo simulations (each time changing the critical path) ***")
for run_index, rd in enumerate(real_durations, start=1):

    # Create sampled_activity_set for this run
    sampled_activity_set = {
        activity: (rd[activity], 0)  # duration from rd, cost = 0 (irrelevant for this experiment)
        for activity in activity_names.keys()
    }

    # Simulate the new CPM schedule (with real durations and costs)
    _, total_duration, total_cost, simulated_schedule = calculate_critical_path(sampled_activity_set, activity_dependencies, activity_names, False)
    
    # Draw each simulated Gantt chart
    show_gantt_chart(simulated_schedule, showCP=True, showName=True,
                                    xlabel_size=12, ylabel_size=12,
                                    xtick_size=12, ytick_size=12,
                                    title_size=0)
    print("Total Simulated Project Duration = ", total_duration)

    # Add the total project duration, total project cost and simulated schedule to the list_simulated_schedules
    list_simulated_schedules.append((total_duration, total_cost, simulated_schedule))


    
# Put the list_simulated_schedules into a dataframe (necessary for the sensitity calculations)
simulated_schedules = pd.DataFrame(list_simulated_schedules, columns=['Total Duration', 'Total Cost', 'Simulated Schedules'])

#print("simulated_schedules = ", simulated_schedules)

# Print the simulated project duration values
print("*** The simulated project data ***")
print(f"  - Average duration = {simulated_schedules['Total Duration'].mean():.2f}")
print(f"  - Standard deviation = {simulated_schedules['Total Duration'].std():.2f}")
print(f"  - Minimum duration = {simulated_schedules['Total Duration'].min():.2f}")
print(f"  - Maximum duration = {simulated_schedules['Total Duration'].max():.2f}")

##############################################################################
### Step 4. Calculate and display the sensitivity metric values (time only)
###         - Criticality index CI
###         - Significance index SI
###         - Schedule sensitivity index SSI
###         - Cruciality index CRI(t) (I added (t) since can also be used for cost)
##############################################################################

# Calculate the sensitivity metrics (time sensitivity only)
CI, SI, SSI, CRIt, CRIc = calculate_sensitivity_metrics(simulated_schedules, False)

# Show the values of the sensitivity metrics as percentages (with 0 decimal places)
sensitivity_data = {
    'CI': CI,
    'SI': SI,
    'SSI': SSI,
    'CRIt': CRIt
}
df = pd.DataFrame(sensitivity_data)
df = df.applymap(lambda x: f'{x * 100:.0f}%')
print("*** The time-based sensitivity metrics for each activity (values) ***")
print(df)

# Show the values of the sensitivity metrics as graphs
print("*** The time-based sensitivity metrics for each activity (in graphs) ***")
create_horizontal_sensitivity_graph(CI,"Criticality Index (CI)", xlabel_size=0, ylabel_size=0) #Figure 7.9
create_horizontal_sensitivity_graph(SI,"Significance Index (SI)", xlabel_size=0, ylabel_size=0) #Figure 7.14
create_horizontal_sensitivity_graph(SSI,"Schedule Sensitivity Index (SSI)", xlabel_size=0, ylabel_size=0) #Figure 7.13
create_horizontal_sensitivity_graph(CRIt,"Cruciality Index (CRI(t))", xlabel_size=0, ylabel_size=0) #Figure 7.10
#create_horizontal_sensitivity_graph(CRIc,"CRI(c)")
