from airflow.plugins_manager import AirflowPlugin
from kafka_topic_sensor import KafkaTopicSensor

class KafkaSensorPlugin(AirflowPlugin):
    name = "kafka_sensor_plugin"
    sensors = [KafkaTopicSensor]
