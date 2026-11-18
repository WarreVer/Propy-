"""
    Module Name: my_SRA_Engine.py
    
    THIS MODULE CONTAINS ALL PROCEDURES FOR A SCHEDULE RISK ANALYSIS USING MONTE CARLO SIMULATIONS

    This python file contains the following procedures:
    
        A. RUN A MONTE CARLO SIMULATION
        - def perform_monte_carlo_simulation(nrRuns, activity_names, activity_dependencies, activity_schedule,  
                                sim_level, sim_method, schedule_type, 
                                activity_risk_classes=None, resource_requirements=None, resource_availability=None, 
                                debugInfo=False)
            * The Monte Carlo simulation can be implemented in various ways, and I have made some choices, described below
            * Easy to understand parameters:
                - nrRuns: Number of simulation runs
                - activity_names
                - activity_dependencies: Activity network
            * Important parameters
                - activity_schedule: The baseline schedule used as the reference point for simulations
                    = This schedule can be either CPM or RES (cf. schedule_type)
                - schedule_type = activity_schedule can be "CPM" or "RES" schedule
                    CPM: Experiments 5 and 6 using a CPM schedule --> Output CI, SI, SSI, CRI
                    RES: Experiments 7 and 8 using a RCPSP schedule --> Output RCI, RSI, RSSI, CRI
                    Note that parameters "resource_requirements" and "resource_availability" are
                         only necessary if schedule_type = "RES"
            * Choices that I have made (could be done totally different)
                - sim_method: Choose the simulation type ("RAND" or "CLASS")
                - sim_level: Level of uncertainty in the activity durations ("LOW", "MEDIUM" or "HIGH")      
                - activity_risk_classes: Only necessary if sim_method = "CLASS" (3 classes used)
                - The MCS procedure often calls the "select_distribution_parameters" procedure:
                    ° level can be "LOW", "MEDIUM" or "HIGH"
                    ° risk_type can be "NORMAL", "SYM_TRIANGULAR", "RIGHTTAILED_TRIANGULAR" or "UNIFORM"

        B. CALCULATE SENSITIVITY METRICS (TIME AND COST)
        - calculate_sensitivity_metrics(simulated_schedules_df, debugInfo)
            * This procedure calculates the following sensitivity metrics:
              - Time sensitivity:
                  ° CI, SI and SSI (for critical path simulations) 
                  ° RCI, RSI and RSSI (for critical chain simulations)
                  ° CRI(t) (for CP and CC simulations)
              - Cost sensitivity    
                  ° CRI(c) (for CP and CC simulations)
              (Abbreviations for criticality index, sensitivity index, schedule sensitivity index, cruciality index)

        - create_horizontal_sensitivity_graph(sensitivity_dictionary, title_string, ...layoutoptions...)

        C. VISUALIZE THE GENERATED DATA (ACTIVITY (not very important) AND PROJECT)
        - visualize_simulated_activity_data(sim_schedules, Time_or_Cost, ...layoutoptions...)
        - visualize_simulated_project_data(sim_schedules, ...layoutoptions...)

        Note: Some procedures contain layout options:
                                        xlabel_size=None, ylabel_size=None,
                                        xtick_size=None, ytick_size=None,
                                        legend_size=None,
                                        title_size=None, 

        D. References: 
            Find a general introduction to schedule risk analysis in:
                Vanhoucke, M., 2014, 
                "Integrated project management and control: First comes the theory, then the practice", 
                Springer: 141 pages
                
            Find the relevance of the sensitivity graphs in:
                Vanhoucke, M., 2018, 
                “The data-driven project manager: A statistical battle against project obstacles”, 
                Apress: 158 pages
"""    

from Python_Modules.my_General_Functions import *
from Python_Modules.my_CPM_Scheduler import *
from Python_Modules.my_RCP_Scheduler import *

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from scipy.stats import norm, triang, rv_discrete, uniform, cauchy, pareto
from scipy.stats import lognorm
import random

def select_distribution_parameters(level, risk_type):
    
