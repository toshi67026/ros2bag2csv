#!/usr/bin/env python3

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List

import pandas as pd
import yaml
from rich.progress import track
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_types_from_msg, get_typestore

from msg_parser import (
    parse_bool,
    parse_float32,
    parse_float32_multiarray,
    parse_point,
    parse_pose,
    parse_pose_stamped,
    parse_twist,
    parse_vector3,
)

ParserFunc = Callable[[Any, str], Dict[str, Any]]

MESSAGE_PARSERS: Dict[str, ParserFunc] = {
    "std_msgs/msg/Bool": parse_bool,
    "std_msgs/msg/Float32": parse_float32,
    "std_msgs/msg/Float32MultiArray": parse_float32_multiarray,
    "geometry_msgs/msg/Vector3": parse_vector3,
    "geometry_msgs/msg/Point": parse_point,
    "geometry_msgs/msg/Twist": parse_twist,
    "geometry_msgs/msg/Pose": parse_pose,
    "geometry_msgs/msg/PoseStamped": parse_pose_stamped,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert ROS2 bag files to CSV with selective topic extraction."
    )
    parser.add_argument("bagfile", type=str, help="path to target bag file directory")
    parser.add_argument(
        "-t",
        "--target_topic",
        type=str,
        default="target_topic.yaml",
        help="path to target topic yaml file",
    )
    return parser.parse_args()


def resolve_existing_path(path_str: str, label: str) -> Path:
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path_str}")
    return path


def load_target_topics(topic_file: Path) -> List[str]:
    with topic_file.open("r", encoding="utf-8") as f:
        target_topics = yaml.safe_load(f)

    if not isinstance(target_topics, list) or not all(
        isinstance(topic, str) for topic in target_topics
    ):
        raise ValueError("target topic yaml must be a list of topic strings")

    return target_topics


def guess_msgtype(path: Path) -> str:
    """Guess message type name from msg file path."""
    name = path.relative_to(path.parents[2]).with_suffix("")
    if "msg" not in name.parts:
        name = name.parent / "msg" / name.name
    return str(name)


def register_custom_messages() -> Any:
    typestore = get_typestore(Stores.ROS2_HUMBLE)
    add_types: Dict[str, Any] = {}
    """
    # --- Custom Message Support ---
    # Uncomment the block below to register your custom message types.
    # You also need to implement parser functions in msg_parser.py and
    # add them to MESSAGE_PARSERS.

    your_custom_msgs_pkg = Path(get_package_share_directory("your_custom_msgs"))
    custom_msgs_list = list((your_custom_msgs_pkg / "msg").glob("*.msg"))

    for custom_msg_path in custom_msgs_list:
        msgdef = custom_msg_path.read_text(encoding="utf-8")
        add_types.update(get_types_from_msg(msgdef, guess_msgtype(custom_msg_path)))
    """

    typestore.register(add_types)
    return typestore


def extract_rows(reader: AnyReader, topics: Iterable[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for topic in track(list(topics), description="Reading topics"):
        connections = [conn for conn in reader.connections if conn.topic == topic]
        if not connections:
            print(f"topic not found: {topic}, skip this topic")
            continue

        for connection, timestamp, rawdata in reader.messages(connections=connections):
            msg = reader.deserialize(rawdata, connection.msgtype)
            msg_type = str(msg.__msgtype__)
            parser = MESSAGE_PARSERS.get(msg_type)
            if parser is None:
                print(f"unsupported msg type: {msg_type}, topic: {topic}")
                continue

            row: Dict[str, Any] = {
                "time": datetime.fromtimestamp(timestamp / 1e9),
                "timestamp": timestamp,
            }
            row.update(parser(msg, topic))
            rows.append(row)

    return rows


def convert_bag_to_csv(bagfile_path: Path, target_topics: List[str]) -> Path:
    typestore = register_custom_messages()

    with AnyReader([bagfile_path], default_typestore=typestore) as reader:
        rows = extract_rows(reader, target_topics)

    df = pd.DataFrame(rows)
    print(df.head())

    csv_file_path = Path(str(bagfile_path).rstrip("/") + ".csv")
    df.to_csv(csv_file_path, index=False)
    return csv_file_path


def main() -> None:
    args = parse_args()
    bagfile_path = resolve_existing_path(args.bagfile, "bagfile")
    topic_path = resolve_existing_path(args.target_topic, "target topic yaml file")

    target_topics = load_target_topics(topic_path)
    csv_file_path = convert_bag_to_csv(bagfile_path, target_topics)
    print(f"csv file is saved at: {csv_file_path}")


if __name__ == "__main__":
    main()
