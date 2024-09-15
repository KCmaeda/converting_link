import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster, TransformListener, Buffer
from geometry_msgs.msg import TransformStamped
from tf_transformations import euler_from_quaternion, quaternion_from_euler

pre_roll = 0.0
pre_pitch = 0.0 
pre_yaw = 0.0

class PitchFilteredTransformPublisher(Node):
    def __init__(self):
        super().__init__('pitch_filtered_transform_publisher')

        # tf2のバッファとリスナーを作成
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # tf2で新しい座標系をパブリッシュするためのブロードキャスタ
        self.tf_broadcaster = TransformBroadcaster(self)

        # 10Hzでタイマーを実行
        self.timer = self.create_timer(0.1, self.publish_filtered_transform)

    def publish_filtered_transform(self):
        global pre_roll
        global pre_pitch
        global pre_yaw
        try:
            # base_linkの座標変換を取得
            now = rclpy.time.Time()
            transform = self.tf_buffer.lookup_transform('odom', 'base_link', now)

            # クォータニオンを取得して、オイラー角に変換
            quaternion = (
                transform.transform.rotation.x,
                transform.transform.rotation.y,
                transform.transform.rotation.z,
                transform.transform.rotation.w
            )
            roll, pitch, yaw = euler_from_quaternion(quaternion)
            
            if abs(roll - pre_roll) <= 0.3:
                roll = pre_roll
            if abs(pitch - pre_pitch) <= 0.3:
                pitch = pre_pitch
            if abs(yaw - pre_yaw) <= 0.3:
                yaw = pre_yaw
                
            pre_roll = roll
            pre_pitch = pitch
            pre_yaw = yaw

            # 新しいクォータニオンを生成
            new_quaternion = quaternion_from_euler(roll, pitch, yaw)

            # base_link_2のTransformを作成
            new_transform = TransformStamped()
            new_transform.header.stamp = self.get_clock().now().to_msg()
            new_transform.header.frame_id = 'odom'
            new_transform.child_frame_id = 'base_link_2'

            # 位置は元のtransformからコピー
            new_transform.transform.translation.x = transform.transform.translation.x
            new_transform.transform.translation.y = transform.transform.translation.y
            new_transform.transform.translation.z = transform.transform.translation.z

            # 新しい回転を設定
            new_transform.transform.rotation.x = new_quaternion[0]
            new_transform.transform.rotation.y = new_quaternion[1]
            new_transform.transform.rotation.z = new_quaternion[2]
            new_transform.transform.rotation.w = new_quaternion[3]

            # base_link_2のTransformをパブリッシュ
            self.tf_broadcaster.sendTransform(new_transform)

        except Exception as e:
            self.get_logger().info(f'Could not transform base_link to base_link_2: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = PitchFilteredTransformPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

