# file: /api/services/pubsub_service.py

import json

from typing import Dict
from api.config import logger, GOOGLE_CLOUD_PROJECT, PUBSUB_TOPIC
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.publisher.futures import Future

publisher : pubsub_v1.PublisherClient = pubsub_v1.PublisherClient()
TOPIC_PATH : str = publisher.topic_path(GOOGLE_CLOUD_PROJECT, PUBSUB_TOPIC)

class PubSubService:
    @staticmethod
    def publish_message(message_data : Dict) -> str:
        if not isinstance(message_data, dict):
            logger.error("El mensaje debe ser un diccionario.")
            raise ValueError("El mensaje debe ser un diccionario.")
        
        codified_data : str = json.dumps(message_data).encode('utf-8')
        logger.info("")
        logger.info(f"Message data: {message_data}")
        logger.info("")
        
        future : Future = publisher.publish(TOPIC_PATH, data=codified_data)
        result : str = future.result()
        logger.info(f"Mensaje publicado en PubSub: {result}")
        return result
    