#    level can be "LOW", "MEDIUM" or "HIGH"
#    risk_type can be "NORMAL", "SYM_TRIANGULAR", "RIGHTTAILED_TRIANGULAR" or "UNIFORM"
    
    min_scale = max_scale = low_percentage = high_percentage = None  # Default values
    
    if level == "LOW":
        if risk_type in ["NORMAL", "LOGNORMAL"]:
            min_scale, max_scale = {
                "NORMAL": (0.05, 0.1),
                "LOGNORMAL": (0.1, 0.3)
            }[risk_type]
        elif risk_type in ["SYM_TRIANGULAR", "RIGHTTAILED_TRIANGULAR", "UNIFORM"]:
            low_percentage, high_percentage = {
                "SYM_TRIANGULAR": (0.9, 1.1),
                "RIGHTTAILED_TRIANGULAR": (0.9, 1.15),
                "UNIFORM": (0.85, 1.15)
            }[risk_type]
        else:
            raise ValueError("Invalid risk type")

    elif level == "MEDIUM":
        if risk_type in ["NORMAL", "LOGNORMAL"]:
            min_scale, max_scale = {
                "NORMAL": (0.1, 0.3),
                "LOGNORMAL": (0.3, 0.6)
            }[risk_type]
        elif risk_type in ["SYM_TRIANGULAR", "RIGHTTAILED_TRIANGULAR", "UNIFORM"]:
            low_percentage, high_percentage = {
                "SYM_TRIANGULAR": (0.75, 1.25),
                "RIGHTTAILED_TRIANGULAR": (0.75, 1.40),
                "UNIFORM": (0.60, 1.40)
            }[risk_type]
        else:
            raise ValueError("Invalid risk type")

    elif level == "HIGH":
        if risk_type in ["NORMAL", "LOGNORMAL"]:
            min_scale, max_scale = {
                "NORMAL": (0.3, 0.5),
                "LOGNORMAL": (0.6, 1.0)
            }[risk_type]            
        elif risk_type in ["SYM_TRIANGULAR", "RIGHTTAILED_TRIANGULAR", "UNIFORM"]:
            low_percentage, high_percentage = {
                "SYM_TRIANGULAR": (0.5, 1.5),
                "RIGHTTAILED_TRIANGULAR": (0.5, 1.75),
                "UNIFORM": (0.40, 1.60)
            }[risk_type]
        else:
            raise ValueError("Invalid risk type")

    else:
        raise ValueError("Invalid level")

    return min_scale, max_scale, low_percentage, high_percentage
  

def perform_monte_carlo_simulation(
    nrRuns, activity_names, activity_dependencies, activity_schedule,  
    sim_level, sim_method, schedule_type, 
    activity_risk_classes=None, resource_requirements=None, resource_availability=None, 
    debugInfo=False
):     
    
    """
    This Schedule Risk Analysis procedure runs a Monte Carlo simulation to imitate real-life executions, as follows
        - Uncertainty in the activity durations is simulated based on activity duration distributions
        - Uncertainty in the activity costs is calculated as the unit cost per activity * the simulation duration
        
    --> Inputs:
            - nrRuns: Number of simulation runs
            - activity_names
            - activity_dependencies: Activity network
            - activity_schedule: The baseline schedule used as the reference point for simulations
                = This schedule can be either CPM or RES (cf. schedule_type)
       - sim_method = "RAND" or "CLASS"
            - sim_level: Level of uncertainty in the activity durations ("LOW", "MEDIUM" or "HIGH")
            - sim_method: Choose the simulation type ("RAND" or "CLASS")
            - schedule_type: activity_schedule can be "CPM" or "RES" schedule
            - activity_risk_classes: Only necessary if sim_method = "CLASS" (3 classes used)
            - resource_requirements: Only necessary if schedule_type = "RES"
            - resource_availability: Only necessary if schedule_type = "RES"
            - debugInfo

    --> Outputs: A dataframe of simulated schedules containing for each run:
            - Total Project Duration
            - Total Project Cost
            - Simulated Schedule: (dictionary as "key: (activity name, time, cost, start, end, slack)”)
    
    Note that this procedure can be used for different purposes:
        - To get an idea about the uncertainty of the total project duration and cost (visualize_simulated_project_data)
        - To perform a schedule risk analysis and get the activity sensitivity metrics (calculate_sensitivity_metrics)
        - To simulate an artificial project execution and get the Earned Value Management metrics (plot_selected_metrics)
    """

    # Import pandas, this is necessary if "perform_monte_carlo_simulation" is run several times
    import pandas as pd
    

    # Step 1. Validate schedule_type (with or without resources)
    #         CPM = the activity_schedule is a CPM schedule and the simulated schedule will ingore resources too
    #               (resource_requirements and resource_availability can be put on None)
    #         RES = the activity_schedule is a RCP schedule and the simulated schedule will solve resource conflits too
    #               (resource_requirements and resource_availability are required)
    #               Note: the activity_schedule can be constructed with priority rules or with optimal MIP model
    #                     the simulated_schedule is constructed with a parallel schedule generation scheme 
    #                     (using the activity start times of the activity_schedule as priority rule
    if schedule_type not in {"CPM", "RES"}:
        raise ValueError("schedule_type must be either 'CPM' or 'RES'")

    if schedule_type == "RES" and (resource_requirements is None or resource_availability is None):
        raise ValueError("resource_requirements and resource_availability are required when schedule_type='RES'.")

    if sim_method not in {"RAND", "CLASS"}:
        raise ValueError("sim_method must be either 'RAND' or 'CLASS'")
        
    if sim_method == "CLASS" and activity_risk_classes is None:
        raise ValueError("activity_risk_classes is required when sim_method='CLASS'.")

    # Debugging info if needed
    if debugInfo:
        print(f"Running Monte Carlo Simulation with schedule_type: {schedule_type}")
    
    # Initialize the activities dictionary
    activity_uncertainty = {}  
   
    # Assign probability distributions to activities (for their durations)
    for activity, details in activity_schedule.items():
        activity_name, activity_duration, activity_cost, start, finish, slack = details[0]  # Unpack the first tuple in the list

        
