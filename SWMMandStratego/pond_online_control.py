import csv
import datetime
import strategoutil as sutil
import yaml


def create_weather_forecast(rain_data_file, weather_forecast_file, start_date, horizon,
                            uncertainty):
    """
    Create a weather forecast from historical rain data.
    """
    rain_data = read_rain_data(rain_data_file)
    weather_forecast = calculate_weather_intervals(rain_data, start_date, horizon, uncertainty)
    write_weather_forecast(weather_forecast_file, weather_forecast)


def read_rain_data(data_file):
    """
    Read the historical rain data from file.
    """
    with open(data_file, "r") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        rain_data = []
        for row in csv_reader:
            dt = datenum_to_datetime(float(row[0]))
            dt = round_datetime_to_minute(dt)
            rain_data.append([dt, float(row[1])])
    return rain_data


def datenum_to_datetime(datenum):
    """
    Convert Matlab datenum into Python datetime.

    Notes on day counting
    matlab: day one is 1 Jan 0000
    python: day one is 1 Jan 0001
    Hence a reduction of 366 days, for year 0 AD was a leap year
    """
    days = datenum % 1
    return datetime.datetime.fromordinal(int(datenum) - 366) + datetime.timedelta(days=days)


def round_datetime_to_minute(dt):
    """
    Rounds a datetime object to its nearest minute.
    """
    dt += datetime.timedelta(seconds=30)
    dt -= datetime.timedelta(seconds=dt.second,
                             microseconds=dt.microsecond)
    return dt


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
            f.write(line2.format(period, self.controller.print_var_names()))

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
            f.write(line2.format(period, self.controller.print_var_names()))

    def perform_at_start_iteration(self, controlperiod, horizon, duration, step, **kwargs):
        """
        Performs some customizable preprocessing steps at the start of each MPC iteration.

        Overrides SafeMPCsetup.perform_at_start_iteration().
        """
        current_date = kwargs["start_date"] + datetime.timedelta(hours=step)
        create_weather_forecast(kwargs["historical_rain_data_path"],
                                kwargs["weather_forecast_path"], current_date, horizon * 60,
                                kwargs["uncertainty"])


if __name__ == "__main__":
    # Define location of the relevant files and commands.
    model_template_path = "uppaal/pond_ADHS_external_weather_online.xml"
    query_file_path = "uppaal/pond_ADHS_query.q"
    model_config_path = "uppaal/model_config.yaml"
    learning_config_path = "uppaal/verifyta_config.yaml"
    historical_rain_data_path = "uppaal/Rain_Ts.txt"
    weather_forecast_path = "uppaal/weather_forecast.csv"
    output_file_path = "uppaal/result.txt"
    verifyta_command = "verifyta-stratego-8-7"

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
                              verifytacommand=verifyta_command, debug=debug)

    # Define the MPC parameters.
    period = 60  # Period in time units (minutes).
    horizon = 12  # How many periods to compute strategy for.
    duration = 72  # Duration of experiment in periods.
    start_date = datetime.datetime(year=2019, month=9, day=5)  # The day to start the MPC with.
    uncertainty = 0.1  # The uncertainty in the weather forecast generation.

    controller.run(period, horizon, duration, start_date=start_date,
                   historical_rain_data_path=historical_rain_data_path,
                   weather_forecast_path=weather_forecast_path, uncertainty=uncertainty)
