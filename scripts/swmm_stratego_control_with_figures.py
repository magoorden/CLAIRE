from pyswmm import Simulation, Nodes, Links, RainGages, Subcatchments
import os.path
import csv
import re
import strategoutil as sutil
import datetime
import sys
import yaml
import weather_forecast_generation as weather
import matplotlib.pyplot as plt


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
        time_series.append(sim.start_time)
        water_depth_basin1.append(su1.depth)
        water_depth_basin2.append(su2.depth)
        rain.append(0)
        total_precipitation = 0

        plt.ion()
        plt.rc('font', size=16)
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, gridspec_kw={'height_ratios': [5, 1]})
        # Axes for current pond water level.
        # ax1 = fig.add_subplot(2, 2, 1)
        ax1.set_xlabel('')
        ax1.set_ylabel('Water level [m]')
        ax1.set_title("Water level at " + current_time.strftime('%Y-%m-%d %H:%M'))
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, su1.full_depth)

        # Axes for pond water level history.
        #ax2 = fig.add_subplot(2, 2, 2)
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Water level [m]', color='blue')
        ax2.set_title('History of water level')
        ax2.set_xlim(sim.start_time, sim.end_time)
        plt.setp(ax2.get_xticklabels(), rotation=30, ha='right')  # autofmt_xdate removes all other x_axes

        ax2.set_ylim(0, su1.full_depth + 2)
        ax2.tick_params(axis='y', colors='blue')
        ax2.spines['left'].set_color('blue')

        ax22 = ax2.twinx()  # Instantiate a second axes that shares the same x-axis
        ax22.set_ylabel('Rainfall [mm]', color='black')
        ax22.set_ylim(5, 0)
        ax22.tick_params(axis='y', colors='black')
        #fig.tight_layout()  # Otherwise the right y-label is slightly clipped

        # Axes for weather forecast.
        #ax3 = fig.add_subplot(2, 1, 2)
        ax3.axis('off')
        rain_low, rain_high, rain_int = get_weather_forecast_result(weather_forecast_path)
        text = ax3.text(0.1, 0.05, f'Weather forecast:\n- Next rainfall starts between {rain_low} '
                                   f'and {rain_high} minutes.\n- The rain intensity will be '
                                   f'approximately {60*rain_int:.2f} mm/h.\n\nChosen control '
                                   f'setting: {1.75*orifice.target_setting:.2f}', size=22)
        weather_forecast_low.append(rain_low)
        weather_forecast_high.append(rain_high)
        weather_forecast_int.append(rain_int)

        ax4.axis('off')
        plt.show()
        plt.pause(10)  # So you can rescale the fig before the first data is being plotted.

        # Plot the actual data.
        points, = ax1.fill([0, 1, 1, 0], [0, 0, su1.depth, su1.depth], 'b')
        level_basin1_line, = ax2.plot(time_series, water_depth_basin1, 'b')
        level_basin2_line, = ax2.plot(time_series, water_depth_basin2, '--r')
        orifice_line, = ax2.plot(time_series, orifice_settings, 'g')
        rain_line, = ax22.step(time_series, rain, 'k')
        ax2.legend([level_basin1_line, level_basin2_line], ['Optimal control', 'static control'],
                   loc='center right')
        plt.pause(0.01)

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
            ax1.set_title(basin_id + ": " + current_time.strftime('%Y-%m-%d %H:%M'))
            points.set_xy([[0, 0], [1, 0], [1, su1.depth], [0, su1.depth]])
            level_basin1_line.set_data(time_series, water_depth_basin1)
            level_basin2_line.set_data(time_series, water_depth_basin2)
            rain_line.set_data(time_series, rain)
            plt.pause(0.1)
            # ax.fill([0, 1, 1, 0], [0, 0, su.depth, su.depth], 'b')

            i = i + 1
            print_progress_bar(i, duration, "progress")
            # Set the control parameter
            orifice.target_setting = get_control_strategy(su1.depth, current_time, controller,
                                                          period, horizon, rain_data_file,
                                                          weather_forecast_path, uncertainty)
            orifice_settings.append(1.75*orifice.target_setting + 2)
            orifice_line.set_data(time_series, orifice_settings)
            rain_low, rain_high, rain_int = get_weather_forecast_result(weather_forecast_path)
            text.set_text(f'Weather forecast:\n- Next rainfall starts between {rain_low} and '
                          f'{rain_high} minutes.\n- The rain intensity will be approximately '
                          f'{60*rain_int:.2f} mm/h.\n\nChosen control setting: '
                          f'{1.75*orifice.target_setting:.2f}')
            weather_forecast_low.append(rain_low)
            weather_forecast_high.append(rain_high)
            weather_forecast_int.append(rain_int)
            plt.pause(0.1)

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
    plt.pause(5)
    dirname = os.path.dirname(swmm_inputfile)
    output_csv_file = os.path.join(dirname, csv_file_basename + "." + "csv")
    with open(output_csv_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "water_depth_basin1", "water_depth_basin2", "orifice_setting",
                         "rain", "forecast_low", "forecast_high", "forecast_int"])
        for i, j, k, l, m, n, o, p in zip(time_series, water_depth_basin1, water_depth_basin2,
                                          orifice_settings, rain, weather_forecast_low,
                                          weather_forecast_high, weather_forecast_int):
            i = i.strftime('%Y-%m-%d %H:%M')
            writer.writerow([i, j, k, l, m, n, o, p])


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
        with open(self.query_file, "w") as f:
            line1 = f"strategy opt = minE (c) [<={horizon}*{period}]: <> (t=={final} && o <= 0)\n"
            f.write(line1)
            f.write("\n")
            line2 = f"simulate 1 [<={period}+1] {{ {self.controller.get_var_names_as_string()} " \
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
    base_folder = os.path.dirname(os.path.dirname(this_file))
    swmm_folder = "swmm_models"
    swmm_inputfile = os.path.join(base_folder, swmm_folder, "swmm_demo3.inp")
    assert (os.path.isfile(swmm_inputfile))

    # We found the model. Now we have to include the correct path to the rain data into the model.
    rain_data_file = "swmm_5061.dat"  # Assumed to be in the same folder as the swmm model input file.
    rain_data_file = os.path.join(base_folder, swmm_folder, rain_data_file)
    insert_rain_data_file_path(swmm_inputfile, rain_data_file)

    # Finally we can specify other variables of swimm.
    orifice_id = "OR1"
    basin_id = "SU1"
    time_step = 60 * 60  # 60 seconds/min x 60 min/h -> 1 h
    swmm_results = "swmm_demo3_results"

    # Now we locate the Uppaal folder and files.
    uppaal_folder_name = "uppaal"
    uppaal_folder = os.path.join(base_folder, uppaal_folder_name)
    model_template_path = os.path.join(uppaal_folder, "pond.xml")
    query_file_path = os.path.join(uppaal_folder, "pond_demo3_query.q")
    model_config_path = os.path.join(uppaal_folder, "pond_demo3_config.yaml")
    learning_config_path = os.path.join(uppaal_folder, "verifyta_demo3_config.yaml")
    weather_forecast_path = os.path.join(uppaal_folder, "demo3_weather_forecast.csv")
    output_file_path = os.path.join(uppaal_folder, "demo3_result.txt")
    verifyta_command = "verifyta-stratego-8-11"
    insert_paths_in_uppaal_model(model_template_path, weather_forecast_path,
                                 os.path.join(uppaal_folder, "libtable.so"))

    # Define uppaal model variables.
    action_variable = "Open"  # Name of the control variable.
    debug = True  # Whether to run in debug mode.
    period = 60  # Control period in time units (minutes).
    horizon = 18  # How many periods to compute strategy for.
    uncertainty = 0.1  # The uncertainty in the weather forecast generation.

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

    swmm_control(swmm_inputfile, orifice_id, basin_id, time_step, swmm_results, controller,
                 period, horizon, rain_data_file, weather_forecast_path, uncertainty)
    print("procedure completed!")


if __name__ == "__main__":
    main()