######### Method 1. Randomly choose a distribution type #########
        if sim_method == "RAND":
#           distribution_type = random.choice(['normal', 'triangular', 'uniform', 'cauchy', 'pareto'])
            min_scale ,max_scale, _, _ = select_distribution_parameters(sim_level, "NORMAL")
            distribution_type = 'normal'

               # WERKT NOG NIET... NEGATIVE VALUES
#            min_scale, max_scale, _, _ = select_distribution_parameters(sim_level, "LOGNORMAL")
#            distribution_type = 'lognormal'

    
######### Method 2. Use triangular distributions based on the three PERT estimates #########
        # TODO!!!!!!!!!
    
        elif sim_method == "PERT":
            print("THE PERT SIMULATION IS STILL UNDER CONSTRUCTION")
        
######### Method 3. Use the activity_risk_classes #########
        #    - Variation: A symmetrical distribution to denote that earliness is equally likely than lateness
        #    - Foreseen uncertainty: A skewed distribution to denote that lateness is more likely than earliness
        #    - Unforeseen uncertainty: A uniform distribution to denote that each duration is equally likely (stating that the risk is really unknown)
        #    - This is of course just a simple illustrative system that can be extended, and more information can be found in:
        #      REFERENCE XXXXXX
        
        
        # Normal distributions
        #   - Average duration = activity_duration
        #   - Standard deviation between min_stDev and max_stDev as a factor min_scale/max_scale of the activity_duration
        # Examples:
        #   - Low uncertainty (activity durations are highly predictable): e.g., min_scale = 0.05, max_scale = 0.1
        #   - Medium uncertainty (some variation expected) e.g., min_scale = 0.1, max_scale = 0.3
        #   - High uncertainty (activity durations are very uncertain) e.g., min_scale = 0.3, max_scale = 0.5
        #
        # Lognormal distributions
        #   - Low Risk (σ = 0.1 – 0.3): The lognormal distribution is almost symmetric, with low dispersion.
        #   - Medium Risk (σ = 0.3 – 0.6): More spread in the duration values.
        #   - High Risk (σ = 0.6 – 1.0): Highly skewed distribution with a long right tail.
        #
        # Triangular distributions
        #   - mode = activity duration
        #   - lower_limit and upper_limit expressed as a percentage of the activity_duration
        # Examples:
        #   A. For symmetric distributions (variation)
        #   - Low uncertainty: low_percentage = 0.9 and high_percentage = 1.1
        #   - Medium uncertainty: low_percentage = 0.75 and high_percentage = 1.25
        #   - High uncertainty: low_percentage = 0.5 and high_percentage = 1.5
        #   B. For tailed distributions (foreseen uncertainty)            
        #   - Low uncertainty: low_percentage = 0.9 and high_percentage = 1.15
        #   - Medium uncertainty: low_percentage = 0.75 and high_percentage = 1.40
        #   - High uncertainty: low_percentage = 0.5 and high_percentage = 1.75
        #
        # Uniform distributions (unforseen uncertainty)
        #   - lower_limit and upper_limit expressed as a percentage of the activity_duration
        # Examples (values of variation but a bit wider)
        #   - Low uncertainty: low_percentage = 0.85 and high_percentage = 1.15
        #   - Medium uncertainty: low_percentage = 0.60 and high_percentage = 1.40
        #   - High uncertainty: low_percentage = 0.40 and high_percentage = 1.60
        
        elif sim_method == "CLASS":
            # Use the "select_distribution_parameters" procedure to set the parameters
            #    - level can be "LOW", "MEDIUM" or "HIGH"
            #    - risk_type can be "NORMAL", "SYM_TRIANGULAR", "RIGHTTAILED_TRIANGULAR" or "UNIFORM"

            # Select the distributions for each activity (according to their activity risk class)
            if activity in activity_risk_classes["No Risk"]:
                distribution_type = 'norisk'
            elif activity in activity_risk_classes["Variation"]:
    #            print(f"{activity_names[activity]} belongs to Variation")
                _ ,_ , low_percentage, high_percentage = select_distribution_parameters(sim_level, "SYM_TRIANGULAR")
                distribution_type = 'triangular'
            elif activity in activity_risk_classes["Foreseen Uncertainty"]:
    #            print(f"{activity_names[activity]} belongs to Foreseen Uncertainty")
                _ ,_ , low_percentage, high_percentage = select_distribution_parameters(sim_level, "RIGHTTAILED_TRIANGULAR")
                distribution_type = 'triangular'
            elif activity in activity_risk_classes["Unforeseen Uncertainty"]:
    #            print(f"{activity_names[activity]} belongs to Unforeseen Uncertainty")
                _ ,_ , low_percentage, high_percentage = select_distribution_parameters(sim_level, "UNIFORM")
                distribution_type = 'uniform'
            else:
    #            print(f"{activity_names.get(activity, 'Unknown Activity')} is not classified")
                min_scale ,max_scale, _, _ = select_distribution_parameters(sim_level, "NORMAL")    
                distribution_type = 'normal'
        else:
            print("No valid method chosen")
            return 0


        # Select the appropriate probability distribution for simulation activity duration uncertainty
        # Note that "duration_distribution" is a distribution object, so I used a constant distribution with scipy.stats.rv_discrete:

        if distribution_type == 'norisk':
            activity_uncertainty[activity] = {
                'duration_distribution': rv_discrete(values=([activity_duration], [1.0])),  # 100% probability of `activity_duration`
                'cost_per_unit': activity_cost / activity_duration if activity_duration != 0 else 0
            }
        elif distribution_type == 'normal':
            min_stDev = max(min_scale,min_scale * activity_duration)
            max_stDev = max(min_stDev,max_scale * activity_duration)
            scale = random.uniform(min_stDev, max_stDev)  # Random scale between min and max
            activity_uncertainty[activity] = {
                'duration_distribution': norm(loc=activity_duration, scale=scale),
                'cost_per_unit': activity_cost / activity_duration if activity_duration != 0 else 0
            }
        elif distribution_type == 'lognormal':    
            sigma = random.uniform(min_scale, max_scale)
            
            mu = np.log(activity_duration) - (sigma**2 / 2)  # Adjusted mean
