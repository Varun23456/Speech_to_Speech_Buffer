import json
import pika
import asyncio
import requests
from typing import Optional
from Utils import JSONFixer
from Config import ASR_DICTIONARY, INPUT_LANG, ASR_API_TIMEOUT

class ASRMessageProcessor:
    """Handles processing and management of RabbitMQ messages."""
    
    def __init__(self, input_queue: str, output_queue: str, cloudamqp_url: str, log_queue: str = "log_queue"):
        """
        Initialize MessageProcessor with queue configuration.

        Args:
            input_queue: Name of the input queue
            output_queue: Name of the output queue
            cloudamqp_url: URL for CloudAMQP connection
            log_queue: Name of the log queue
        """
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.cloudamqp_url = cloudamqp_url
        self.log_queue = log_queue
        self.asr_config = ASR_DICTIONARY.get(INPUT_LANG)
        if not self.asr_config:
            raise ValueError(f"No ASR configuration found for input language: {INPUT_LANG}")

    async def asr_inference(self, channel: pika.channel.Channel, audio_data: bytes) -> dict:
        """
        Perform ASR inference on the given audio data with a timeout.
        
        Returns:
            dict: The JSON response from the ASR API if successful, or None on error
        """
        
        url = self.asr_config["api_endpoint"]
        headers = {"access-token": self.asr_config["access_token"]}
        files = {"audio_file": ("audio.wav", audio_data, "audio/wav")}
        timeout_value = ASR_API_TIMEOUT

        try:
            response = requests.post(
                url,
                headers=headers,
                files=files,
                timeout=timeout_value
            )
            # Raise an HTTPError if the response was unsuccessful
            response.raise_for_status()

            # If we reach here, the request was successful
            log_msg = f"ASR Inference successful for {url}."
            await self.log_message(channel, log_msg, "ASR_INFERENCE")
            return response.json()

        except requests.exceptions.Timeout:
            log_msg = f"ASR Inference Error: Request timed out after {timeout_value} seconds."
            await self.log_message(channel, log_msg, "ASR_INFERENCE")
            return None

        except requests.exceptions.HTTPError as e:
            # Check for 'Too Many Requests' or any other HTTP error
            if e.response is not None and e.response.status_code == 429:
                log_msg = "ASR Inference Error: Too Many Requests (429)."
            else:
                log_msg = f"ASR Inference HTTP Error: {e}"
            await self.log_message(channel, log_msg, "ASR_INFERENCE")
            return None

        except requests.exceptions.RequestException as e:
            # Catches all other requests-related errors
            log_msg = f"ASR Inference Error: {e}"
            await self.log_message(channel, log_msg, "ASR_INFERENCE")
            return None

        except Exception as e:
            log_msg = f"ASR Inference Error: {e}"
            await self.log_message(channel, log_msg, "ASR_INFERENCE")
            return None


    async def log_message(self, channel: pika.channel.Channel, log_msg: str, log_level: str):
        """Log a message to the log queue."""
        try:
            if channel is None:
                print(f"Log ({log_level}): {log_msg}")
                return
            channel.queue_declare(queue=self.log_queue, durable=True)
            log_entry = {"level": log_level, "message": log_msg}
            channel.basic_publish(
                exchange='',
                routing_key=self.log_queue,
                body=json.dumps(log_entry),
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except Exception as e:
            print(f"Failed to publish log message to {self.log_queue}: {e}")

    async def process_message(self, channel: pika.channel.Channel, method_frame: Optional[pika.spec.Basic.Deliver],
                              body: bytes) -> bool:
        """Process a single message with error handling."""
        try:
            # Perform ASR inference
            log_msg = "Received audio file for ASR inference"
            await self.log_message(channel, log_msg, "INFO")

            asr_response = await self.asr_inference(channel, body)
            if not asr_response or asr_response.get("status") != "success":
                log_msg = f"ASR failed: {asr_response.get('message', 'Unknown error')}"
                await self.log_message(channel, log_msg, "ERROR")
                return False

            try:
                # If asr_response is already a dict, use it directly; otherwise, decode it.
                if isinstance(asr_response, dict):
                    data = asr_response
                else:
                    data = json.loads(asr_response)
                log_msg = f"Received valid JSON message: {data}"
                await self.log_message(channel, log_msg, "INFO")
            except Exception as e:
                malformed_queue = f"{self.input_queue}_malformedjson"
                log_msg = f"Malformed JSON detected: {asr_response}"
                await self.log_message(channel, log_msg, "WARNING")

                try:
                    channel.queue_declare(queue=malformed_queue, durable=True)
                    # Publish the original input message (body) to the malformed queue.
                    channel.basic_publish(
                        exchange='',
                        routing_key=malformed_queue,
                        body=asr_response,
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                    log_msg = f"Malformed JSON message pushed to '{malformed_queue}'"
                    await self.log_message(channel, log_msg, "INFO")
                    return True
                except Exception as e:
                    log_msg = f"Failed to push malformed JSON to '{malformed_queue}': {e}"
                    await self.log_message(channel, log_msg, "ERROR")
                    return False

            try:
                # await asyncio.sleep(15)  # Simulate processing time
                try:
                    channel.queue_declare(queue=self.output_queue, durable=True, passive=True)
                except pika.exceptions.ChannelClosedByBroker:
                    if channel.is_closed:
                        channel = channel.connection.channel()
                    channel.queue_declare(queue=self.output_queue, durable=True)
                    log_msg = f"Recreated output queue '{self.output_queue}'"
                    await self.log_message(channel, log_msg, "INFO")

                try:
                    channel.basic_publish(
                        exchange='',
                        routing_key=self.output_queue,
                        body=json.dumps(data),
                        properties=pika.BasicProperties(delivery_mode=2),
                        mandatory=True
                    )

                    log_msg = f"Successfully published to {self.output_queue}"
                    await self.log_message(channel, log_msg, "INFO")
                    return True

                except pika.exceptions.AMQPConnectionError as e:
                    log_msg = f"RabbitMQ Server Down Error: {e}"
                    await self.log_message(channel, log_msg, "ERROR")
                    return False

                except ConnectionResetError:
                    log_msg = "Network disconnected! Reconnecting..."
                    await self.log_message(channel, log_msg, "ERROR")
                    return False

            except Exception as e:
                log_msg = f"Failed to publish message: {e}"
                await self.log_message(channel, log_msg, "ERROR")
                return False

        except Exception as e:
            log_msg = f"Processing Error: {e}"
            await self.log_message(channel, log_msg, "ERROR")
            return False

    async def consume_messages(self):
        retry_delay = 1
        connection = None
        channel = None
        queue_empty_logged = False 
        
        while True:
            try:
                if not connection or connection.is_closed:
                    params = pika.URLParameters(self.cloudamqp_url)
                    params.socket_timeout = 5
                    connection = pika.BlockingConnection(params)
                    channel = connection.channel()
                    channel.queue_declare(queue=self.input_queue, durable=True)
                    channel.queue_declare(queue=self.output_queue, durable=True)
                    channel.queue_declare(queue=self.log_queue, durable=True)
                        

                method_frame, _, body = channel.basic_get(queue=self.input_queue, auto_ack=False)

                if method_frame:
                    if await self.process_message(channel, method_frame, body):
                        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                    else:
                        channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
                    queue_empty_logged = False    
                else:
                    if not queue_empty_logged:
                        log_msg = f"Input queue '{self.input_queue}' is currently empty."
                        await self.log_message(channel, log_msg, "INFO")
                        queue_empty_logged = True

                retry_delay = 1

            except pika.exceptions.ChannelClosedByBroker as e:
                error_message = str(e)
                if connection.is_closed:
                    params = pika.URLParameters(self.cloudamqp_url)
                    params.socket_timeout = 5
                    connection = pika.BlockingConnection(params)
                if channel is None or channel.is_closed:
                    channel = connection.channel()

                if "NOT_FOUND - no queue" in error_message:
                    if self.input_queue in error_message:
                        log_msg = f"Input queue '{self.input_queue}' not found. Recreating queue."
                        await self.log_message(channel, log_msg, "ERROR")
                        channel.queue_declare(queue=self.input_queue, durable=True)
                    else:
                        log_msg = f"Queue not found: {error_message}"
                        await self.log_message(channel, log_msg, "ERROR")
                else:
                    log_msg = f"Channel closed by broker: {e}"
                    await self.log_message(channel, log_msg, "ERROR")

            except pika.exceptions.AMQPConnectionError as e:
                log_msg = f"RabbitMQ Server Down Error: {e}"
                await self.log_message(channel, log_msg, "ERROR")
                if connection and not connection.is_closed:
                    connection.close()
                await self.log_message(channel, f"Retrying in {retry_delay} seconds...", "ERROR")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)

            except ConnectionResetError:
                log_msg = "Network disconnected! Reconnecting..."
                if connection and not connection.is_closed:
                    connection.close()
                await self.log_message(channel, f"Retrying in {retry_delay} seconds...", "ERROR")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)

            except Exception as e:
                log_msg = f"Unexpected error: {e}"
                await self.log_message(channel, log_msg, "ERROR")
                if connection and not connection.is_closed:
                    connection.close()
                await asyncio.sleep(1)

            await asyncio.sleep(0.1)
