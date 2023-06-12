import datetime


def process_rain_data(input_data_file, output_data_file, dt_lower, dt_upper):
    """
    Read the historical rain data from file.
    """
    with open(input_data_file, "r") as f:
        with open(output_data_file, "a") as out:
            lines = f.readlines()

            for line in lines:
                words = line.split()
                # In <name>.dat rain file, we have mm/dd/yyyy hh:mm:ss x.y per line.
                dt = datetime.datetime.strptime(words[0] + " " + words[1], "%m/%d/%Y %H:%M:%S")
                if dt_lower <= dt <= dt_upper:
                    out.write(line)


if __name__ == "__main__":
    input_data_file = "swmm_5061.dat"
    output_data_file = "swmm_5061_small.dat"
    dt_lower = datetime.datetime(2019, 8, 1)
    dt_upper = datetime.datetime(2019, 10, 1)
    process_rain_data(input_data_file, output_data_file, dt_lower, dt_upper)
