from pyswmm import Simulation, Links
import os.path
import re


def swmm_control(swmm_inputfile, orifice_id, time_step):
    orifice_settings = []

    with Simulation(swmm_inputfile) as sim:
        orifice = Links(sim)[orifice_id]
        sim.step_advance(time_step)

        orifice.target_setting = 0.2
        orifice_settings.append(orifice.target_setting)

        # Run the simulation.
        for step in sim:
            orifice_settings.append(orifice.target_setting)
            assert orifice_settings[-1] == orifice_settings[-2]  # Sanity check


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
    swmm_step_size = 30  # desired swmm step size in minutes.
    time_step = 60 * swmm_step_size  # should be in seconds, 60 seconds/min

    swmm_control(swmm_inputfile, orifice_id, time_step)
    print("procedure completed!")


if __name__ == "__main__":
    main()
