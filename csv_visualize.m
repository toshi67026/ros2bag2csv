clc
clear
close all

% read csv file
csv_file = 'sample_csv';
data = readtable([csv_file, '.csv']);

% get received time and response data
float = data.float;
float_valid = ~isnan(float);
float_time = data.time(float_valid);

init_idx = 1; % set initial index

init_time = float_time(init_idx);
end_time = seconds(float_time(end) - init_time);
time = data.time - init_time; % adjust start time to 0

% simple data (ex. Float32)
float = data.float;

% struct data (ex. Vector3)
ns1_vel_x = data.ns1_vel_x;
ns1_vel_y = data.ns1_vel_y;

% array data (ex. Float32MultiArray)
ns2_array_data0 = data.ns2_array_data0;
ns2_array_data1 = data.ns2_array_data1;

% valid data
float_valid = ~isnan(float);
ns1_vel_valid = ~isnan(ns1_vel);
ns2_array_valid = ~isnan(ns2_array);

% time
float_time = seconds(time(float_valid));
ns1_vel_x_time = seconds(time(ns1_vel_x_valid));
ns2_array_time = seconds(time(ns2_array_valid));

%% plot
figure('Name', [csv_file, '_float']);
hold on
plot(time, float(float_valid), 'b');
xlabel('Time [s]', 'Interpreter', 'latex');
xlim([0, end_time])

figure('Name', [csv_file, '_ns1_vel']);
hold on
plot(ns1_vel_time, ns1_vel_x(ns1_vel_valid));
plot(ns1_vel_time, ns1_vel_y(ns1_vel_valid));
legend({'$v_x$', '$v_y$'}, 'Interpreter', 'latex');
xlabel('Time [s]', 'Interpreter', 'latex');
xlim([0, end_time])

figure('Name', [csv_file, '_ns2_array']);
hold on
plot(ns2_array_time, ns2_array_data0(ns2_array_valid));
plot(ns2_array_time, ns2_array_data1(ns2_array_valid));
legend({'data0', 'data1'}, 'Interpreter', 'latex');
xlabel('Time [s]', 'Interpreter', 'latex');
xlim([0, end_time])
