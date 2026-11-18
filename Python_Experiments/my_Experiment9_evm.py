#############################################################################
### Example experiment 9: Earned Value Management (EVM)
### = The project network structure has a major impact on the accuracy of EVM predictions
###
###   The experiment replicates all project data graphs written in the following book:
###      - Title: Integrated project management and control: First comes the theory, then the practice
###      - Author: Mario Vanhoucke
###      - Year: 2014
###      - Publisher: Springer
###      - Source: https://doi.org/10.1007/978-3-319-04331-9
###
###   Note: 
###      - The network structure is measured by the serial/parallel indicator SP 
###      - The SP indicator ranges from completely parallel projects (SP = 0) to completely serial (SP = 1)
###      - The experiment is illustrated on three projects with a different network structure:
###         1. Cost information system: Parallel project (SP = 0.25)
###         2. Patient transport system: In-between (SP = 0.50)
###         3. Old carriage house renovation: Serial project (SP = 0.75)
###
###   Progress data: 
###      - The project progress can be generated in two different ways (parameter "generate_progress_data"):
###        * "MANUAL" : manually created data from the book mentioned above 
###        * "MCS"    : using a single Monte Carlo simulation run
###                   (in this case, the generated graphs differ from the original book graphs (depending on the simulation parameters))
###
###   The project progress is set to MANUAL using the data from the book and the generated graphs
###   correspond to the following figures/table:
###      - Activity networks: Figures 1.1, 1.3 and 1.5
###      - Gantt charts: Figures 1.2, 1.4 and 1.6
###      - Project data (planned and progress): Tables 1.2, 1.3 and 1.4
###      - EVM key metrics 
###            ° PV, AC and EV: Figures 2.3, 2.4 and 2.5
###            ° ES: Figure 3.4
###      - EVM performance metrics: 
###            ° SPI and CPI: Figure 2.6
###            ° SPI(t): Figure 3.5
###        --> summary reports of Figures 2.7, 2.8 and 2.9
###        --> summary reports of Figures 4.4, 4.5 and 4.6
###      - EVM forecasting metrics: 
###            ° Time forecasting: Table 5.1 and Figure 5.2
###            ° Cost forecasting: Table 5.2 and Figure 5.3
###      - EVM forecasting accuracy: 
###            ° Time accuracy: Table 5.3
###            ° Cost accuracy: Table 5.4
###        --> Summary reports of Figures 5.4, 5.5 and 5.6
###
###    Summary details:
###      - Calculated EVM metrics: 
###         * Key metrics (inputs): 
###           - Planned Value (PV)
###           - Actual Cost (AC)
###           - Earned Value (EV)
###           - Earned Schedule (ES)
###         * Performance metrics:
###           - Schedule Performance Index (SPI) (based on EV)
###           - Schedule Performance Index (SPI(t)) (based on ES)
###           - Cost Performance Index (CPI)
###         * Predictions:
###           - Estimate at completion for time (EAC(t)): 9 versions
###           - Estimate at completion for cost (EAC): 8 versions
###
###    Other interesting reference for the SP indicator:
###      - Vanhoucke, M., Coelho, J., Debels, D., Maenhout, B. and Tavares, L.V.
###        "An evaluation of the adequacy of project network generators with systematically sampled networks"
###        European Journal of Operational Research, 187(2), 511–524, 2018 (doi:10.1016/j.ejor.2007.03.032).
###
###    Download the summary file "Summary_Experiment_9.pdf" or print on screen
###
#############################################################################

# Choose the project (1, 2 or 3)
projectID = 2

# Select the progress data generation (existing data (= MANUAL) or single Monte Carlo run (= MCS))
generate_progress_data = "MANUAL"
#generate_progress_data = "MCS"

print_summary_file(Infofolder, 9)

#############################################################################
### Step 1. Construct a CPM schedule (earliest start schedule)            ###
#############################################################################

activity_names, activity_set, predecessors_list = get_project_data_ipmc_2014(projectID)
add_dummy_nodes_to_project_data(activity_set,activity_names,prl=predecessors_list)

activity_dependencies = create_activity_network_dependencies(predecessors_list,{},activity_names, debugInfo = False)

# Construct the CPM schedule
graph, PD, BAC, planned_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, False)
print('Planned duration (PD) = ', PD)
print('Budget at completion (BAC) = ', BAC)

graph_nodummies = construct_activity_network(activity_set, activity_dependencies, activity_names, includeDummy=False)
SP = calculate_serial_parallel_indicator(graph_nodummies)
print(f"Serial/Parallel Indicator (SP): {SP:.2f}")

