from pyswmm import Simulation, Nodes, Links
import os.path
import csv

def swmm_control(swmm_inputfile, orifice_id, opening_settings, basin_id, time_step, csv_file_basename):
    """
    Implement the control strategy from uppal stratego to swmm
    requires:
        swmm_inputfile: path
        orifice_id: string
        open_settings: percentage of orifice opening, float, from 0 to 1
        basin_id: string, upstream basin ID
        time_step: float
        csv_file_basename: path

    returns:
        one csv files with three columns:
        col 0. time 
        col 1. the upstream pond water level changes when implemented control strategy, meter above the bottom elevation of basin
        col 2. the orifice flow (dischagre) changes when implemented control strategy, cubic meter per second
    """
    time_series = []
    water_depth = []
    orifice_flow = []

    with Simulation(swmm_inputfile) as sim:
        su = Nodes(sim)[basin_id]
        orifice = Links(sim)[orifice_id]

        sim.step_advance(time_step)
        orifice.target_setting = opening_settings # set the control parameter
        for step in sim:
            time_series.append(sim.current_time)
            water_depth.append(su.depth)
            orifice_flow.append(orifice.flow)
    
    dirname = os.path.dirname(swmm_inputfile)
    output_csv_file = os.path.join(dirname, csv_file_basename + "." + "csv")
    with open(output_csv_file, "w") as f:
        writer = csv.writer(f)
        for i, j, k in zip(time_series, water_depth, orifice_flow):
            writer.writerow([i, j, k])

if __name__ == "__main__":
    # First figure out where the swmm model file is located. This is also OS dependent.
    swmm_inputfile = r"C:\github\CLAIRE\swmm_models\test4_swmm_simulation_control_catchment_storage.inp"

   # Finally we can specify other variables and start the swmm script.
    orifice_id = "OR1"
    opening_settings = 0.5 # 50% opening
    basin_id = "SU1"
    time_step = 60
    csv_file_basename = "swmm_results_after_control_implemented"

    swmm_control(swmm_inputfile, orifice_id, opening_settings, basin_id, time_step, csv_file_basename)
    print("procedure completed!")


    

