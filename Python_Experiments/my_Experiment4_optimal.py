#############################################################################
### Example experiment 4: Scheduling Projects with Resources (Optimally)
### = Solve the resource-constrained project scheduling problem optimally with integer programming
###
###   This experiment solves the resource-constrained project scheduling problem using a standard
###   integer programming model solved by the standard optimisation library PuLP for Python (https://coin-or.github.io/pulp)
###
###   Note: 
###      - The experiment makes use of three projects
###        (projects 1 and 2 come from "Book 1" and project 3 comes from "Book 2" mentioned below)
###        * Project 1 (1 resource). Network of Figure 7.1, resource data from Table 7.1 with schedule of Figure 7.3
###        * Project 2 (4 resources). Network of Figure 7.1, resource data from Table 7.2 with schedule of Figure 7.4
###        * Project 3 (4 resources). File "mv2.rcp" from the DC1 set as explained in Book 2 (see also Experiment 3 for further references)
###
###      - Optimisation solvers
###        * PuLP uses "CBC" as the default solver (The code uses PULP_CBC_CMD, a PuLP solver command wrapper that explicitly calls the CBC solver)
###        * The solver can be easily replaced with other, possibly more powerful solvers, such as CPLEX or GUROBI
###        * Both the choice of solver and the formulation of the integer programming (IP) model impact the complexity of the search
###          ° Project 1: Easy to solve (with current formulation in PuLP)
###          ° Project 2: very difficult (with current formulation in PuLP)
###          ° Project 3: Easy to solve (with current formulation in PuLP)
###   Alert:
###      - If you are interested in what defines the complexity to solve a project, read book 2 (information below)
###
###   Books:
###      The resource-constrained project scheduling problem is known to be NP-hard. 
###      Lots of research has been devoted to this challenging problem.
###   
###      Book 1: A general book on project scheduling, including a Chapter 8 on the RCPSP (with project data used in the experiment)
###      - Title: Project Management with Dynamic Scheduling: Baseline Scheduling, Risk Analysis and Project Control
###      - Author: Mario Vanhoucke
###      - Year: 2013
###      - Publisher: Springer
###      - Source: https://doi.org/10.1007/978-3-642-40438-2
###
###      Book 2: A book showing the search for project data for the RCPSP to better understand the complexity of this scheduling problem.
###      - Title: A Quest for Projects with Scarce Resources: Seeking Schedule Intelligence Through Project Data Discovery
###      - Author: Mario Vanhoucke
###      - Year: 2025
###      - Publisher: Springer
###      - Source: https://doi.org/10.1007/978-3-031-71507-5
###
###    Download the summary file "Summary_Experiment_4.pdf" or print on screen
###
#############################################################################

# Procedure to select the correct function to load the project data
def get_project_data(projectID):
    if projectID == 1:
        filename = Filefolder + "DS_Book_Table7_1.rcp"
    elif projectID == 2:
        filename = Filefolder + "DS_Book_Table7_2.rcp" ##USE THIS ONE
    elif projectID == 3:
        filename = Filefolder + "mv2.rcp" # Only MTS, LNRJ and LFT gives a good solution (20) while the others are (much) worse (optimal is 18)
#        filename = Filefolder + "drone.rcp" # THIS IS JUST A TEST
    else:
        raise ValueError("Invalid projectID. Choose 1, 2, or 3.")
    return filename    

# Set the project ID (change this to 2 or 3 as needed)
projectID = 1
print_summary_file(Infofolder, 4)

###########################################################################################
### Step 1. Construct a CPM schedule and detect resource conflicts                      ###
###########################################################################################
filename = get_project_data(projectID)
_, activity_set, successors_list, activity_names, \
        resource_requirements, resource_availability, _ = read_patterson_file(filename)
add_dummy_nodes_to_project_data(activity_set,activity_names,sul=successors_list,rr=resource_requirements)
activity_dependencies = create_activity_network_dependencies({},successors_list,activity_names, debugInfo = False)

# Construct the CPM schedule
graph, PD, BAC, planned_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, False)
#print('Planned duration (PD) = ', PD)
#print('Budget at completion (BAC) = ', BAC)

# Visualize the network graph (created in the "calculate_critical_path" function)
visualize_network(graph, activity_names,showDummy = True)

# Visualize the schedule using a Gantt chart
#show_gantt_chart(planned_schedule)

# Visualize the resource profiles (possibly with overallocations)
#plot_resource_profiles(planned_schedule, resource_availability, resource_requirements)

###########################################################################################
### Step 2. Construct a resource-feasible schedule
### = Solve the resource-constrained project scheduling problem (if possible) 
###   (explore the two options if you like)
###########################################################################################

# Option 1. Solve the model with no time windows and large upper bound time horizon
project_makespan, total_cost, activity_schedule = resource_scheduler_optimizer(
    activity_names, activity_set, activity_dependencies, resource_availability, 
    resource_requirements, debugInfo = False)

# Option 2. Solve the model with strict activity time windows and heuristic upper bound time horizon
project_makespan, total_cost, activity_schedule = resource_scheduler_optimizer(
    activity_names, activity_set, activity_dependencies, resource_availability, 
    resource_requirements, time_window = True,  priority_rule = "LPT", debugInfo = False)

print("Optimal project duration (makespan) = ", project_makespan)

###########################################################################################
### Step 3. Show the solutions
### Note that the activities are not (always) scheduled as soon as possible
###########################################################################################

# Print the optimal activity_schedule
#for activity, schedule in activity_schedule.items():
#    print(f"{activity}: {schedule}")

# Show the Gantt chart of the schedule (and see that it is not an earliest start schedule!)
show_gantt_chart(activity_schedule, showCP = False, showCost = False)

#plot_resource_profiles(activity_schedule, resource_availability, resource_requirements)
plot_resource_profiles(activity_schedule, resource_availability, resource_requirements, legend_size=12, showName = False)