# Visualize the network graph (created in the "calculate_critical_path" function) and Gantt chart
visualize_network(graph, activity_names,showDummy = False)
show_gantt_chart(planned_schedule, showCost = True, title_size = 0, showName = False)

# Calculate the regularity index RI (based on the PV line)
PV, _, _, _, AT, _, _, _, _, _, _ = calculate_evm_key_metrics(planned_schedule, planned_schedule)
RI = calculate_regularity_index(PD, BAC, PV, AT)
print(f"Regularity Index (RI): {RI:.2f}")

##############################################################################
### Step 2. Construct the real schedule (i.e. the project is finished)
###         = the real activity durations differ from the planned durations
###         = the cost is linearly related to the real duration 
###  - generate_progress_data == "MANUAL": Use the progress data from the book
###  - generate_progress_data == "MCS": Use risk classes and simulate one real-life execution
###                              (nrRuns should be 1 since it is a simulation of one execution run to get EVM data)
##############################################################################

if generate_progress_data == "MANUAL":

    # Set the real durations for the activities (0 for dummy start and end) and create a new real_activity_set with new durations and costs
    if projectID == 1:
        real_duration = {'DS': 0, 'A1': 1, 'A2': 3, 'A3': 3, 'A4': 3, 'A5': 5, 'A6': 3, 'A7': 4, 'A8': 2, 'A9': 1, 
                         'A10': 1, 'A11': 3, 'A12': 1, 'A13': 2, 'A14': 1, 'A15': 3, 'A16': 2, 'A17': 1, 'DE': 0}
    elif projectID == 2:
        real_duration = {'DS': 0, 'A1': 1, 'A2': 2, 'A3': 4, 'A4': 1, 'A5': 4, 'A6': 2, 'A7': 3, 'A8': 1, 'A9': 2, 
                         'A10': 5, 'A11': 4, 'A12': 3, 'A13': 5, 'A14': 5, 'A15': 3, 'A16': 5, 'A17': 2, 'DE': 0}
    elif projectID == 3:
        real_duration = {'DS': 0, 'A1': 2, 'A2': 3, 'A3': 5, 'A4': 2, 'A5': 6, 'A6': 1, 'A7': 2, 'A8': 1, 'A9': 1, 
                         'A10': 1, 'A11': 2, 'A12': 2, 'A13': 2, 'A14': 1, 'A15': 2, 'A16': 1, 'A17': 1, 'DE': 0}
    else:
        print("No valid project ID")
    
    real_activity_set = {
        activity: (real_duration.get(activity, 0),
                  (cost / duration) * real_duration.get(activity, 0) if duration > 0 else 0
        )
        for activity, (duration, cost) in activity_set.items()}

    # Construct the real execution schedule of the project (and real project duration and cost)
    graph, real_duration, real_cost, real_schedule = calculate_critical_path(real_activity_set, activity_dependencies, activity_names, False)

if generate_progress_data == "MCS":
    
    # Assign activities to risk classes (randomly for illustrative purposes)
    activity_risk_classes = generate_random_activity_risk_classes(activity_names)

    # Generate exactly one execution run
    nrRuns = 1 
    list_simulated_schedules_df = perform_monte_carlo_simulation(
        nrRuns, activity_names, activity_dependencies, planned_schedule,  
        "LOW", "CLASS", "CPM", 
        activity_risk_classes, resource_requirements=None, resource_availability=None, 
        debugInfo=True)

    # Get the real schedule (and extract real project duration and cost)
    real_schedule = list_simulated_schedules_df.at[0, 'Simulated Schedules']  # Extract dictionary from the first (and only) row
    real_duration = list_simulated_schedules_df['Total Duration'][0]
    real_cost = list_simulated_schedules_df['Total Cost'][0]

# Abbreviate to RD (real duration) and RAC (real (cost) at completion) 
RD = real_duration
RAC = real_cost
print("Real project duration (RD) = ", real_duration)
print("Real project cost (RC) = ", real_cost)
#show_gantt_chart(real_schedule)

# Print the start times of the planned and real schedule (WHYYYYYYYY?????????)
start_times = {activity: details[0][3] for activity, details in planned_schedule.items()}
rounded_start_times = [round(time, 1) for time in start_times.values()]
print("Planned schedule = ", rounded_start_times)

start_times = {activity: details[0][3] for activity, details in real_schedule.items()}
rounded_start_times = [round(time, 1) for time in start_times.values()]
print("Real schedule = ", rounded_start_times)

