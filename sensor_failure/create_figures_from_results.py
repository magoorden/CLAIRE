import csv
import matplotlib as mpl
import matplotlib.pyplot as plt
from collections import deque
import dateutil
mpl.use('macosx')

if __name__ == "__main__":
    results_path = "swmm_results.csv"
    max_water_level = 1.0

    # Get data from file to initialize figures.
    with open(results_path, "r") as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')

        # Get first row.
        row = next(reader)
        start_time = row["time"]

        # Get last row.
        dd = deque(reader, maxlen=1)
        last_row = dd.pop()
        end_time = last_row["time"]

    # Prepare the demonstration figures.
    plt.ion()
    plt.rc('font', size=16)
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, gridspec_kw={'height_ratios': [5, 1], 'width_ratios': [1, 2]})
    fig.suptitle('ONLINE CONTROL OF A STORMWATER POND USING UPPAAL', fontsize=30)
    # Axes for current pond water level.
    # ax1 = fig.add_subplot(2, 2, 1)
    ax1.set_xlabel('')
    ax1.set_ylabel('Water level [m]')
    ax1.set_title("Stream water level at " + start_time)
    ax1.set_xlim(0, 1)
    ax1.set_xticks([])
    ax1.set_ylim(0, max_water_level-0.7)

    # Axes for pond water level history.
    # ax2 = fig.add_subplot(2, 2, 2)
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Water level [m]', color='blue')
    ax2.set_title('History of water level')
    ax2.set_xlim(dateutil.parser.parse(start_time), dateutil.parser.parse(end_time) + dateutil.relativedelta.relativedelta(hours=+1))
    plt.setp(ax2.get_xticklabels(), rotation=30,
             ha='right')  # autofmt_xdate removes all other x_axes

    ax2.set_ylim(0, max_water_level-0.7)
    ax2.tick_params(axis='y', colors='blue')
    ax2.spines['left'].set_color('blue')

    ax22 = ax2.twinx()  # Instantiate a second axes that shares the same x-axis
    ax22.set_ylabel('Rainfall [mm]', color='black')
    ax22.set_ylim(20, 0)
    ax22.tick_params(axis='y', colors='black')
    # fig.tight_layout()  # Otherwise the right y-label is slightly clipped

    # Axes for weather forecast.
    # ax3 = fig.add_subplot(2, 1, 2)
    ax3.axis('off')
    text = ax3.text(0.1, -0.2, '', size=22)

    ax4.axis('off')
    plt.show()

    # Plot dummy data so we have the line objects.
    points, = ax1.fill([0, 1, 1, 0], [0, 0, 0, 0], 'b')
    # level_basin1_line, = ax2.plot([], [], 'b')
    level_stream1_rep_line, = ax2.plot([], [], 'b')
    level_stream1_true_line, = ax2.plot([], [], '--r')
    orifice_line, = ax2.step([], [], 'g')
    nn_active_line, = ax2.step([], [], '--k')
    rain_line, = ax22.step([], [], 'k')
    ax2.legend([rain_line, orifice_line, level_stream1_true_line, level_stream1_rep_line, nn_active_line],
               ['Rain precipitation', 'Orifice control with Uppaal', 'Water level stream true',
                'Water level stream reported', 'neural network active'],
               #loc='center right')
               loc=(0.65, 0.7))
    plt.pause(0.01)
    plt.pause(5)  # So you can rescale the fig before the first data is being plotted.

    # Generate demonstration figure.
    time_series = []
    water_depth_stream1_rep = []
    water_depth_stream1_true = []
    rain_series = []
    orifice_series = []
    nn_active = []

    with open(results_path, "r") as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')

        for row in reader:
            # Collect the new data.
            time_series.append(dateutil.parser.parse(row["time"]))
            water_depth_stream1_rep.append(float(row["water_depth_stream1_reported"]))
            water_depth_stream1_true.append(float(row["water_depth_stream1_true"]))
            rain_series.append(float(row["rain"]))
            # orifice_series.append((float(row["orifice_setting"]) - 2) / 10 + 0.1)  # Old data was generated with offset hard coded.
            orifice_series.append(float(row["orifice_setting"]) / 30 + 0.2)
            nn_active.append(float(row["nn_active"])-0.1)

            # Plot the actual data
            ax1.set_title("Water level at " + row["time"])
            points.set_xy([[0, 0], [1, 0], [1, water_depth_stream1_rep[-1]], [0, water_depth_stream1_rep[-1]]])
            level_stream1_rep_line.set_data(time_series, water_depth_stream1_rep)
            level_stream1_true_line.set_data(time_series, water_depth_stream1_true)
            rain_line.set_data(time_series, rain_series)
            orifice_line.set_data(time_series, orifice_series)
            nn_active_line.set_data(time_series, nn_active)
            text.set_text(f'Weather forecast:\n- Next rainfall starts between '
                          f'{row["forecast_low"]} and {row["forecast_high"]} minutes.\n- The rain '
                          f'intensity will be approximately {60 * float(row["forecast_int"]):.2f} '
                          f'mm/h.\n\nChosen control setting by Uppaal: '
                          f'{float(row["orifice_setting"]):.2f}')
            plt.pause(0.01)

    plt.pause(5)
