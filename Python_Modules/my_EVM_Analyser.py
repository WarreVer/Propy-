"""
    Module Name: my_EVM_Analyser
    
    THIS MODULE CONTAINS ALL PROCEDURES FOR AN EARNED VALUE MANAGEMENT ANALYSIS

    This python file contains the following procedures:
    
        # EVM KEY METRICS AND PERFORMANCE MEASURES:

        - calculate_regularity_index(PD, BAC, PV, AT)
                = Can be called once the PV in the baseline schedule is known

        - calculate_evm_key_metrics(planned_schedule, real_schedule):
                * Calls "get_time_points(planned_schedule, real_schedule)"
                * This procedure calculates 
                    - The key metrics PV, AC, EV and ES
                    - The performance measures SV, CV, SV(t), SPI, CPI, SPI(t)
  
        - plot_selected_EVM_metrics(time_points, show_values = False, default_value=None, default_title=None,
                              xlabel_size=None, ylabel_size=None,
                              xtick_size=None, ytick_size=None,
                              legend_size=None,
                              title_size=None, 
                              thous_sep=None,
                              **kwargs):
                * time_points (list or array): The x-axis values (time) represented by the actual time AT.
                * kwargs: Up to 3 named arrays (e.g., PV=PV, AC=AC, EV=EV).
        
        # EVM FORECASTING:
        
        - calculate_evm_predictions(planned_schedule, PV, AC, EV, ES, AT, SV, SVt, CV, SPI, SPIt, CPI):
                * Calculates nine time and eight cost forecasting metrics
                
        - get_all_forecasting_accuracy(RealValue, prediction_values, method_names, debugInfo = False):
                * Calculates the MAPE and MPE values in the procedure "calculate_forecast_accuracy" 
                
        Note: 
            - How to determine the time points (x-axis) in all EVM graphs?

                Approach 1. Not used, but still possible in "calculate_evm_key_metrics"
                    = Take the unique start and end times of activities in the baseline schedule and real execution
                    Disadvantage: Many intermediate values do not appear on the graph
                Approach 2. Used by calling "get_time_points"
                    = All time values from start till end (maximum of baseline and real duration)
                    Advantage: Nice graphs
                    Possible disadvantage: Many values

        Reference: Find a general introduction to Earned Value Management in:
            Vanhoucke, M., 2010, 
            "Measuring time: Improving project performance using earned value management", 
            Springer: 164 pages
"""    

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker  # Import for thousand separator


from Python_Modules.my_General_Functions import * 

def get_time_points(planned_schedule, real_schedule):
    time_points = set()

    # Collect time points for planned schedule
    for values in planned_schedule.values():
        for (_, _, _, start, end, _) in values:
            # Add the start and end times
            time_points.add(start)
            time_points.add(end)
            # Add intermediate times between start and end (linearly spread)
            num_intervals = int(end - start)  # Duration is the number of intervals
            for i in range(1, num_intervals):
                intermediate_time = start + i
                time_points.add(intermediate_time)

    # Collect time points for real schedule
    for values in real_schedule.values():
        for (_, _, _, start, end, _) in values:
            # Add the start and end times
            time_points.add(start)
            time_points.add(end)
            # Add intermediate times between start and end (linearly spread)
            num_intervals = int(end - start)  # Duration is the number of intervals
            for i in range(1, num_intervals):
                intermediate_time = start + i
                time_points.add(intermediate_time)

    # Return sorted list of time points
    return sorted(time_points)

def calculate_regularity_index(PD, BAC, PV, AT):
     
    # The regularity index can only be calculated after having the PV and AT curve calculated as follows:
    #        PV, _, _, _, AT, _, _, _, _, _, _ = calculate_evm_key_metrics(planned_schedule, planned_schedule)    

    # Compute the linear reference line
    linear_line = (BAC / PD) * AT