# Show the planned value line
PV, _, _, _, AT, _, _, _, _, _, _ = calculate_evm_key_metrics(planned_schedule, planned_schedule)
plot_selected_EVM_metrics(AT, show_values = False, PV=PV, legend_size = 0, thous_sep=True)


#############################################################################
### Step 3. Calculate the Earned Value Management metrics                 ###
###    (as shown in Figures x.x and x.x of the book "IJFKDLJJKJFLDS Time")   ###
#############################################################################

PV, AC, EV, ES, AT, SV, SVt, CV, SPI, SPIt, CPI = calculate_evm_key_metrics(planned_schedule, real_schedule)

plot_selected_EVM_metrics(AT, show_values = False, PV=PV, EV=EV, AC=AC, thous_sep=True)
plot_selected_EVM_metrics(AT, ES=ES, AT=AT)

plot_selected_EVM_metrics(AT, default_value = 0, SV=SV, CV=CV)
plot_selected_EVM_metrics(AT, SVt=SVt)

plot_selected_EVM_metrics(AT, SPI=SPI, CPI=CPI, ylabel_size = 0)
plot_selected_EVM_metrics(AT, default_value = 1, SPI=SPI, SPIt=SPIt, ylabel_size = 0)

#############################################################################
### Step 4. Predict the final project duration and cost at each period    ###
###    - 9 time forecasting metrics (table 5.1 of the book)
###        * Planned value forecasting method: with PF = 1, xxxx
### xxxxx
###, earned duration, earned schedule ###
###    - 8 forecasting metrics (table 5.2 of the book)
#############################################################################

(EACtPV1, EACtPV2, EACtPV3, EACtED1, EACtED2, EACtED3, EACtES1, EACtES2, EACtES3, 
 EAC1, EAC2, EAC3, EAC4, EAC5, EAC6, EAC7, EAC8) = calculate_evm_predictions(
    planned_schedule, PV, AC, EV, ES, AT, SV, SVt, CV, SPI, SPIt, CPI)

# Time predictions according to the performance factor (PF)
plot_selected_EVM_metrics(AT, default_value = RD, default_title = "Time predictions (future according to plan)", EACtPV1=EACtPV1, EACtED1=EACtED1, EACtES1=EACtES1, ylabel_size = 0, legend_size = 0)
plot_selected_EVM_metrics(AT, default_value = RD, default_title = "Time predictions (future according to current performance)", EACtPV2=EACtPV2, EACtED2=EACtED2, EACtES2=EACtES2, ylabel_size = 0, legend_size = 0)
plot_selected_EVM_metrics(AT, default_value = RD, default_title = "Time predictions (future according to current time/cost performance)", EACtPV3=EACtPV3, EACtED3=EACtED3, EACtES3=EACtES3, ylabel_size = 0, legend_size = 0)

# Cost predictions according to the performance factor (PF)
plot_selected_EVM_metrics(AT, default_value = RAC, default_title = "Cost predictions (future according to plan)", EAC1=EAC1)
plot_selected_EVM_metrics(AT, default_value = RAC, default_title = "Cost predictions (future according to current performance)", EAC2=EAC2, EAC3=EAC3, EAC4=EAC4)
plot_selected_EVM_metrics(AT, default_value = RAC, default_title = "Cost predictions (future according to current time/cost performance)", EAC5=EAC5, EAC6=EAC6)
plot_selected_EVM_metrics(AT, default_value = RAC, default_title = "Cost predictions (future according to weighted current time/cost performance)", EAC7=EAC7, EAC8=EAC8)


# Accuracy of the time forecasts
print("\nTime accuracy values (9 methods)")
prediction_values = [EACtPV1, EACtPV2, EACtPV3, EACtED1, EACtED2, EACtED3, EACtES1, EACtES2, EACtES3]
method_names = ["EACtPV1", "EACtPV2", "EACtPV3", "EACtED1", "EACtED2", "EACtED3", "EACtES1", "EACtES2", "EACtES3"]
RealValue = RD
MAPE, MPE = get_all_forecasting_accuracy(RealValue, prediction_values, method_names, debugInfo = True)

# Accuracy of the cost forecasts
print("\nCost accuracy values (8 methods)")
prediction_values = [EAC1, EAC2, EAC3, EAC4, EAC5, EAC6, EAC7, EAC8]
method_names = ["EAC1", "EAC2", "EAC3", "EAC4", "EAC5", "EAC6", "EAC7", "EAC8"]
RealValue = RAC
MAPE, MPE = get_all_forecasting_accuracy(RealValue, prediction_values, method_names, debugInfo = True)