#            epsilon = 1e-6  # Smallest allowed duration
#            adjusted_duration = max(activity_duration, epsilon)
#            mu = np.log(adjusted_duration) - (sigma**2 / 2)

            activity_uncertainty[activity] = {
                'duration_distribution': lognorm(s=sigma, scale=np.exp(mu), loc=0),  # Corrected scale
                'cost_per_unit': activity_cost / activity_duration if activity_duration != 0 else 0
            }                        
        elif distribution_type == 'triangular':
            # Triangular distribution requires lower limit, upper limit, and mode
            mode = activity_duration  # Set mode to activity_duration
            lower_limit = max(0,activity_duration * low_percentage)
            upper_limit = activity_duration * high_percentage          
            
            if lower_limit == upper_limit:
                duration_distribution = rv_discrete(values=([lower_limit], [1.0]))  # Always returns lower_limit
            else:
                c = (mode - lower_limit) / (upper_limit - lower_limit)
                duration_distribution = triang(c, loc=lower_limit, scale=(upper_limit - lower_limit))
           
            activity_uncertainty[activity] = {
                'duration_distribution': duration_distribution,
                'cost_per_unit': activity_cost / activity_duration if activity_duration != 0 else 0
            }

        elif distribution_type == 'uniform':
            lower_limit = max(0,activity_duration * low_percentage)
            upper_limit = activity_duration * high_percentage                                     
            activity_uncertainty[activity] = {
                'duration_distribution': uniform(loc=lower_limit, scale=(upper_limit - lower_limit)),
                'cost_per_unit': activity_cost / activity_duration if activity_duration != 0 else 0
            }  
        elif distribution_type == 'cauchy':
            # Cauchy distribution is defined by a location and scale
            location = activity_duration  # Set location to activity_duration
            scale = random.uniform(min_scale, max_scale)  # Random scale for variability
            activity_uncertainty[activity] = {
                'duration_distribution': cauchy(loc=location, scale=scale),
                'cost_per_unit': activity_cost / activity_duration if activity_duration != 0 else 0
            }

        elif distribution_type == 'pareto':
            # Pareto distribution requires a scale parameter (x_m) and shape parameter (alpha)
            x_m = max(1, activity_duration - 2)  # Minimum value must be greater than zero
            alpha = random.uniform(1.5, 3)  # Shape parameter for fat tails
            activity_uncertainty[activity] = {
                'duration_distribution': pareto(b=alpha, scale=x_m),
                'cost_per_unit': activity_cost / activity_duration if activity_duration != 0 else 0
            }    

    # Run a Monte Carlo simulation (MCS)
    min_activity_duration = 0 # never generate negative durations (e.g. dummies have already 0 days)
    num_simulations = nrRuns
    list_simulated_schedules = []

    for count in range(num_simulations):
        if debugInfo:
            print_progress_bar("Running Monte Carlo simulation: ", count, num_simulations, steps = 1, bar_length = 40)
        
        # Sample durations based on uncertainty defined in "activity_uncertainty"
        sampled_durations = {
            activity: max(activity_info['duration_distribution'].rvs(), min_activity_duration)
            for activity, activity_info in activity_uncertainty.items()
        }
