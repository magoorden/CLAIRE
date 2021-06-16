from pyswmm import Simulation, Nodes
import os.path
import csv

def extract_basin_wl (swmm_inputfile_dir, basin_id, time_step, csv_file_basename):
    """
    this function extracts the time sequential water level in the specified basin from swmm model

    requires: 
        swmm_inputfile_dir : swmm model path, str
        basin_id : basin id from swmm, str
        time_step: time interval in seconds, int
        csv_file_basename : csv file basename, str

    returns:
        time sequntial csv file
    """
    time_series = []
    water_depth = []

    with Simulation(swmm_inputfile_dir) as sim:
        su = Nodes(sim)[basin_id]
        sim.step_advance(time_step)
        for step in sim:
            time_series.append(sim.current_time)
            water_depth.append(su.depth)

    dirname = os.path.dirname(swmm_inputfile_dir)
    output_csv_file = os.path.join(dirname, csv_file_basename + "." + "csv")
    with open(output_csv_file, "w") as f:
        writer = csv.writer(f)
        for i, j in zip(time_series, water_depth):
            writer.writerow([i, j])

if __name__ == "__main__":
    swmm_inputfile_dir = r"C:\github\CLAIRE\swmm_models\test4_swmm_simulation_control.inp"
    basin_id = "SU1"
    time_step = 60
    csv_file_basename = "basin_wl"
    extract_basin_wl (swmm_inputfile_dir, basin_id, time_step, csv_file_basename)
    print ("procedure completed!")
