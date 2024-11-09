#!/usr/bin/env python3

import argparse
from rich.progress import track
from datetime import datetime
from pathlib import Path

import yaml
import pandas as pd
from ament_index_python.packages import get_package_share_directory
from msg_parser import *  # noqa: F403
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_types_from_msg, get_typestore


def guess_msgtype(path: Path) -> str:
    """Guess message type name from path."""
    name = path.relative_to(path.parents[2]).with_suffix("")
    if "msg" not in name.parts:
        name = name.parent / "msg" / name.name
    return str(name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bagfile", type=str, help="relative path to target bag file")
    parser.add_argument(
        "-t",
        "--target_topic",
        type=str,
        default="target_topic.yaml",
        help="relative path to target topic yaml file",
    )
    args = parser.parse_args()

    bagfile_path = Path.cwd() / Path(args.bagfile)  # join
    assert bagfile_path.exists(), f"bagfile not found: {args.bagfile}"

    # load target topic yaml file
    topic_path = Path.cwd() / Path(args.target_topic)  # join
    assert topic_path.exists(), f"target topic yaml file not found: {args.target_topic}"
    with open(topic_path) as f:
        target_topic = yaml.safe_load(f.read())

    # add custom messages
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    add_types = {}

    path_info_msgs_pkg = Path(get_package_share_directory("path_info_msgs"))
    custom_msgs_list = list((path_info_msgs_pkg.joinpath("msg")).glob("*.msg"))

    for pathstr in custom_msgs_list:
        custom_msg_path = Path(pathstr)
        msgdef = custom_msg_path.read_text(encoding="utf-8")
        add_types.update(get_types_from_msg(msgdef, guess_msgtype(custom_msg_path)))

    typestore.register(add_types)

    # Create reader instance and open for reading.
    df = pd.DataFrame()
    with AnyReader([bagfile_path], default_typestore=typestore) as reader:
        for topic_name in track(target_topic):
            connections = [x for x in reader.connections if x.topic == topic_name]
            if len(connections) == 0:
                print(f"topic not found: {topic_name}, skip this topic")
                continue
            for connection, timestamp, rawdata in reader.messages(connections=connections):
                msg = reader.deserialize(rawdata, connection.msgtype)
                time = datetime.fromtimestamp(timestamp / 1e9)  # unix time to datetime
                time_dict = {"time": time, "timestamp": timestamp}
                msg_type = str(msg.__msgtype__)

                # siwtch by msg type
                if msg_type == "std_msgs/msg/Bool":
                    df_add = pd.DataFrame(time_dict | parse_bool(msg, topic_name), index=[0])
                    df = pd.concat([df, df_add], ignore_index=True)
                elif msg_type == "geometry_msgs/msg/Vector3":
                    df_add = pd.DataFrame(time_dict | parse_vector3(msg, topic_name), index=[0])
                    df = pd.concat([df, df_add], ignore_index=True)
                elif msg_type == "geometry_msgs/msg/Point":
                    df_add = pd.DataFrame(time_dict | parse_point(msg, topic_name), index=[0])
                    df = pd.concat([df, df_add], ignore_index=True)
                elif msg_type == "std_msgs/msg/Float32":
                    df_add = pd.DataFrame(time_dict | parse_float32(msg, topic_name), index=[0])
                    df = pd.concat([df, df_add], ignore_index=True)
                elif msg_type == "std_msgs/msg/Float32MultiArray":
                    df_add = pd.DataFrame(time_dict | parse_float32_multiarray(msg, topic_name), index=[0])
                    df = pd.concat([df, df_add], ignore_index=True)
                elif msg_type == "geometry_msgs/msg/Pose":
                    df_add = pd.DataFrame(time_dict | parse_pose(msg, topic_name), index=[0])
                    df = pd.concat([df, df_add], ignore_index=True)
                elif msg_type == "geometry_msgs/msg/PoseStamped":
                    df_add = pd.DataFrame(time_dict | parse_pose_stamped(msg, topic_name), index=[0])
                    df = pd.concat([df, df_add], ignore_index=True)
                else:
                    print(f"unsupported msg type: {msg_type}, topic: {topic_name}")

    # convert to csv
    print(df.head())
    csv_file_path = args.bagfile.rstrip("/") + ".csv"
    df.to_csv(csv_file_path)
    print("csv file is saved at: ", csv_file_path)


if __name__ == "__main__":
    main()
