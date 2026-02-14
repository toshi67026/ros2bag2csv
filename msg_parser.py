#!/usr/bin/env python3

from functools import wraps
from typing import Any, Callable, Dict

from tf_transformations import euler_from_quaternion


def _normalize_topic(topic_name: str) -> str:
    return topic_name.lstrip("/").replace("/", ".") + "."


def _merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for item in dicts:
        merged.update(item)
    return merged


def with_fixed_topic(func: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
    """Decorator to normalize topic names for parser outputs."""

    @wraps(func)
    def wrapper(msg: Any, topic_name: str) -> Dict[str, Any]:
        fixed_topic = _normalize_topic(topic_name)
        return func(msg, fixed_topic)

    return wrapper


@with_fixed_topic
def parse_header(msg: Any, topic: str) -> Dict[str, Any]:
    return {
        f"{topic}stamp": msg.stamp,
        f"{topic}frame_id": msg.frame_id,
    }


@with_fixed_topic
def parse_bool(msg: Any, topic: str) -> Dict[str, Any]:
    return {f"{topic}data": msg.data}


@with_fixed_topic
def parse_float32(msg: Any, topic: str) -> Dict[str, Any]:
    return {f"{topic}data": msg.data}


@with_fixed_topic
def parse_float32_multiarray(msg: Any, topic: str) -> Dict[str, Any]:
    if len(msg.layout.dim) != 1:
        raise ValueError("Float32MultiArray parser only supports 1-dimensional layout")
    return {f"{topic}data{i}": data for i, data in enumerate(msg.data)}


@with_fixed_topic
def parse_vector3(msg: Any, topic: str) -> Dict[str, Any]:
    return {
        f"{topic}x": msg.x,
        f"{topic}y": msg.y,
        f"{topic}z": msg.z,
    }


@with_fixed_topic
def parse_point(msg: Any, topic: str) -> Dict[str, Any]:
    return {
        f"{topic}x": msg.x,
        f"{topic}y": msg.y,
        f"{topic}z": msg.z,
    }


@with_fixed_topic
def parse_quaternion(msg: Any, topic: str) -> Dict[str, Any]:
    return {
        f"{topic}x": msg.x,
        f"{topic}y": msg.y,
        f"{topic}z": msg.z,
        f"{topic}w": msg.w,
    }


@with_fixed_topic
def parse_quaternion_as_euler(msg: Any, topic: str) -> Dict[str, Any]:
    roll, pitch, yaw = euler_from_quaternion([msg.x, msg.y, msg.z, msg.w])
    return {
        f"{topic}roll": roll,
        f"{topic}pitch": pitch,
        f"{topic}yaw": yaw,
    }


def parse_twist(msg: Any, topic: str) -> Dict[str, Any]:
    return _merge_dicts(
        parse_vector3(msg.linear, f"{topic}/linear"),
        parse_vector3(msg.angular, f"{topic}/angular"),
    )


def parse_pose(msg: Any, topic: str) -> Dict[str, Any]:
    return _merge_dicts(
        parse_point(msg.position, f"{topic}/position"),
        parse_quaternion(msg.orientation, f"{topic}/orientation"),
        parse_quaternion_as_euler(msg.orientation, f"{topic}/euler"),
    )


def parse_pose_stamped(msg: Any, topic: str) -> Dict[str, Any]:
    return _merge_dicts(
        parse_header(msg.header, f"{topic}/header"),
        parse_pose(msg.pose, f"{topic}/pose"),
    )
