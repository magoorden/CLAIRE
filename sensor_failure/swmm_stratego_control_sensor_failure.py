import torch
from pyswmm import Simulation, Nodes, Links, RainGages, Subcatchments
import os.path
import csv
import re
import strategoutil as sutil
import datetime
import sys
import yaml
import weather_forecast_generation as weather
from nn_code.models import Model
from nn_code.utils import DATA_LOADER
import pandas as pd
import numpy as np


def swmm_control(swmm_inputfile, orifice_id, basin_id, time_step, csv_file_basename, controller,
                 period, horizon, rain_data_file, weather_forecast_path, uncertainty,
                 neural_network_data_loader, neural_network_model, sensor_failure_start,
                 sensor_failure_duration):
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
    water_depth_basin1 = []
    water_depth_basin2 = []
    orifice_settings = []
    water_depth_stream1_reported = []
    water_depth_stream1_true = []
    nn_active = []
    rain = []
    weather_forecast_low = []
    weather_forecast_high = []
    weather_forecast_int = []

    # We should have at least a single reading of the initial stream water level.
    assert(sensor_failure_start > 0)
    assert(sensor_failure_duration > 0)

    with Simulation(swmm_inputfile) as sim:
        # Start the simulation.
        sys.stdout.write('\n')
        i = 0
        interval = sim.end_time - sim.start_time
        duration = interval.total_seconds() / time_step
        print_progress_bar(i, duration, "progress")
        su1 = Nodes(sim)[basin_id]
        su2 = Nodes(sim)['SU2']
        orifice = Links(sim)[orifice_id]
        stream = Nodes(sim)["J2"]
        # rg1 = RainGages(sim)["RG1"]
        ca = Subcatchments(sim)["S1"]
        sim.step_advance(time_step)
        current_time = sim.start_time

        water_depth_stream1_reported.append(stream.depth)
        water_depth_stream1_true.append(stream.depth)
        last_stream_level = water_depth_stream1_reported[-1]

        orifice.target_setting = get_control_strategy(su1.depth, stream.depth, current_time, controller, period,
                                                      horizon, rain_data_file,
                                                      weather_forecast_path, uncertainty)
        orifice_settings.append(1.75 * orifice.target_setting)
        rain_low, rain_high, rain_int = get_weather_forecast_result(weather_forecast_path)
        weather_forecast_low.append(rain_low)
        weather_forecast_high.append(rain_high)
        weather_forecast_int.append(rain_int)
        time_series.append(sim.start_time)
        water_depth_basin1.append(su1.depth)
        water_depth_basin2.append(su2.depth)
        nn_active.append(0)
        rain.append(0)  # Obtaining rain is only possible after the first simulation step.
        total_precipitation = 0

        total_inflow = 0
        total_outflow = 0
        total_rainfall = 0

        # Run the simulation.
        for step in sim:
            i = i + 1
            print_progress_bar(i, duration, "progress")

            current_time = sim.current_time
            time_series.append(current_time)
            water_depth_basin1.append(su1.depth)
            water_depth_basin2.append(su2.depth)
            rain.append(ca.statistics.get('precipitation') - total_precipitation)
            total_precipitation = ca.statistics.get('precipitation')

            sensor_out = sensor_failure_start < i < sensor_failure_start + sensor_failure_duration
            if sensor_out:
                j = i - sensor_failure_start  # Remember that step size of nn is 30 min.
                w_pred, w_std = get_estimated_stream_level(neural_network_model, neural_network_data_loader, rain[-j:], last_stream_level, j)
                stream_level = w_pred[-1][0][0] / 100  # SWMM is in m, while NN model is in cm.
                nn_active.append(1)
            else:
                stream_level = stream.depth
                last_stream_level = stream.depth * 100  # SWMM is in m, while NN model is in cm.
                nn_active.append(0)


            water_depth_stream1_reported.append(stream_level)
            water_depth_stream1_true.append(stream.depth)

            # Set the control parameter in case we can switch.
            if i % (period * 60 / time_step) == 0:
                orifice.target_setting = get_control_strategy(su1.depth, stream_level, current_time, controller,
                                                              period, horizon, rain_data_file,
                                                              weather_forecast_path, uncertainty)
            orifice_settings.append(1.75 * orifice.target_setting)
            if i > 2 and i % (period * 60 / time_step) != 0:
                assert orifice_settings[-1] == orifice_settings[-2]  # Sanity check where time step != control period
            rain_low, rain_high, rain_int = get_weather_forecast_result(weather_forecast_path)
            weather_forecast_low.append(rain_low)
            weather_forecast_high.append(rain_high)
            weather_forecast_int.append(rain_int)

            # orifice_flow.append(orifice.flow)
            # rain.append(rg1.rainfall)
            # total_inflow = total_inflow + su.total_inflow
            # basin_total_inflow.append(total_inflow)
            # overflow.append(su.statistics.get('flooding_volume'))
            # total_outflow = total_outflow + su.total_outflow
            # basin_total_outflow.append(total_outflow)
            # basin_total_evaporation.append(su.storage_statistics.get('evap_loss'))
            # total_rainfall = total_rainfall + ca.rainfall
            # subcatchment_total_rain.append(total_rainfall)
            # subcatchment_total_runoff.append(ca.statistics.get('runoff'))
            # subcatchment_total_infiltration.append(ca.statistics.get('infiltration'))
            # subcatchment_total_evaporation.append(ca.statistics.get('evaporation'))

    i = i + 1
    print_progress_bar(i, duration, "progress")
    dirname = os.path.dirname(swmm_inputfile)
    output_csv_file = os.path.join(dirname, csv_file_basename + "." + "csv")
    with open(output_csv_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "water_depth_basin1", "water_depth_basin2", "orifice_setting",
                         "rain", "forecast_low", "forecast_high", "forecast_int", "water_depth_stream1_reported",
                         "water_depth_stream1_true", "nn_active"])
        for i, j, k, l, m, n, o, p, q, r, s in zip(time_series, water_depth_basin1, water_depth_basin2,
                                          orifice_settings, rain, weather_forecast_low,
                                          weather_forecast_high, weather_forecast_int, water_depth_stream1_reported,
                                          water_depth_stream1_true, nn_active):
            i = i.strftime('%Y-%m-%d %H:%M')
            writer.writerow([i, j, k, l, m, n, o, p, q, r, s])