#        print("Activity = ",activity)
#        print("Simulated activity durations: ",sampled_durations)        

        # Calculate costs based on sampled durations
        calculated_costs = {activity: duration * activity_info['cost_per_unit']
                            for activity, (duration, activity_info) in zip(sampled_durations.keys(), 
                            zip(sampled_durations.values(), activity_uncertainty.values()))}
        total_cost = sum(calculated_costs.values())
        #print("Simulated activity costs: ",calculated_costs)
        #print(f"Project cost: {total_cost:.2f}")

        # Merge the sampled durations and costs in dictionary "key: (duration, cost)" for calculation CPM (like activity_set)
        sampled_activity_set = {
            activity: (sampled_durations[activity], calculated_costs[activity])
            for activity in sampled_durations.keys()
        }

        # Simulate the new CPM schedule (with real durations and costs)
        if schedule_type == "CPM":
            _, total_duration, real_cost, simulated_schedule = calculate_critical_path(
                sampled_activity_set, activity_dependencies, activity_names, False)

        # Simulate the new resource feasible schedule (with real durations and costs)
        # Approach: 
        #    - Use the start times of the current schedule as priority rule 
        #    - Apply the roadrunner strategy (no railway of fully optimized strategy) using the parallel SGS!
        if schedule_type == "RES":
            # Set the priority list equal to the start times of the resource-feasible baseline schedule
            priority_list = [(key, values[0][3]) for key, values in activity_schedule.items()]
            # Generate a sampled schedule with the new durations (the corresponding costs)
            total_duration, project_cost, simulated_schedule, _, _ = parallel_sgs(
                activity_names,
                sampled_activity_set,
                activity_dependencies,
                resource_requirements, # not in CPM simulation
                resource_availability, # not in CPM simulation
                priority_list,
                debugInfo = False
            )
            #print("Simulated duration = ", total_duration)
        
        # Add the total project duration, total project cost and simulated schedule 
        list_simulated_schedules.append((total_duration, total_cost, simulated_schedule))
        
        # Note that the total_cost should be the same than the real_cost (check!)
        # print("real_cost is equal to Total Cost" if real_cost == total_cost else "real_cost is not equal to Total Cost")

    # Convert results to a DataFrame for analysis
    list_simulated_schedules_df = pd.DataFrame(list_simulated_schedules, columns=['Total Duration', 'Total Cost', 'Simulated Schedules'])
    return list_simulated_schedules_df
    
def visualize_simulated_project_data(sim_schedules,
                                      xlabel_size=None, ylabel_size=None,
                                      xtick_size=None, ytick_size=None,
                                      legend_size=None,
                                      title_size=None, 
):

    import matplotlib.ticker as ticker
    
    xlabel_size = xlabel_size if xlabel_size is not None else Value_xlabel_size
    ylabel_size = ylabel_size if ylabel_size is not None else Value_ylabel_size
    xtick_size = xtick_size if xtick_size is not None else Value_xtick_size
    ytick_size = ytick_size if ytick_size is not None else Value_ytick_size
    legend_size = legend_size if legend_size is not None else Value_legend_size    
    title_size = title_size if title_size is not None else Value_title_size

    
    # Visualization (duration)
    plt.figure(figsize=(10, 6))
    plt.hist(sim_schedules['Total Duration'], bins=30, color='lightblue', edgecolor='black', alpha=0.7)
    plt.title('Monte Carlo Simulation of Project Duration', fontsize = title_size)
    plt.xlabel('Total Duration', fontsize = xlabel_size)
    plt.ylabel('Frequency', fontsize = ylabel_size)
    plt.grid(axis='y', alpha=0.75)
    plt.axvline(sim_schedules['Total Duration'].mean(), color='red', linestyle='dashed', linewidth=2, label='Mean Duration')

    # Format the x-axis and y-axis to use thousand separators
