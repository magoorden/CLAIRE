from pyswmm import Simulation, Nodes, Links, RainGages, Subcatchments
import os.path
import csv
import re


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
        col 2. the orifice flow (discharge) changes when implemented control strategy, cubic meter per second
    """
    time_series = []
    water_depth = []
    orifice_flow = []
    basin_total_inflow = []
    basin_total_outflow = []
    overflow = []
    rain = []
    subcatchment_total_rain = []
    subcatchment_total_runoff = []
    subcatchment_total_infiltration = []

    with Simulation(swmm_inputfile) as sim:
        su = Nodes(sim)[basin_id]
        orifice = Links(sim)[orifice_id]
        rg1 = RainGages(sim)["RG1"]
        ca = Subcatchments(sim)["S1"]

        sim.step_advance(time_step)
        orifice.target_setting = opening_settings # set the control parameter
        total_inflow = 0
        total_outflow = 0
        total_rainfall = 0
        for step in sim:
            time_series.append(sim.current_time)
            water_depth.append(su.depth)
            orifice_flow.append(orifice.flow)
            rain.append(rg1.rainfall)
            total_inflow = total_inflow + su.total_inflow
            basin_total_inflow.append(total_inflow)
            overflow.append(su.statistics.get('flooding_volume'))
            total_outflow = total_outflow + su.total_outflow
            basin_total_outflow.append(total_outflow)
            total_rainfall = total_rainfall + ca.rainfall
            subcatchment_total_rain.append(total_rainfall)
            subcatchment_total_runoff.append(ca.statistics.get('runoff'))
            subcatchment_total_infiltration.append(ca.statistics.get('infiltration'))

    dirname = os.path.dirname(swmm_inputfile)
    output_csv_file = os.path.join(dirname, csv_file_basename + "." + "csv")
    with open(output_csv_file, "w") as f:
        writer = csv.writer(f)
        for i, j, k, l, m, n, o, p, q, r in zip(time_series, water_depth, orifice_flow, rain,
                                                basin_total_inflow, basin_total_outflow, overflow,
                                                subcatchment_total_rain, subcatchment_total_runoff,
                                                subcatchment_total_infiltration):
            i = i.strftime('%Y-%m-%d %H:%M')
            writer.writerow([i, j, k, l, m, n, o, p, q, r])


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
    swmm_inputfile = os.path.join(base_folder, swmm_folder, "test4_swmm_simulation_control_catchment_storage_removed.inp")
    assert (os.path.isfile(swmm_inputfile))

    # We found the model. Now we have to include the correct path to the rain data into the model.
    rain_data_file = "swmm_5061.dat"  # Assumed to be in the same folder as the swmm model input file.
    rain_data_file = os.path.join(base_folder, swmm_folder, rain_data_file)
    insert_rain_data_file_path(swmm_inputfile, rain_data_file)

    # Finally we can specify other variables and start the swmm script.
    orifice_id = "OR1"
    opening_settings = 1.0 # 50% opening
    basin_id = "SU1"
    time_step = 60
    csv_file_basename = "swmm_results_catchment_removed"

    swmm_control(swmm_inputfile, orifice_id, opening_settings, basin_id, time_step, csv_file_basename)
    print("procedure completed!")


    

