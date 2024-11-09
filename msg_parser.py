#!/usr/bin/env python3

from functools import wraps
from tf_transformations import euler_from_quaternion
from typing import Callable, Dict, Any



def with_fixed_topic(func: Callable) -> Callable:
    """Decorator to format topic names

    Strips leading '/' and replaces '/' with '.' and adds a trailing '.'
    This ensures consistent topic naming across all parser functions.

    Args:
        func: Parser function to be decorated

    Returns:
        Wrapped function that handles topic name formatting
    """

    @wraps(func)
    def wrapper(msg: Any, topic_name: str) -> Dict:
        fixed_topic = topic_name.lstrip("/").replace("/", ".") + "."
        return func(msg, fixed_topic)

    return wrapper


@with_fixed_topic
def parse_header(msg, topic: str) -> dict:
    """Parse ROS header message into dictionary format

    Args:
        msg: ROS header message
        topic: Topic name prefix for the output dictionary keys

    Returns:
        Dictionary containing timestamp and frame_id
    """
    return {
        f"{topic}stamp": msg.stamp,
        f"{topic}frame_id": msg.frame_id,
    }


@with_fixed_topic
def parse_bool(msg, topic: str) -> dict:
    """Parse boolean message into dictionary format"""
    return {f"{topic}data": msg.data}


@with_fixed_topic
def parse_float32(msg, topic: str) -> dict:
    """Parse float32 message into dictionary format"""
    return {f"{topic}data": msg.data}


@with_fixed_topic
def parse_float32_multiarray(msg, topic: str) -> dict:
    """Parse float32 multi array message into dictionary format

    Assumes 1-dimensional array layout

    Args:
        msg: ROS message containing float32 multi array
        topic: Topic name prefix for the output dictionary keys

    Returns:
        Dictionary with indexed data entries

    Raises:
        AssertionError: If array dimension is not 1
    """
    assert len(msg.layout.dim) == 1, "data length must be 1"
    return {f"{topic}data{i}": data for (i, data) in enumerate(msg.data)}


@with_fixed_topic
def parse_vector3(msg, topic: str) -> dict:
    """Parse Vector3 message into dictionary format"""
    return {
        f"{topic}x": msg.x,
        f"{topic}y": msg.y,
        f"{topic}z": msg.z,
    }


@with_fixed_topic
def parse_point(msg, topic: str) -> dict:
    """Parse Point message into dictionary format"""
    return {
        f"{topic}x": msg.x,
        f"{topic}y": msg.y,
        f"{topic}z": msg.z,
    }


@with_fixed_topic
def parse_quaternion(msg, topic: str) -> dict:
    """Parse Quaternion message into dictionary format"""
    return {
        f"{topic}x": msg.x,
        f"{topic}y": msg.y,
        f"{topic}z": msg.z,
        f"{topic}w": msg.w,
    }


@with_fixed_topic
def parse_quaternion_as_euler(msg, topic: str) -> dict:
    """Parse Quaternion message into Euler angles (roll, pitch, yaw)

    Converts quaternion to Euler angles using tf_transformations
    """
    roll, pitch, yaw = euler_from_quaternion([msg.x, msg.y, msg.z, msg.w])
    return {
        f"{topic}roll": roll,
        f"{topic}pitch": pitch,
        f"{topic}yaw": yaw,
    }


def parse_pose(msg, topic_name: str) -> dict:
    """Parse Pose message into dictionary format

    Combines position, orientation (both quaternion and euler) data
    """
    return (
        parse_point(msg.position, f"{topic_name}/position")
        | parse_quaternion(msg.orientation, f"{topic_name}/orientation")
        | parse_quaternion_as_euler(msg.orientation, f"{topic_name}/euler")
    )


def parse_pose_stamped(msg, topic_name: str) -> dict:
    """Parse PoseStamped message into dictionary format

    Combines header and pose data
    """
    return parse_header(msg.header, f"{topic_name}/header") | parse_pose(
        msg.pose, f"{topic_name}/pose"
    )
