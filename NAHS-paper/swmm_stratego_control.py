from pyswmm import Simulation, Nodes, Links, RainGages, Subcatchments
import os.path
import csv
import re
import strategoutil as sutil
import datetime
import sys
import yaml
import weather_forecast_generation as weather


def swmm_control(swmm_inputfile, orifice_id, basin_id, time_step, csv_file_basename, controller,
                 period, horizon, rain_data_file, weather_forecast_path, uncertainty):
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
    # orifice_flow = []
    # basin_total_inflow = []
    # basin_total_outflow = []
    # basin_total_evaporation = []
    # overflow = []
    rain = []
    weather_forecast_low = []
    weather_forecast_high = []
    weather_forecast_int = []
    overflow_duration_basin1 = []
    overflow_duration_basin2 = []
    # subcatchment_total_rain = []
    # subcatchment_total_runoff = []
    # subcatchment_total_infiltration = []
    # subcatchment_total_evaporation = []

    with Simulation(swmm_inputfile) as sim:
        sys.stdout.write('\n')
        i = 0
        interval = sim.end_time - sim.start_time
        duration = interval.total_seconds() / 3600
        print_progress_bar(i, duration, "progress")
        su1 = Nodes(sim)[basin_id]
        su2 = Nodes(sim)['SU2']
        orifice = Links(sim)[orifice_id]
        # rg1 = RainGages(sim)["RG1"]
        ca = Subcatchments(sim)["S1"]
        sim.step_advance(time_step)
        current_time = sim.start_time

        orifice.target_setting = get_control_strategy(su1.depth, current_time, controller, period,
                                                      horizon, rain_data_file,
                                                      weather_forecast_path, uncertainty)
        orifice_settings.append(1.75*orifice.target_setting + 2)
        rain_low, rain_high, rain_int = get_weather_forecast_result(weather_forecast_path)
        weather_forecast_low.append(rain_low)
        weather_forecast_high.append(rain_high)
        weather_forecast_int.append(rain_int)
        time_series.append(sim.start_time)
        water_depth_basin1.append(su1.depth)
        water_depth_basin2.append(su2.depth)
        rain.append(0)
        total_precipitation = 0
        overflow_duration_basin1.append(0)
        overflow_duration_basin2.append(0)

        total_inflow = 0
        total_outflow = 0
        total_rainfall = 0
        for step in sim:
            current_time = sim.current_time
            time_series.append(current_time)
            water_depth_basin1.append(su1.depth)
            water_depth_basin2.append(su2.depth)
            rain.append(ca.statistics.get('precipitation') - total_precipitation)
            total_precipitation = ca.statistics.get('precipitation')
            overflow_duration_basin1.append(su1.statistics.get('flooding_duration'))
            overflow_duration_basin2.append(su2.statistics.get('flooding_duration'))

            i = i + 1
            print_progress_bar(i, duration, "progress")
            # Set the control parameter
            orifice.target_setting = get_control_strategy(su1.depth, current_time, controller,
                                                          period, horizon, rain_data_file,
                                                          weather_forecast_path, uncertainty)
            orifice_settings.append(1.75*orifice.target_setting + 2)
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
                         "rain", "forecast_low", "forecast_high", "forecast_int",
                         "overflow_duration_basin1", "overflow_duration_basin2"])
        for i, j, k, l, m, n, o, p, q, r in zip(time_series, water_depth_basin1, water_depth_basin2,
                                          orifice_settings, rain, weather_forecast_low,
                                          weather_forecast_high, weather_forecast_int,
                                          overflow_duration_basin1, overflow_duration_basin2):
            i = i.strftime('%Y-%m-%d %H:%M')
            writer.writerow([i, j, k, l, m, n, o, p, q, r])

