#############################################################################
### Example experiment 2: Time/cost trade-off optimisation in project scheduling
### = Solve the discrete time/cost trade-off problem (DTCTP) with integer programing
###
###   The experiment makes use of projects with multiple activity duration/cost combinations. 
###   The DTCTP is NP hard and extends the basic critical path method with questions, such as: 
###         * How to minimise the duration of a project for a given budget constraint?
###         * How to minimise the cost of a projec for a given project deadline?
###         * How to find each optimal time/cost point of the project over the complete time horizon
###
###   Note: 
###      - The experiment makes use of three projects (references mentioned below)
###        ° Project 1. Small project from Study 1 
###                     (and published as Figure 3.2 in book 1)
###        ° Project 2. Simplified version of the real water production project of Study 2 
###                     (and published as Figure 3.5 and Table 3.1 in book 1)
###        ° Project 3. Stadium construction project (adapted from the project used in book 2)
###
###   References
###      Book 1. 
###      - Title: The Data-Driven Project Manager: A Statistical Battle Against Project Obstacles
###      - Author: Mario Vanhoucke
###      - Year: 2018
###      - Publisher: Apress Berkeley, CA
###      - Source: https://doi.org/10.1007/978-1-4842-3498-3
###
###      Book 2. 
###      - Title: Project Management with Dynamic Scheduling: Baseline Scheduling, Risk Analysis and Project Control
###      - Author: Mario Vanhoucke
###      - Year: 2013
###      - Publisher: Springer
###      - Source: https://doi.org/10.1007/978-3-642-40438-2
###
###      Study 1. 
###      - Title: New computational results on the discrete time/cost trade-off problem in project networks
###      - Author: Erik Demeulemeester, Bert De Reyck, Bram Foubert, Willy Herroelen and Mario Vanhoucke
###      - Year: 1998
###      - Publisher: Journal of the Operational Research Society, 49(11), 1153–1163
###      - Source: https://10.1057/palgrave.jors.2600634
###
###      Study 2. 
###      - Title: The project scheduling game (PSG): simulating time/ cost trade-offs in projects
###      - Author: Mario Vanhoucke, Ann Vereecke and Paul Gemmel
###      - Year: 2005
###      - Publisher: Project Management Journal, 36(1), 51–59
###      - Source: https://doi.org/10.1177/875697280503600106
###
###    Download the summary file "Summary_Experiment_2.pdf" or print on screen
###
#############################################################################

# Procedure to select the correct function to load the project data
def get_project_data(projectID):
    if projectID == 1:
        return get_project_data_1998_paper()
#        return get_project_data_for_Lucy()
    elif projectID == 2:
        return get_project_data_VMW()       
    elif projectID == 3:
        return get_project_data_ddpm_2018_extended() 
    else:
        raise ValueError("Invalid projectID. Choose 1, 2, or 3.")

# Set the project ID (change this to 2 or 3 as needed)
projectID = 1
print_summary_file(Infofolder, 2)

###########################################################################################
### Step 1. Calculate the earliest and latest possible project end time                 ###
###         (= this defines the complete time horizon of the project)                   ###
###########################################################################################

#Read the project data with the time/cost trade-offs
activity_set, time_cost_trade_offs, predecessors_list, activity_names, _ = get_project_data(projectID)

# Add dummy start and end nodes (Not really necessary here, but it is a good practice to do this every time)
add_dummy_nodes_to_project_data(activity_set, activity_names, prl=predecessors_list, tct=time_cost_trade_offs)

# Create activity dependencies
activity_dependencies = create_activity_network_dependencies(predecessors_list,{},activity_names, debugInfo = False)

#show_design_structure_matrix(activity_dependencies)
show_design_structure_matrix(activity_dependencies,xtick_size=17,title_size=17, showDummy = True)
show_design_structure_matrix(activity_dependencies,showDummy = False)

# Construct the CPM schedule with a minimum project duration
activity_set = select_minimum_activity_durations(time_cost_trade_offs, debugInfo = False)
graph, min_PD, max_BAC, short_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, False)
#print(f"\nMinimum project duration: {min_PD}")

# Construct the CPM schedule with a maximum project duration
activity_set = select_maximum_activity_durations(time_cost_trade_offs, debugInfo = False)
graph, max_PD, min_BAC, long_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, False)
#print(f"\nMaximum project duration: {max_PD}")

# Visualize the network graph (with or without dummy nodes)
visualize_network(graph, activity_names, showCP = False,
                        showEdgeLabels=False,
                        xtick_size=20,
                        ytick_size=20,
                        title_size=10,
                        node_size=9000,
                        showDummy=True)
visualize_network(graph, activity_names, showCP = False,
                        showEdgeLabels=False,
                        xtick_size=20,
                        ytick_size=20,
                        title_size=10,
                        node_size=9000,
                        showDummy=False)

visualize_network(graph, activity_names, showDummy=False)

# Visualize the schedule
#show_gantt_chart(short_schedule, False)
#show_gantt_chart(long_schedule)

print(f"Minimum project duration is {min_PD:.2f} (with cost {max_BAC:.2f}) (not optimized yet)")#": {min_PD},{max_BAC}")
print(f"Maximum project duration is {max_PD:.2f} (with cost {min_BAC:.2f})")# {max_PD},{min_BAC}")
print(f"Let's optimise the project cost for each possible project time between {min_PD:.2f} and {max_PD:.2f}")

###########################################################################################
### Step 2. Solve the discrete time/cost trade-off problem                              ###
###         (= iterate for the complete time horizon between min_PD and max_PD,         ###
###          each time running the integer programmming model in "time_cost_optimizer") ###
###########################################################################################

# Initialize an empty list to store optimised project times and costs for each duration
time_cost_profile = []

# Loop from min_PD to max_PD inclusive (i.e. the complete time horizon) and solve the problem (time_cost_optimizer)
for pd in range(min_PD, max_PD + 1):  
    project_deadline = pd
    TC, activity_schedule = time_cost_optimizer(time_cost_trade_offs, activity_dependencies, 
                                                activity_names, project_deadline, debugInfo = False)
#    print(activity_schedule)
    print(f"The project with deadline {project_deadline:.2f} has a minimum cost of {TC:.2f}")
    time_cost_profile.append((project_deadline,TC))

# Extract the first and second elements from each tuple
x_values = [x for x, y in time_cost_profile]
y_values = [y for x, y in time_cost_profile]


###########################################################################################
### Step 3. Plot the time/cost profile graph over the complete time horizon             ###
###########################################################################################

import matplotlib.ticker as ticker
from matplotlib.ticker import MultipleLocator
plt.plot(x_values, y_values, marker='o', linestyle='-', color='darkred')  # Line plot with markers
plt.xlabel('Project duration', fontsize = Value_xlabel_size)
plt.ylabel('Project cost', fontsize = Value_ylabel_size)
plt.title('Time/cost profile', fontsize = Value_title_size)
plt.xticks(fontsize=Value_xtick_size)
plt.yticks(fontsize=Value_ytick_size)
plt.grid(True)  # Add grid lines for better readability
#plt.gca().yaxis.set_major_locator(MultipleLocator(3))
plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}')) # Format the y-axis to use thousand separators
plt.tight_layout()  # Adjust layout for better spacing
plt.show()

###########################################################################################
### Optional step. Solve the model for a certain deadline and print it on the screen.   ###
###########################################################################################

#project_deadline = (min_PD + max_PD) / 2
#TC, activity_schedule = time_cost_optimizer(time_cost_trade_offs, activity_dependencies, activity_names, project_deadline, debugInfo = True)
