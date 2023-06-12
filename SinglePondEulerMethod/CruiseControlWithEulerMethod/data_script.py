import re
import csv


if __name__ == "__main__":

    with open("cruise_minmax_corrected_new_method_result_multiple_simulations.txt") as raw:
        data = {}
        variableName = ""
        for line in raw:
            if line.startswith("["):
                # Line contains data
                simNumber = line[1]
                allData = re.findall("\([0-9.]*,[0-9.]*\)", line)
                data[f"{variableName}_{simNumber}"] = allData
            else:
                # Line contains variable name
                variableName = line[:-2]

    for name, data in data.items():
        with open(f"cruise_data_{name}.ttt", "w") as f:
            writer = csv.writer(f, delimiter=' ')
            for datapoint in data:
                writer.writerow(datapoint[1:-1].split(","))
