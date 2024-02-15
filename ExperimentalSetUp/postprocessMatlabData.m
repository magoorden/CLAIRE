%% Preprocess the measurement data.
% The precision of the time stamp is not handled well by TikZ / pdfplot.
% This script will transform the date format to seconds from the start of
% the experiment.

clear all

folder = "OnlineControlExperiment15/data/fixed/"; % The location of the .mat files.
files = ["Control_stateData","DepthData", "RainData"]; % The names of the .mat files (excluding the extenstion).
ignore = 8; % Number of first lines to ignore, as data collection might have started before the actual experiment started.

for file = files
    data = importdata(strcat(folder, file, ".mat"));
    
    data(1:ignore, :) = [];
    
    nrows = size(data,1);
    A = data - [data(1,1) * ones(nrows,1), zeros(nrows,1)];
    B = [86400 * A(:,1), A(:,2)];
    C = [round(B(:,1)), B(:,2)];

    writematrix(C,strcat(folder, file, ".csv"));
end