"""
ros2_square_cmd_vel.py — node ROS 2 (rclpy) yang menggerakkan robot omnidirectional
(Robotont / simulator) membentuk lintasan persegi lewat topic /cmd_vel.
Karena holonomic, robot cukup mengubah linear.x dan linear.y tanpa berputar.

Jalankan (ROS 2 Humble, workspace sudah di-source):
    python3 ros2_square_cmd_vel.py
Untuk differential drive (mis. turtlesim): ganti DIFF = True,
    ros2 run turtlesim turtlesim_node
    python3 ros2_square_cmd_vel.py --ros-args -r /cmd_vel:=/turtle1/cmd_vel

Catatan: file ini BELUM diuji pada ROS sungguhan (ROS tidak tersedia saat repo
ini disusun). Logika kinematikanya sudah diuji di kinematika_mobile_robot.py.
"""
import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

DIFF = False
V = 0.2          # m/s
SIDE = 1.0       # m
W = math.pi / 4  # rad/s (untuk differential drive)


class Square(Node):
    def __init__(self):
        super().__init__("square_cmd_vel")
        self.pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.dt = 0.05
        self.plan = self.build_plan()
        self.timer = self.create_timer(self.dt, self.tick)

    def build_plan(self):
        n_lin = int(SIDE / V / self.dt)
        if DIFF:
            n_rot = int((math.pi / 2) / W / self.dt)
            return [((V, 0.0, 0.0), n_lin), ((0.0, 0.0, W), n_rot)] * 4
        return [((V, 0.0, 0.0), n_lin), ((0.0, V, 0.0), n_lin), ((-V, 0.0, 0.0), n_lin), ((0.0, -V, 0.0), n_lin)]

    def tick(self):
        msg = Twist()
        if self.plan:
            (vx, vy, wz), n = self.plan[0]
            msg.linear.x, msg.linear.y, msg.angular.z = vx, vy, wz
            self.plan[0] = ((vx, vy, wz), n - 1)
            if n - 1 <= 0:
                self.plan.pop(0)
        else:
            self.get_logger().info("Lintasan persegi selesai")
            self.timer.cancel()
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = Square()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.pub.publish(Twist())
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
