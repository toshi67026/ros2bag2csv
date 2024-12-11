# ros2bag2csv

Convert ROS2 bag files to CSV format with selective topic extraction, utilizing the [rosbags](https://gitlab.com/ternaris/rosbags) library.

## Requirements
- Python3.8+
- ROS 2

## Installation
```
python3 -m pip install -r requirements.txt
```


## Usage
```sh
python3 ros2bag2csv.py [-t target_topic.yaml] {rosbag_file_dir}
```

### Topic configuration example

```yaml
- /float
- /ns1/vel
- /ns2/array
```

### Supported messages
Currently supports the following message types.
Other message types including custom messages can be added by implementing parser functions.

```
std_msgs: Bool, Float32, Float32MultiArray
geometry_msgs: Point, Pose, PoseStamped, Quaternion, Twist, Vector3
```

### Processing example
Example MATLAB processing and visualization script is provided in `csv_visualize.m`.


## License
Apache License 2.0