#    print("LINEAR = ", linear_line)

    # Compute RI
    sum_PV = np.sum(PV)
#    sum_linear_PV_diff = np.sum(linear_line - PV)
    sum_linear_PV_abs_diff = np.sum(np.abs(linear_line - PV))

#    RI = (sum_PV - sum_linear_PV_diff) / sum_PV
    RI = (sum_PV - sum_linear_PV_abs_diff) / sum_PV
    return RI

def calculate_evm_key_metrics(planned_schedule, real_schedule):
    
    # I only use the time points obtained in the procedure "get_time_points"
    method_time_points = 2
    
    # Extract all unique time points
    if method_time_points == 1:
        time_points = sorted(set(end for values in planned_schedule.values() for (_, _, _, _, end, _) in values)
                             .union(set(end for values in real_schedule.values() for (_, _, _, _, end, _) in values)))
    #    print("Unique time points = ", time_points)
    elif method_time_points == 2:
        time_points = get_time_points(planned_schedule, real_schedule)
    
    if method_time_points == 1:
        # Compute Planned Value (PV)
        # Use indexing index[2] for cost, index[4] for end time
        pv = []
        for t in time_points:
            planned_value = sum(index[2] for values in planned_schedule.values() 
                                for index in values if index[4] <= t)
            pv.append(planned_value)

        # Compute Actual Cost (AC)
        ac = []
        for t in time_points:
            actual_cost = sum(index[2] for values in real_schedule.values() 
                              for index in values if index[4] <= t)
            ac.append(actual_cost)

        # Compute Earned Value (EV)
        ev = []
        for t in time_points:
            earned_value = sum(planned_activity[2]  # Use planned cost
                               for key, values in planned_schedule.items()
                               for planned_activity in values
                               if any(real_activity[4] <= t for real_activity in real_schedule.get(key, [])))  
            ev.append(earned_value)
    elif method_time_points == 2:
        # Initialize lists to hold the results
        pv = []
        ac = []
        ev = []

        # Helper function to calculate the linear cost distribution
        def linear_cost(start, end, cost, t):
            # If the time point is within the activity's duration
            if start < t <= end:
                return cost * (t - start) / (end - start)

            # If the time point is later than the activity finish
            if t > end:
                return cost

            # If the time point is before the activity starts
            return 0

        # Compute Planned Value (PV)
        for t in time_points:
            planned_value = 0
            for values in planned_schedule.values():
                for index in values:
                    start, end, cost = index[3], index[4], index[2]
                    planned_value += linear_cost(start, end, cost, t)
            pv.append(planned_value)

        # Compute Actual Cost (AC)
        for t in time_points:
            actual_cost = 0
            for values in real_schedule.values():
                for index in values:
                    start, end, cost = index[3], index[4], index[2]
                    actual_cost += linear_cost(start, end, cost, t)
            ac.append(actual_cost)


        # Compute Earned Value (EV)
        for t in time_points:
            earned_value = 0
            for key, values in planned_schedule.items():
                for planned_activity in values:
                    # Get planned details (cost, start, and end)
                    planned_start, planned_end, planned_cost = planned_activity[3], planned_activity[4], planned_activity[2]

                    # Check if the activity is in progress at time t in the real schedule
                    completed_fraction = 0  # Default to 0 if the activity hasn't been completed yet
                    for real_activity in real_schedule.get(key, []):
                        real_start, real_end = real_activity[3], real_activity[4]

                        # If real activity is in progress or completed by time t
                        if real_start == real_end:
                            completed_fraction = 1
                        elif real_start <= t <= real_end:
                            # Calculate the completed fraction based on real schedule
                            completed_fraction = (t - real_start) / (real_end - real_start)
                            break
                        elif t > real_end:  # If the real activity is already finished
                            completed_fraction = 1  # Fully completed
                            break

                    # Add the earned value based on the completed fraction and planned cost
                    earned_value += planned_cost * completed_fraction

            ev.append(earned_value)
        
    PV = np.array(pv)
    AC = np.array(ac)
    EV = np.array(ev)    