def get_estimated_stream_level(model, data_loader, rain_values, last_stream_level, num_steps):
    """
    Get an estimation of the stream water level from the neural network.

    :param model: The neural network model.
    :param data_loader: The data loader for this specific neural network such that inputs have
    correct format.
    :param rain_values: The rain intensity observations during the period of prediction.
    :param last_stream_level: Last observed (true) steam water level.
    :param num_steps: The number of prediction steps from the last observed stream water level.
    Each step is 30 minutes.
    :return: An array of stream water level predictions and an array of standard deviation errors
    on these predictions.
    """
    gauges_features = []
    for rain in rain_values:
        gauges_features.append(data_loader.get_feat_([rain]*7))
    g_input = torch.stack(gauges_features)

    MC_NUM = 10  # num of Monte carlo simulation
    return model.predict_(torch.Tensor([last_stream_level]), g_input, step=num_steps + 1, mc_num=MC_NUM)

def get_control_strategy(current_pond_level, current_stream_level, current_time, controller, period, horizon,
                         rain_data_file, weather_forecast_path, uncertainty):
    controller.controller.update_state({'w': current_pond_level * 100, 'st_w': current_stream_level * 100})  # Conversion from m to cm.
    control_setting = controller.run_single(period, horizon, start_date=current_time,
                                            historical_rain_data_path=rain_data_file,
                                            weather_forecast_path=weather_forecast_path,
                                            uncertainty=uncertainty)

    return control_setting