def get_control_strategy(current_water_level, current_time, controller, period, horizon,
                         rain_data_file, weather_forecast_path, uncertainty):
    controller.controller.update_state({'w': current_water_level * 100}) #  Conversion from m to cm.
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
        with open(self.queryfile, "w") as f:
            line1 = f"strategy loaded = loadStrategy{{Pond.location, Rain.location," \
                    f"UrbanCatchment.location,Controller.location,CostFunction.location,Rain.i, " \
                    f"Rain.rainLoc,Rain.dryL,Rain.dryU,Rain.rainL,Rain.rainU}}->{{t,S_UC,w,o,c," \
                    f"Rain.d,Controller.x,rain,Open}}" \
                    f"(\"/home/martijn/Documents/CLAIRE/NAHS-paper/off-line_strategy.json\")"
            # line1 = f"strategy opt = minE (c + alpha * o) [<={horizon}*{period}]: <> (t=={final})\n"
            f.write(line1)
            f.write("\n")
            line2 = f"simulate 1 [<={period}+1] {{ {self.controller.get_var_names_as_string()} " \
                    f"}} under loaded\n"
            f.write(line2)

    def create_alternative_query_file(self, horizon, period, final):
        """
        Create an alternative query file in case the original query could not be satisfied by
        Stratego, i.e., it could not find a strategy. Current content will be overwritten.

        Overrides SafeMPCsetup.create_alternative_query_file().
        """
        with open(self.queryfile, "w") as f:
            line1 = f"strategy opt = minE (o) [<={horizon}*{period}]: <> (t=={final})\n"
            f.write(line1)
            f.write("\n")
            line2 = f"simulate 1 [<={period}+1] {{ {self.controller.get_var_names_as_string()} " \
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


def main():
    # First figure out where the swmm model file is located. This is also OS dependent.
    this_file = os.path.realpath(__file__)
    base_folder = os.path.dirname(this_file)
    swmm_inputfile = os.path.join(base_folder, "swmm_online.inp")
    assert (os.path.isfile(swmm_inputfile))

    # We found the model. Now we have to include the correct path to the rain data into the model.
    rain_data_file = "swmm_5061.dat"
    rain_data_file = os.path.join(base_folder, rain_data_file)
    insert_rain_data_file_path(swmm_inputfile, rain_data_file)

    # Finally we can specify other variables of swimm.
    orifice_id = "OR1"
    basin_id = "SU1"
    time_step = 60 * 60  # 60 seconds/min x 60 min/h -> 1 h
    swmm_results = "sim_online_offline_strategy_long"

    # Now we locate the Uppaal folder and files.
    model_template_path = os.path.join(base_folder, "pond_online.xml")
    query_file_path = os.path.join(base_folder, "pond_online_query.q")
    model_config_path = os.path.join(base_folder, "pond_online_config.yaml")
    learning_config_path = os.path.join(base_folder, "verifyta_online_config.yaml")
    weather_forecast_path = os.path.join(base_folder, "online_weather_forecast.csv")
    output_file_path = os.path.join(base_folder, "online_result-offline-strategy_long.txt")
    verifyta_command = "verifyta-stratego-9"
    insert_paths_in_uppaal_model(model_template_path, weather_forecast_path,
                                 os.path.join(base_folder, "libtable.so"))

    # Define uppaal model variables.
    action_variable = "Open"  # Name of the control variable.
    debug = True  # Whether to run in debug mode.
    period = 60  # Control period in time units (minutes).
    horizon = 1  # How many periods to compute strategy for.
    uncertainty = 0.1  # The uncertainty in the weather forecast generation.

    # Get model and learning config dictionaries from files.
    with open(model_config_path, "r") as yamlfile:
        model_cfg_dict = yaml.safe_load(yamlfile)
    with open(learning_config_path, "r") as yamlfile:
        learning_cfg_dict = yaml.safe_load(yamlfile)

    # Construct the MPC object.
    controller = MPCSetupPond(model_template_path, output_file_path, queryfile=query_file_path,
                              model_cfg_dict=model_cfg_dict,
                              learning_args=learning_cfg_dict,
                              verifyta_command=verifyta_command,
                              external_simulator=False,
                              action_variable=action_variable, debug=debug)

    swmm_control(swmm_inputfile, orifice_id, basin_id, time_step, swmm_results, controller,
                 period, horizon, rain_data_file, weather_forecast_path, uncertainty)
    print("\n")
    print("Procedure completed!")


if __name__ == "__main__":
    main()
