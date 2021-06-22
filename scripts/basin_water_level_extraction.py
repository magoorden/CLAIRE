import re

from pyswmm import Simulation, Nodes
import os.path
import csv


def extract_basin_wl(swmm_inputfile, basin_id, time_step, csv_file_basename):
    """
    Extracts the time sequential water level in the specified basin from swmm model and write it to
    a csv file.

    :param str swmm_inputfile: swmm model path
    :param str basin_id: basin id from swmm
    :param int time_step: time interval in seconds
    :param str csv_file_basename: csv file basename
    """
    time_series = []
    water_depth = []

    with Simulation(swmm_inputfile) as sim:
        su = Nodes(sim)[basin_id]
        sim.step_advance(time_step)
        for step in sim:
            time_series.append(sim.current_time)
            water_depth.append(su.depth)

    dirname = os.path.dirname(swmm_inputfile)
    output_csv_file = os.path.join(dirname, csv_file_basename + "." + "csv")
    with open(output_csv_file, "w") as f:
        writer = csv.writer(f)
        for i, j in zip(time_series, water_depth):
            writer.writerow([i, j])


def insert_rain_data_file_path(swmm_inputfile, rain_data_file):
    """
    Insert the provided rain data file path into the swmm model.

    :param str swmm_inputfile: swmm model path
    :param str rain_data_file: rain data file path
    """
    with open(swmm_inputfile, "r+") as f:
        file_content = f.read()
        new_line = "long_term_rainfallgauge5061 FILE \"" + rain_data_file + "\""
        file_content = re.sub(r"long_term_rainfallgauge5061 FILE \"[^\"]*\"", new_line,
                              file_content, count=1)
        f.seek(0)
        f.write(file_content)
        f.truncate()


if __name__ == "__main__":
    # First figure out where the swmm model file is located. This is also OS dependent.
    this_file = os.path.realpath(__file__)
    base_folder = os.path.dirname(os.path.dirname(this_file))
    swmm_folder = "swmm_models"
    swmm_inputfile = os.path.join(base_folder, swmm_folder, "test4_swmm_simulation_control.inp")
    assert(os.path.isfile(swmm_inputfile))

    # We found the model. Now we have to include the correct path to the rain data into the model.
    rain_data_file = "swmm_5061.dat" # Assumed to be in the same folder as the swmm model input file.
    rain_data_file = os.path.join(base_folder, swmm_folder, rain_data_file)
    insert_rain_data_file_path(swmm_inputfile, rain_data_file)
    
    # Finally we can specify other variables and start the swmm script.
    basin_id = "SU1"
    time_step = 60
    csv_file_basename = "basin_wl"
    extract_basin_wl(swmm_inputfile, basin_id, time_step, csv_file_basename)
    print("procedure completed!")