#    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
#    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f'{int(y):,}'))

    plt.xticks(fontsize=xtick_size)
    plt.yticks(fontsize=ytick_size)

    plt.legend(fontsize = legend_size)
    plt.show()

    # Print standard deviation, minimum, and maximum durations with comma as thousand separators
    print(f"Mean Project Duration: {sim_schedules['Total Duration'].mean():,.2f}")
    print(f"Standard Deviation: {sim_schedules['Total Duration'].std():,.2f}")
    print(f"Minimum Duration: {sim_schedules['Total Duration'].min():,.2f}")
    print(f"Maximum Duration: {sim_schedules['Total Duration'].max():,.2f}")

    mean_duration = sim_schedules['Total Duration'].mean()
    stdev_duration = sim_schedules['Total Duration'].std()

    # Visualization (cost)
    plt.figure(figsize=(10, 6))
    plt.hist(sim_schedules['Total Cost'], bins=30, color='lightblue', edgecolor='black', alpha=0.7)
    plt.title('Monte Carlo Simulation of Project Cost', fontsize = title_size)
    plt.xlabel('Total Cost', fontsize = xlabel_size)
    plt.ylabel('Frequency', fontsize = ylabel_size)
    plt.grid(axis='y', alpha=0.75)
    plt.axvline(sim_schedules['Total Cost'].mean(), color='red', linestyle='dashed', linewidth=2, label='Mean Cost')
    # Format the x-axis and y-axis to use thousand separators
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f'{int(y):,}'))

    plt.xticks(fontsize=xtick_size)
    plt.yticks(fontsize=ytick_size)  
    
    plt.legend(fontsize = legend_size)
    plt.show()

    # Print standard deviation, minimum, and maximum durations with comma as thousand separators
    print(f"Mean Project Cost: {sim_schedules['Total Cost'].mean():,.2f}")
    print(f"Standard Deviation: {sim_schedules['Total Cost'].std():,.2f}")
    print(f"Minimum Cost: {sim_schedules['Total Cost'].min():,.2f}")
    print(f"Maximum Cost: {sim_schedules['Total Cost'].max():,.2f}")

