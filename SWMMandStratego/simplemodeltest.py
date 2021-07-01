import sys
from functools import cache

import pyswmm
import strategoutil as sutil
from pyswmm import Simulation, Nodes, Links
import os.path
import re
import yaml
import datetime
import csv


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


def run_swmm(swmm_inputfile, basin_id, orfice_id, time_step, output_csv_file, water_level,
             valve_opening, start_time, end_time):
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
        su.initial_depth = water_level
        orf = Links(sim)[orfice_id]
        orf.target_setting = valve_opening

        sim.start_time = start_time
        sim.end_time = end_time

        # TODO: Figure out what the difference is between the above options and using init_conditions
        # def init_conditions():
        #     su.initial_depth = water_level
        # sim.initial_conditions(init_conditions)

        sim.step_advance(time_step)
        for step in sim:
            time_series.append(sim.current_time)
            water_depth.append(su.depth)

    sys.stdout.flush()
    with open(output_csv_file, "w") as f:
        writer = csv.writer(f)
        for i, j in zip(time_series, water_depth):
            writer.writerow([i, j])

    return water_depth[len(water_depth) - 1]


def create_weather_forecast(rain_data_file, weather_forecast_file, start_date, horizon,
                            uncertainty):
    """
    Create a weather forecast from historical rain data.
    """
    # TODO: add caching
    rain_data = read_rain_data(rain_data_file)
    weather_forecast = calculate_weather_intervals(rain_data, start_date, horizon, uncertainty)
    write_weather_forecast(weather_forecast_file, weather_forecast)


@cache
def read_rain_data(data_file):
    """
    Read the historical rain data from file.
    """
    with open(data_file, "r") as f:
        lines = f.readlines()
        rain_data = []
        for line in lines:
            words = line.split()
            # In <name>.dat rain file, we have mm/dd/yyyy hh:mm:ss x.y per line.
            dt = datetime.datetime.strptime(words[0] + " " + words[1], "%m/%d/%Y %H:%M:%S")
            rain_data.append([dt, float(words[2]) / 60])
    return rain_data


def calculate_weather_intervals(rain_data, start_date, horizon, uncertainty):
    """
    Calculate lower and upper bounds of dry and rain intervals starting from a specified date and
    time. The horizon for creating these intervals are assumed to be given in minutes.
    """
    # Check start_date.
    assert horizon > 0
    assert start_date >= rain_data[0][0]
    assert start_date + datetime.timedelta(minutes=horizon) <= rain_data[len(rain_data) - 1][0]

    # Go in rain_data to start date and time. Remember that each line represents 1 minute.
    index = 0
    while rain_data[index][0] != start_date:
        index += 1

    # Initialize variables.
    raining = rain_data[index][1] > 0
    start_current_interval = index
    cumulative_rain = 0.0
    weather_intervals = []
    next_interval = []

    # If we start with rain, the first dry interval will be dummy values.
    if raining:
        next_interval.append(0)
        next_interval.append(0)

    while rain_data[index][0] <= start_date + datetime.timedelta(minutes=horizon):
        current_rain = rain_data[index][1]
        if raining and current_rain > 0:
            # It was raining and it is still raining.
            cumulative_rain += current_rain

        elif raining and current_rain == 0:
            # It was raining but it stopped raining.
            interval_duration = index - start_current_interval
            next_interval.append(int(round(interval_duration * (1 - uncertainty))))
            next_interval.append(int(round(interval_duration * (1 + uncertainty))))
            start_current_interval = index
            next_interval.append(cumulative_rain / interval_duration)
            weather_intervals.append(next_interval)
            next_interval = []
            raining = False

        elif not raining and current_rain == 0:
            # It was dry and it is still dry. Nothing special to do.
            pass

        elif not raining and current_rain > 0:
            # It was dry but it started raining.
            interval_duration = index - start_current_interval
            next_interval.append(int(round(interval_duration * (1 - uncertainty))))
            next_interval.append(int(round(interval_duration * (1 + uncertainty))))
            start_current_interval = index
            cumulative_rain = current_rain
            raining = True

        else:
            # We should not be here.
            raise RuntimeError("Rain data has unexpected values.")

        index += 1

    # Wrap up the last next_interval array.
    interval_duration = index - start_current_interval
    next_interval.append(int(round(interval_duration * (1 - uncertainty))))
    next_interval.append(int(round(interval_duration * (1 + uncertainty))))
    if raining:
        next_interval.append(cumulative_rain / interval_duration)
    else:
        next_interval.append(0)
        next_interval.append(0)
        next_interval.append(0)
    weather_intervals.append(next_interval)

    # Add two days of dry weather for safety in Uppaal Stratego.
    next_interval = [24 * 60, 24 * 60, 24 * 60, 24 * 60, 0]
    weather_intervals.append(next_interval)
    return weather_intervals