def get_weather_forecast_result(weather_forecast_path):
    with open(weather_forecast_path, "r") as f:
        weather_forecast = csv.reader(f, delimiter=',', quotechar='"')
        headers = next(weather_forecast)
        first_data = next(weather_forecast)

        return int(first_data[0]), int(first_data[1]), float(first_data[4])


def print_progress_bar(i, max, post_text):
    """
    Print a progress bar to sys.stdout.

    Subsequent calls will override the previous progress bar (given that nothing else has been
    written to sys.stdout).

    From `<https://stackoverflow.com/a/58602365>`_.

    :param i: The number of steps already completed.
    :type i: int
    :param max: The maximum number of steps for process to be completed.
    :type max: int
    :param post_text: The text to display after the progress bar.
    :type post_text: str
    """
    n_bar = 20  # Size of progress bar.
    j = i / max
    sys.stdout.write('\r')
    sys.stdout.write(f"[{'=' * int(n_bar * j):{n_bar}s}] {int(100 * j)}%  {post_text}")
    sys.stdout.flush()


class MPCSetupPond(sutil.SafeMPCSetup):
    def create_query_file(self, horizon, period, final):
        """
        Create the query file for each step of the pond model. Current
        content will be overwritten.

        Overrides SafeMPCsetup.create_query_file().
        """
        with open(self.query_file, "w") as f:
            line1 = f"strategy opt = minE (c) [<={horizon}*{period}]: <> (t=={final} && o <= 0)\n"
            f.write(line1)
            f.write("\n")
            line2 = f"simulate [<={period}+1;1] {{ {self.controller.get_var_names_as_string()} " \
                    f"}} under opt\n"
            f.write(line2)

    def create_alternative_query_file(self, horizon, period, final):
        """
        Create an alternative query file in case the original query could not be satisfied by
        Stratego, i.e., it could not find a strategy. Current content will be overwritten.

        Overrides SafeMPCsetup.create_alternative_query_file().
        """
        with open(self.query_file, "w") as f:
            line1 = f"strategy opt = minE (wmax) [<={horizon}*{period}]: <> (t=={final})\n"
            f.write(line1)
            f.write("\n")
            line2 = f"simulate [<={period}+1;1] {{ {self.controller.get_var_names_as_string()} " \
                    f"}} under opt\n"
            f.write(line2)

    def perform_at_start_iteration(self, controlperiod, horizon, duration, step, **kwargs):
        """
        Performs some customizable preprocessing steps at the start of each MPC iteration.

        Overrides SafeMPCsetup.perform_at_start_iteration().
        """
        current_date = kwargs["start_date"] + datetime.timedelta(hours=step)
        weather.create_weather_forecast(kwargs["historical_rain_data_path"],
                                        kwargs["weather_forecast_path"], current_date,
                                        horizon * controlperiod, kwargs["uncertainty"])


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


def insert_paths_in_uppaal_model(uppaal_model, weather_forecast_path, libtable_path):
    """
    Insert the provided weather forecast path into the uppaal model.

    :param str uppaal_model: uppaal model path
    :param str weather_forecast_path: weather forecast path
    :param str libtable_path: libtable.so path
    """
    with open(uppaal_model, "r+") as f:
        file_content = f.read()
        new_line = "const int file_id = table_read_csv(\"" + weather_forecast_path + "\""
        file_content = re.sub(r"const int file_id = table_read_csv\(\"[^\"]*\"", new_line,
                              file_content, count=1)
        new_line = "import \"" + libtable_path + "\""
        file_content = re.sub(r"import \"[^\"]*\"", new_line, file_content, count=1)
        f.seek(0)
        f.write(file_content)
        f.truncate()


def initializeNeuralNetworkDataLoader(hist_data_file):
    df = pd.read_csv(hist_data_file, sep=",", skiprows=2, on_bad_lines='skip',
                     header=None)
    w = np.array(df.iloc[:, 4]) * 100  # water level in basin
    g = np.array(df.iloc[:, 6])[:, None]
    g_a = np.array_split(g, len(w))  # split the gauge values into the same number of water levels
    g_a = np.asarray([np.sum(gg, axis=0) for gg in g_a])  # sum gauges values within each time slots
    data_loader = DATA_LOADER(g_a, w, samp_rate=6, feat_type="hist_indiv", hist_step=6,
                              time_delay=0)
    data_loader.get_feats_()
    return data_loader