#    print("Planned Value = ", PV)
#    print("Actual Cost = ", AC)
#    print("Earned Value = ", EV)
    
    # Compute Earned Schedule (ES)
    es = []
    for ev_value in EV:
        if ev_value <= 0:
            es.append(0)
            continue
        
        # Find where EV falls between PV[t-1] and PV[t]
        es_t = 0
        for i in range(1, len(PV)):
            if PV[i - 1] <= ev_value <= PV[i]:  
                # Linear interpolation for fractional ES
                es_t = time_points[i - 1] + (ev_value - PV[i - 1]) / (PV[i] - PV[i - 1]) * (time_points[i] - time_points[i - 1])
                break
        else:
            # If EV exceeds all PV values, take max time
            es_t = time_points[-1]

        es.append(es_t)
    ES = np.array(es)
    
#    print("Earned Schedule (ES) = ", ES)
    
    # WRONG: THIS IS NOT THE UNIQUE TIME POINTS
    AT = np.array(time_points)
#    print("Actual Time (AT) = ", AT)
    
    # Compute Performance Metrics
    SV = EV - PV
    CV = EV - AC
    SVt = ES - AT
    
    SPI = np.array([EV / PV if PV != 0 else 1 for EV, PV in zip(EV, PV)])
    CPI = np.array([EV / AC if AC != 0 else 1 for EV, AC in zip(EV, AC)])
    SPIt = np.array([ES / AT if AT != 0 else 1 for ES, AT in zip(ES, AT)]) 

#    print("Planned duration (PD) = ", PD)
#    print("Budget at Completion (BAC) = ", BAC)    
#    print("Schedule Performance Index (SPI) = ", SPI)
#    print("Cost Performance Index (CPI) = ", CPI)    
#    print("Schedule Performance Index SPI(t) = ", SPIt)    

    return PV, AC, EV, ES, AT, SV, SVt, CV, SPI, SPIt, CPI

def calculate_evm_predictions(planned_schedule, PV, AC, EV, ES, AT, SV, SVt, CV, SPI, SPIt, CPI):

    # Time forecasting metrics (planned value method, earned duration method and earned schedule method)
    # Reference: https://www.pmknowledgecenter.com/dynamic_scheduling/control/earned-value-management-forecasting-time
    
    PD = max(activity[0][4] for activity in planned_schedule.values())
    BAC = sum(activity[0][2] for activity in planned_schedule.values())
    ED = AT * SPI
    
    PF = 1
    EACtPV1 = PD - (SV * PD) / BAC
    EACtED1 = AT + (np.maximum(PD, AT) - ED) / PF
    EACtES1 = AT + (PD - ES) / PF

    PF = SPI
    EACtPV2 = PD / SPI    
    EACtED2 = AT + (np.maximum(PD, AT) - ED) / PF    
    PF = SPIt
    EACtES2 = AT + (PD - ES) / PF

    SCI = SPI * CPI
    PF = SCI
    EACtPV3 = PD / SCI    
    EACtED3 = AT + (np.maximum(PD, AT) - ED) / PF    
    SCIt = SPIt * CPI
    PF = SCIt
    EACtES3 = AT + (PD - ES) / PF


    # Cost forecasting metrics (8 versions)
    # Reference: https://www.pmknowledgecenter.com/dynamic_scheduling/control/earned-value-management-forecasting-cost
    PF = 1
    EAC1 = AC + (BAC - EV) / PF
    PF = CPI
    EAC2 = AC + (BAC - EV) / PF
    PF = SPI
    EAC3 = AC + (BAC - EV) / PF
    PF = SPIt
    EAC4 = AC + (BAC - EV) / PF
    PF = SPI * CPI
    EAC5 = AC + (BAC - EV) / PF
    PF = SPIt * CPI
    EAC6 = AC + (BAC - EV) / PF
    PF = 0.8 * CPI + 0.2 * SPI
    EAC7 = AC + (BAC - EV) / PF
    PF = 0.8 * CPI + 0.2 * SPIt
    EAC8 = AC + (BAC - EV) / PF
    
    return EACtPV1, EACtPV2, EACtPV3, EACtED1, EACtED2, EACtED3, EACtES1, EACtES2, EACtES3, EAC1, EAC2, EAC3, EAC4, EAC5, EAC6, EAC7, EAC8

