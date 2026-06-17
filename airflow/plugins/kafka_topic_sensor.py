"""
Kafka Topic Sensor

Waits until there are messages in one or more Kafka topics.
Checks the consumer lag dynamically without consuming/committing events.
"""

import logging
from typing import List, Union, Optional

from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults
from kafka import KafkaConsumer, TopicPartition

import sys
sys.path.append("/app")

# Allow dynamic config loading
from agents.config import PipelineConfig

logger = logging.getLogger(__name__)


class KafkaTopicSensor(BaseSensorOperator):
    """
    Waits until one or more Kafka topics contain active, unconsumed messages.

    Args:
        topics: List of topic names (or a single topic string) to monitor.
        bootstrap_servers: Optional broker URL (defaults to PipelineConfig broker).
        group_id: Optional consumer group ID.
    """

    template_fields = ("topics",)

    @apply_defaults
    def __init__(
        self,
        topics: Union[str, List[str], None] = None,
        bootstrap_servers: Optional[str] = None,
        group_id: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.config = PipelineConfig()
        
        # Determine topics
        if topics:
            self.topics = topics if isinstance(topics, list) else [topics]
        else:
            self.topics = self.config.kafka.topics

        self.bootstrap_servers = bootstrap_servers or self.config.kafka.broker
        self.group_id = group_id or (self.config.kafka.group_id + "_sensor")

    def poke(self, context) -> bool:
        self.log.info(
            f"Checking for messages in topics: {self.topics} "
            f"on broker: {self.bootstrap_servers}"
        )
        
        try:
            # We initialize a light consumer simply to fetch end offsets and positions
            consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                consumer_timeout_ms=1000,
            )
            
            total_lag = 0
            
            for topic in self.topics:
                partitions = consumer.partitions_for_topic(topic)
                if not partitions:
                    self.log.warning(
                        f"Topic '{topic}' partitions empty or topic does not exist."
                    )
                    continue
                
                tps = [TopicPartition(topic, p) for p in partitions]
                
                # Fetch the latest offsets (end offsets)
                end_offsets = consumer.end_offsets(tps)
                
                for tp in tps:
                    latest = end_offsets.get(tp, 0)
                    try:
                        # Fetch current committed position
                        current = consumer.position(tp)
                    except Exception:
                        current = 0
                    
                    lag = max(0, latest - current)
                    total_lag += lag
            
            consumer.close()
            self.log.info(f"Calculated total consumer lag across monitored topics: {total_lag} messages")
            return total_lag > 0
            
        except Exception as exc:
            self.log.error(f"Error checking Kafka topic state: {exc}")
            return False