def write_weather_forecast(file, weather_forecast):
    """
    Writes the weather forecast to a csv file. Overwrites current content.
    """
    with open(file, "w") as f:
        weather_writer = csv.writer(f, delimiter=',', quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
        weather_writer.writerow(['#dryL', 'dryU', 'rainL', 'rainU', 'rain'])
        for row in weather_forecast:
            weather_writer.writerow(row)


class MPCSetupPond(sutil.SafeMPCSetup):
    def create_query_file(self, horizon, period, final):
        """
        Create the query file for each step of the pond model. Current
        content will be overwritten.

        Overrides SafeMPCsetup.create_query_file().
        """
        with open(self.queryfile, "w") as f:
            line1 = "strategy opt = minE (c) [<={}*{}]: <> (t=={} && o <= 0)\n"
            f.write(line1.format(horizon, period, final))
            f.write("\n")
            line2 = "simulate 1 [<={}+1] {{ {} }} under opt\n"
            f.write(line2.format(period, self.controller.get_var_names_as_string()))

    def create_alternative_query_file(self, horizon, period, final):
        """
        Create an alternative query file in case the original query could not be satisfied by
        Stratego, i.e., it could not find a strategy. Current content will be overwritten.

        Overrides SafeMPCsetup.create_alternative_query_file().
        """
        with open(self.queryfile, "w") as f:
            line1 = "strategy opt = minE (w) [<={}*{}]: <> (t=={})\n"
            f.write(line1.format(horizon, period, final))
            f.write("\n")
            line2 = "simulate 1 [<={}+1] {{ {} }} under opt\n"
            f.write(line2.format(period, self.controller.get_var_names_as_string()))

    def perform_at_start_iteration(self, controlperiod, horizon, duration, step, **kwargs):
        """
        Performs some customizable preprocessing steps at the start of each MPC iteration.

        Overrides SafeMPCsetup.perform_at_start_iteration().
        """
        current_date = kwargs["start_date"] + datetime.timedelta(minutes=step * controlperiod)
        create_weather_forecast(kwargs["historical_rain_data_path"],
                                kwargs["weather_forecast_path"], current_date,
                                horizon * controlperiod, kwargs["uncertainty"])

    def run_external_simulator(self, chosen_action, controlperiod, step, **kwargs):
        max_out_flow = 60.0 * 95000.0  # Max outflow [cm3/min], 95000 cm3/s = 95 l/s.
        start_datetime = kwargs["start_date"] + datetime.timedelta(minutes=step * controlperiod)
        end_datetime = kwargs["start_date"] + datetime.timedelta(minutes=(step + 1) * controlperiod + 1)

        # Run the SWMM model.
        new_water_level = run_swmm(swmm_inputfile,
                                   kwargs["basin_id"],
                                   kwargs["orfice_id"],
                                   kwargs["swmm_time_step"],
                                   kwargs["swmm_result_file"],
                                   self.controller.get_state("w") / 100,  # Unit controller = cm, unit SWMM = m.
                                   chosen_action / max_out_flow,
                                   start_datetime,
                                   end_datetime)

        # Get the new state.
        return {"w": new_water_level * 100, "t": self.controller.get_state("t") + controlperiod}


if __name__ == "__main__":
    # Assumed folder structure:
    # CLAIRE
    # - scripts
    # - swmm_models
    # - uppaal
    # - SWMMandStratego <- This file should be in this folder. TODO: maybe move it to scripts.

    # First figure out where the swmm model file is located. This is also OS dependent.
    this_file = os.path.realpath(__file__)
    base_folder = os.path.dirname(os.path.dirname(this_file))
    swmm_folder = "swmm_models"
    swmm_inputfile = os.path.join(base_folder, swmm_folder, "test4_swmm_simulation_control.inp")
    assert (os.path.isfile(swmm_inputfile))
    swmm_result_file = os.path.join(base_folder, swmm_folder, "swmm_results.csv")

    # We found the model. Now we have to include the correct path to the rain data into the model.
    rain_data_file = "swmm_5061.dat"  # Assumed to be in the same folder as the swmm model input file.
    rain_data_file = os.path.join(base_folder, swmm_folder, rain_data_file)
    insert_rain_data_file_path(swmm_inputfile, rain_data_file)

    # Now we locate the Uppaal folder and files.
    uppaal_folder_name = "uppaal"
    uppaal_folder = os.path.join(base_folder, uppaal_folder_name)
    model_template_path = os.path.join(uppaal_folder, "pond_ADHS_external_weather_online.xml")
    query_file_path = os.path.join(uppaal_folder, "pond_ADHS_query.q")
    model_config_path = os.path.join(uppaal_folder, "model_config.yaml")
    learning_config_path = os.path.join(uppaal_folder, "verifyta_config.yaml")
    weather_forecast_path = os.path.join(uppaal_folder, "weather_forecast.csv")
    output_file_path = os.path.join(uppaal_folder, "result.txt")
    verifyta_command = "verifyta-stratego-8-7"

    # Define model variables.
    external_simulator = True
    action_variable = "Qout"
    basin_id = "SU1"
    orfice_id = "OR1"
    swmm_time_step = 60  # Unit is seconds.

    # Whether to run in debug mode.
    debug = True

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
                              external_simulator=external_simulator,
                              action_variable=action_variable, debug=debug)

    # Define the MPC parameters.
    period = 60  # Period in time units (minutes).
    horizon = 12  # How many periods to compute strategy for.
    duration = 72  # Duration of experiment in periods.
    start_date = datetime.datetime(year=2019, month=9, day=5)  # The day to start the MPC with.
    uncertainty = 0.1  # The uncertainty in the weather forecast generation.

    controller.run(period, horizon, duration, start_date=start_date,
                   historical_rain_data_path=rain_data_file,
                   weather_forecast_path=weather_forecast_path, uncertainty=uncertainty,
                   basin_id=basin_id, orfice_id=orfice_id, swmm_time_step=swmm_time_step,
                   swmm_result_file=swmm_result_file)