def get_all_forecasting_accuracy(RealValue, prediction_values, method_names, debugInfo = False):
    
    MAPE_list = []
    MPE_list = []
    # Initialize the dictionary to store the results
    forecast_results = {}

    # Loop over the prediction methods (enumerated to keep the index)
    for i, (forecast_values, method_name) in enumerate(zip(prediction_values, method_names), start=1):
        # Calculate MAPE and MPE for each forecast method
        MAPE, MPE = calculate_forecast_accuracy(RealValue, forecast_values)
        # Store the results in the dictionary with "EAC_{i}" as the key
        forecast_results[f"EAC_{i}"] = {"MAPE": MAPE, "MPE": MPE}
        # Store the values in the lists
        MAPE_list.append(MAPE)
        MPE_list.append(MPE)
        # Print the values
        if debugInfo == True:
            print(f"{method_name}: MAPE = {MAPE:.2f}%, MPE = {MPE:.2f}%")
    return MAPE_list, MPE_list

def calculate_forecast_accuracy(RealValue, PredictedValue):

    RealValue = np.array(RealValue)
    PredictedValue = np.array(PredictedValue)
    
    # Avoid division by zero
    mask = RealValue != 0
    MAPE = np.mean(np.abs((RealValue[mask] - PredictedValue[mask]) / RealValue[mask])) * 100
    MPE = np.mean((RealValue[mask] - PredictedValue[mask]) / RealValue[mask]) * 100

    return MAPE, MPE