def main():
    # First figure out where the swmm model file is located. This is also OS dependent.
    # We assume that everything is in the same folder for this experiment.
    this_file = os.path.realpath(__file__)
    base_folder = os.path.dirname(this_file)
    swmm_inputfile = os.path.join(base_folder, "swmm_model.inp")
    assert (os.path.isfile(swmm_inputfile))

    # We found the model. Now we have to include the correct path to the rain data into the model.
    rain_data_file = "swmm_5061_small.dat"
    rain_data_file = os.path.join(base_folder, rain_data_file)
    insert_rain_data_file_path(swmm_inputfile, rain_data_file)

    # Finally we can specify other variables of swimm.
    orifice_id = "OR1"
    basin_id = "SU1"
    swmm_step_size = 30  # desired swmm step size in minutes.
    time_step = 60 * swmm_step_size  # should be in seconds, 60 seconds/min
    swmm_results = "swmm_results"

    # Now we locate the Uppaal folder and files.
    model_template_path = os.path.join(base_folder, "pond_stream.xml")
    query_file_path = os.path.join(base_folder, "pond_query.q")
    model_config_path = os.path.join(base_folder, "pond_config.yaml")
    learning_config_path = os.path.join(base_folder, "verifyta_config.yaml")
    weather_forecast_path = os.path.join(base_folder, "weather_forecast.csv")
    output_file_path = os.path.join(base_folder, "results.txt")
    verifyta_command = "verifyta-5-rc4"
    insert_paths_in_uppaal_model(model_template_path, weather_forecast_path,
                                 os.path.join(base_folder, "libtable.dylib"))

    # Define uppaal model variables.
    action_variable = "Open"  # Name of the control variable.
    debug = True  # Whether to run in debug mode.
    period = 60  # Control period in time units (minutes).
    horizon = 6  # How many periods to compute strategy for.
    uncertainty = 0.1  # The uncertainty in the weather forecast generation.

    # Locate the neural network folder and files.
    neural_network_folder = os.path.join(base_folder, "nn_code")
    hist_data_file = os.path.join(neural_network_folder, "swmm_demo3_temp_results.csv")
    neural_network_model_file = os.path.join(neural_network_folder, "joint_swmm_hist_indiv.pt")
    sensor_failure_time = 72  # Expressed in the number of SWMM time steps.
    sensor_failure_duration = 12  # Expressed in the number of SWMM time steps.

    # Get model and learning config dictionaries from files.
    with open(model_config_path, "r") as yamlfile:
        model_cfg_dict = yaml.safe_load(yamlfile)
    with open(learning_config_path, "r") as yamlfile:
        learning_cfg_dict = yaml.safe_load(yamlfile)

    # Construct the MPC object.
    controller = MPCSetupPond(model_template_path, output_file_path, query_file=query_file_path,
                              model_cfg_dict=model_cfg_dict,
                              learning_args=learning_cfg_dict,
                              verifyta_command=verifyta_command,
                              external_simulator=False,
                              action_variable=action_variable, debug=debug)

    # Initialize the neural network data loader.
    neural_network_data_loader = initializeNeuralNetworkDataLoader(hist_data_file)
    neural_network_model = Model(FEATURE_TYPE="hist_indiv", INPUT_DIM=7, MODEL_TYPE="joint",
                                 SOLVER="rk4", PATH=neural_network_model_file)

    swmm_control(swmm_inputfile, orifice_id, basin_id, time_step, swmm_results, controller,
                 period, horizon, rain_data_file, weather_forecast_path, uncertainty,
                 neural_network_data_loader, neural_network_model, sensor_failure_time,
                 sensor_failure_duration)
    print("procedure completed!")


if __name__ == "__main__":
    main()