def visualize_simulated_activity_data(sim_schedules, Time_or_Cost,
                                      xlabel_size=None, ylabel_size=None, #NOT YET IMPLEMENTED
                                      xtick_size=None, ytick_size=None,#NOT YET IMPLEMENTED
                                      legend_size=None,#NOT YET IMPLEMENTED
                                      title_size=None, #NOT YET IMPLEMENTED
):
    
    activities = list(sim_schedules['Simulated Schedules'].iloc[0].keys())
    
    # Initialize dictionaries to hold means and counts (make sure that activity_names exist in input data!)
    ActivityTimeCost = {activity: [] for activity in activities}

    # Loop over each activity in the list of activities
    for activity in activities:
        # Extract the activity duration and cost (second and third value) from each tuple for the current activity
        activity_duration = sim_schedules['Simulated Schedules'].apply(lambda x: x[activity][0][1])
        activity_cost = sim_schedules['Simulated Schedules'].apply(lambda x: x[activity][0][2])
        if (Time_or_Cost == "T"):
            ActivityTimeCost[activity]=activity_duration
        else:    
            ActivityTimeCost[activity]=activity_cost
    
    # Method 1. Create a histogram for each activity
    #    for activity, values in ActivityTimeCost.items():
    #        plt.figure(figsize=(8, 4))  # Set the figure size
    #        plt.hist(values, bins=5, alpha=0.7, color='blue')  # Create histogram
    #        plt.title(f'Histogram of {activity}')  # Title for each histogram
    #        plt.xlabel('Value')  # X-axis label
    #        plt.ylabel('Frequency')  # Y-axis label
    #        plt.grid(axis='y', alpha=0.75)  # Optional grid for better readability
    #        plt.show()  # Display the histogram    

    #Method 2. Merge the histograms in one plot and optimize the number of bins
    # Number of activities
    num_activities = len(ActivityTimeCost)

    # Determine number of rows needed for the subplots
    num_columns = 4
    num_rows = (num_activities + num_columns - 1) // num_columns  # Ceiling division to get full rows

    # Create subplots with specified rows and columns
    fig, axes = plt.subplots(num_rows, num_columns, figsize=(15, num_rows * 3), sharex=True)

    # Flatten axes array for easy iteration
    axes = axes.flatten()

    # Function to calculate the number of bins dynamically
    def calculate_bins(data):
        # Use Freedman-Diaconis rule to determine number of bins
        if len(data) > 1:  # Ensure we have more than one value
            iqr = np.percentile(data, 75) - np.percentile(data, 25)  # Interquartile range
            bin_width = 2 * iqr / (len(data) ** (1/3))  # Calculate bin width
            if bin_width == 0:  # Handle case where all values are the same (e.g. for dummy activities)
                return 1
            return max(1, int((max(data) - min(data)) / bin_width))  # Ensure at least 1 bin
        return 1  # Return 1 bin if not enough data

    def calculate_bins2(data):
        ###Ensures a well-spread histogram without empty bins
        if len(set(data)) == 1:  
            return 1  # All values are the same, just one bin

        iqr = np.percentile(data, 75) - np.percentile(data, 25)  # Interquartile range
        bin_width = 2 * iqr / (len(data) ** (1/3))  # Freedman-Diaconis rule

        if bin_width == 0 or np.isnan(bin_width):  
            return min(10, len(data) // 2)  # Prevent division errors or empty bins

        num_bins = max(5, int((max(data) - min(data)) / bin_width))  # At least 5 bins
        return num_bins

    def calculate_bins3(data):
        """Ensures well-spread bins without making them too tight or too wide."""
        if len(set(data)) == 1:  
            return 1  # Single value, just one bin

        iqr = np.percentile(data, 75) - np.percentile(data, 25)  # Spread of middle 50%
        bin_width = 2 * iqr / (len(data) ** (1/3))  # Freedman-Diaconis rule

        if bin_width == 0 or np.isnan(bin_width):  
            return min(15, len(data) // 2)  # Force at least 15 bins

        num_bins = max(8, int((max(data) - min(data)) / bin_width))  # At least 8 bins
        return num_bins
    
    
    # Plot histograms for each activity in separate subplots
    for ax, (activity, values) in zip(axes, ActivityTimeCost.items()):
        bins = calculate_bins(values)  # Calculate number of bins
#        bins = calculate_bins3(values)  # Calculate number of bins
#        print("Number of bins = ", bins)
#        print("values = ", values)
        bins = 30
        ax.hist(values, bins=bins, alpha=0.7, color='lightblue')  # Change color as needed
#        ax.hist(values, bins='auto', alpha=0.7, color='lightblue')  # Change color as needed
        ax.set_title(f'Activity {activity}', fontsize = title_size)
        ax.set_ylabel('Frequency', fontsize = xlabel_size)
        ax.grid(axis='y', alpha=0.75)  # Optional grid for better readability

    # Hide any unused subplots
    for i in range(len(ActivityTimeCost), num_rows * num_columns):
        axes[i].axis('off')

    # Add common labels
#    if (Time_or_Cost == "T"):  #Doesn't work
#        plt.title('Simulated activity durations') 
#    else:    
#        plt.title('Simulated activity costs')
#    plt.xlabel('Value')
#    plt.legend(fontsize = legend_size)
    plt.tight_layout()  # Adjust layout for better spacing
    plt.show()  # Display the combined histogram    

def calculate_sensitivity_metrics(simulated_schedules_df, debugInfo):    

    epsilon = 1e-5

    mean_duration = simulated_schedules_df['Total Duration'].mean()
    stdev_duration = simulated_schedules_df['Total Duration'].std()

    if (debugInfo == True):
        print(f"Mean Project Duration: {simulated_schedules_df['Total Duration'].mean():,.2f}")
        print(f"Standard Deviation: {simulated_schedules_df['Total Duration'].std():,.2f}")
        print(f"Minimum Duration: {simulated_schedules_df['Total Duration'].min():,.2f}")
        print(f"Maximum Duration: {simulated_schedules_df['Total Duration'].max():,.2f}")
    
    # Extract the names of activities from the first row of a DataFrame column that contains dictionaries
    activities = list(simulated_schedules_df['Simulated Schedules'].iloc[0].keys())
    
    # Initialize dictionaries to hold means and counts (make sure that activity_names exist in input data!)
    activity_SI = {activity: 0 for activity in activities}
    activity_SI = {activity: 0 for activity in activities}
    activity_CI = {activity: 0 for activity in activities}
    activity_CRIt = {activity: 0 for activity in activities}
    activity_CRIc = {activity: 0 for activity in activities}
    ActivityDurations = {activity: [] for activity in activities}
    activity_SSI = {activity: 0 for activity in activities}    

    # Loop over each activity in the list of activities
    for activity in activities:
        # Extract the activity duration and cost (second and third value) from each tuple for the current activity
        activity_duration = simulated_schedules_df['Simulated Schedules'].apply(lambda x: x[activity][0][1])
        activity_cost = simulated_schedules_df['Simulated Schedules'].apply(lambda x: x[activity][0][2])
        slack = simulated_schedules_df['Simulated Schedules'].apply(lambda x: x[activity][0][5])
        
#        print("activity = ", activity)
#        print("activity_duration (in calculate_sensitivity_metrics)= ", activity_duration)
#        print("slack (in calculate_sensitivity_metrics)= ", slack)
        
        # Cruciality index (for time and cost) - Pearson correlation
        correlation = simulated_schedules_df['Total Duration'].corr(activity_duration)
        activity_CRIt[activity] = abs(correlation)

        correlation = simulated_schedules_df['Total Cost'].corr(activity_cost)
        activity_CRIc[activity] = abs(correlation)

        # Criticality Index (CI)
        activity_CI[activity] = (slack < epsilon).mean()
        
        # Significance Index (SI)
        numerator = activity_duration * simulated_schedules_df['Total Duration']
        denominator = (activity_duration + slack) * mean_duration 
        valid_rows = denominator != 0  # Check for denominator values that are zero
        si = np.where(valid_rows, numerator / denominator, np.nan) # Only calculate SI where the denominator is not zero
        average_si = np.nanmean(si) # Calculate the average SI, excluding any NaN values        
        #average_si = np.nanmean(np.where((denominator != 0), numerator / denominator, np.nan))
        activity_SI[activity] = average_si
    
        # Schedule Sensitivity Index (SSI)
        std_AD = activity_duration.std()
        activity_ssi = (std_AD * activity_CI[activity]) / stdev_duration
        activity_SSI[activity] = activity_ssi

    # Display the results
    if (debugInfo == True):
        print("SI values for each activity:")
        for activity, mean in activity_SI.items():
            print(f"Activity {activity}: {mean:.2f}")

        print("\nCI values for each activity (average number of times slack is below epsilon for each activity):")
        for activity, avg_count in activity_CI.items():
            print(f"Activity {activity}: {avg_count:.2f}")

        print("\nSSI values for each activity:")
        for activity, avg_count in activity_SSI.items():
            print(f"Activity {activity}: {avg_count:.2f}")
    
        print("CRI(t) values for each activity:")
        for activity, mean in activity_CRIt.items():
            print(f"Activity {activity}: {mean:.2f}")

        print("CRI(c) values for each activity:")
        for activity, mean in activity_CRIc.items():
            print(f"Activity {activity}: {mean:.2f}")

    return activity_CI, activity_SI, activity_SSI, activity_CRIt, activity_CRIc

def create_horizontal_sensitivity_graph(sensitivity_dictionary, title_string,
                                          xlabel_size=None, ylabel_size=None,
                                          xtick_size=None, ytick_size=None,
                                          title_size=None
):
    
    xlabel_size = xlabel_size if xlabel_size is not None else Value_xlabel_size
    ylabel_size = ylabel_size if ylabel_size is not None else Value_ylabel_size
    xtick_size = xtick_size if xtick_size is not None else Value_xtick_size
    ytick_size = ytick_size if ytick_size is not None else Value_ytick_size
    title_size = title_size if title_size is not None else Value_title_size

#    print("sensitivity_dictionary = ", sensitivity_dictionary)
    
    # Prepare data for the bar chart
#    activities = list(sensitivity_dictionary.keys())
#    sensitivity_values = list(sensitivity_dictionary.values())

    # Clean and prepare data for plotting
    activities = []
    sensitivity_values = []

    for k, v in sensitivity_dictionary.items():
        # Exclude dummy start and end in the graphs
        if k in (keyDummyStart, keyDummyEnd):
            continue
        # Replace NaN with 0 (this is e.g. when no correlation could be calculated for the NoRisk activities)
        value = 0 if (v is None or isinstance(v, float) and math.isnan(v)) else v
    
        activities.append(k)
        sensitivity_values.append(value)

#    print("activities = ",activities)
#    print("sensitivity_values = ",sensitivity_values)
    
    # Create a horizontal bar chart
    plt.figure(figsize=(10, 4))
    plt.barh(activities, sensitivity_values, color='skyblue')
    
    # Use the title_string for the x-label and update the title with title_string
    if ylabel_size > 0:
        plt.xlabel(f'{title_string} Values', fontsize=xlabel_size)  # Use f-string to insert the title_string
    if xlabel_size > 0:
        plt.ylabel('Activities', fontsize=ylabel_size)
    plt.title(f'{title_string}', fontsize=title_size)  # Use title_string in the title
#    plt.xlim(0, max(sensitivity_values) + 0.1)  # Set x-axis limit for better visualization
    plt.xlim(0, 1)  # Set x-axis limit for better visualization
    plt.grid(axis='x', linestyle='--', alpha=0.7)

    plt.xticks(fontsize=xtick_size)
    plt.yticks(fontsize=ytick_size)
    
    # Show the plot
    plt.tight_layout()
    plt.show()
    