def plot_selected_EVM_metrics(time_points, show_values = False, default_value=None, default_title=None,
                              xlabel_size=None, ylabel_size=None,
                              xtick_size=None, ytick_size=None,
                              legend_size=None,
                              title_size=None, 
                              thous_sep=None,
                              **kwargs):
    """
    This procedure plots up to 3 selected metrics over time.
        Parameters:
            - time_points (list or array): The x-axis values (time) represented by the actual time AT.
            - kwargs: Up to 3 named arrays (e.g., PV=PV, AC=AC, EV=EV).
            - default_value (float, optional): If provided, draws a horizontal dotted black line at this value.
    """
    
    xlabel_size = xlabel_size if xlabel_size is not None else Value_xlabel_size
    ylabel_size = ylabel_size if ylabel_size is not None else Value_ylabel_size
    xtick_size = xtick_size if xtick_size is not None else Value_xtick_size
    ytick_size = ytick_size if ytick_size is not None else Value_ytick_size
    legend_size = legend_size if legend_size is not None else Value_legend_size    
    title_size = title_size if title_size is not None else Value_title_size

    
    # Define a color and marker dictionary for consistency
    styles = {
        "PV": {"color": "blue", "marker": "o", "label": "Planned Value (PV)"},
        "AC": {"color": "red", "marker": "s", "label": "Actual Cost (AC)"},
        "EV": {"color": "green", "marker": "^", "label": "Earned Value (EV)"},
        "ES": {"color": "purple", "marker": "d", "label": "Earned Schedule (ES)"},
        "AT": {"color": "orange", "marker": "x", "label": "Actual Time (AT)"},
        "SPI": {"color": "cyan", "marker": "v", "label": "Schedule Performance Index (SPI)"},
        "SPIt": {"color": "magenta", "marker": "<", "label": "Schedule Performance Index (SPIt)"},
        "CPI": {"color": "brown", "marker": ">", "label": "Cost Performance Index (CPI)"},
        "SV": {"color": "lime", "marker": "h", "label": "Schedule Variance (SV)"},  # Hexagonal marker
        "CV": {"color": "pink", "marker": "p", "label": "Cost Variance (CV)"},  # Pentagon marker
        "SVt": {"color": "gray", "marker": "*", "label": "Time-Based Schedule Variance (SVt)"},  # Star marker

        # Predictions
        "EACtPV1": {"color": "yellow", "marker": "o", "label": "EACtPV1"},
        "EACtPV2": {"color": "yellowgreen", "marker": "s", "label": "EACtPV2"},
        "EACtPV3": {"color": "gold", "marker": "^", "label": "EACtPV3"},
        "EACtED1": {"color": "lightcoral", "marker": "d", "label": "EACtED1"},
        "EACtED2": {"color": "darkorange", "marker": "x", "label": "EACtED2"},
        "EACtED3": {"color": "forestgreen", "marker": "*", "label": "EACtED3"},
        "EACtES1": {"color": "blueviolet", "marker": "p", "label": "EACtES1"},
        "EACtES2": {"color": "crimson", "marker": "h", "label": "EACtES2"},
        "EACtES3": {"color": "darkslateblue", "marker": "v", "label": "EACtES3"},
        "EAC1": {"color": "seagreen", "marker": "^", "label": "EAC1"},
        "EAC2": {"color": "darkseagreen", "marker": "s", "label": "EAC2"},
        "EAC3": {"color": "mediumturquoise", "marker": "d", "label": "EAC3"},
        "EAC4": {"color": "teal", "marker": "x", "label": "EAC4"},
        "EAC5": {"color": "mediumaquamarine", "marker": "*", "label": "EAC5"},
        "EAC6": {"color": "lightseagreen", "marker": "o", "label": "EAC6"},
        "EAC7": {"color": "darkviolet", "marker": "p", "label": "EAC7"},
        "EAC8": {"color": "darkgreen", "marker": "h", "label": "EAC8"}   
    }

    # Limit to 3 arrays
    selected_keys = list(kwargs.keys())[:3]

    if not selected_keys:
        print("No data provided to plot.")
        return

    # Create the plot
    plt.figure(figsize=(10, 6))
    
    for key in selected_keys:
        if key in styles and key in kwargs:
            plt.plot(time_points, kwargs[key], 
                     marker=styles[key]["marker"], linestyle='-', 
                     color=styles[key]["color"], label=styles[key]["label"])
            
            # Conditionally add value annotations
            if show_values:
                for t, val in zip(time_points, kwargs[key]):
                    label = (f"{val:,.2f}" if thous_sep else f"{val:.2f}")
                    plt.text(t, val, label, fontsize=9, ha='right',color=styles[key]["color"])         

    # Add a horizontal dotted black line if default_value is provided      
    if default_value is not None:
        ref_label = (f"Reference ({default_value:,.2f})" if thous_sep else f"Reference ({default_value:.2f})" )
        plt.axhline(y=default_value, color='red', linestyle='dotted', linewidth=1.5, label=ref_label)    
        
    # Formatting
    if xlabel_size:
        plt.xlabel("Time", fontsize=xlabel_size)
    if ylabel_size:    
        plt.ylabel("Metric Value",fontsize=ylabel_size)
    if default_title == None:
        plt.title(" vs ".join(styles[key]["label"] for key in selected_keys),fontsize=title_size)
    else:
        plt.title(default_title,fontsize=title_size)
    
    plt.xticks(fontsize=xtick_size)
    plt.yticks(fontsize=ytick_size)
    
    # Optional thousand separators on Y-axis
    if thous_sep:
        plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

    plt.grid()
    if legend_size:
        plt.legend(fontsize=legend_size)
    plt.show()