import datetime
import csv


def create_file():
    data_file = "/home/martijn/Documents/CLAIRE/swmm_models/zero.dat"
    start_date = datetime.datetime(2019, 9, 5, 0, 1, 0)
    end_date = datetime.datetime(2019, 9, 24, 0, 0, 0)
    with open(data_file, "w") as f:
        current_date = start_date
        while current_date < end_date:
            f.write(current_date.strftime('%m/%d/%Y %H:%M:%S') + " 0.0\n")
            # f_writer = csv.writer(f, delimiter=' ')
            # f_writer.writerow([current_date.strftime('%m/%d/%Y %H:%M:%s'), "0.0"])
            current_date += datetime.timedelta(minutes=1)


if __name__ == "__main__":
    create_file()
