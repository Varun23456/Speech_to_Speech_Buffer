import json
import pika
import asyncio
import requests
from typing import Optional
from Utils import JSONFixer
from Config import MT_DICTIONARY, INPUT_LANG, OUTPUT_LANG, MT_API_TIMEOUT

class MTMessageProcessor:
    """Handles processing and management of RabbitMQ messages for Machine Translation."""
    
    def __init__(self, input_queue: str, output_queue: str, cloudamqp_url: str, log_queue: str = "log_queue"):
        """
        Initialize MTMessageProcessor with queue configuration.

        Args:
            input_queue: Name of the input queue (expected to receive ASR JSON messages)
            output_queue: Name of the output queue (to publish MT results)
            cloudamqp_url: URL for CloudAMQP connection
            log_queue: Name of the log queue
        """
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.cloudamqp_url = cloudamqp_url
        self.log_queue = log_queue
        # Use the key pair "input_to_output" (e.g., "english_to_hindi") for MT lookup.
        mt_key = f"{INPUT_LANG}_to_{OUTPUT_LANG}"
        self.mt_config = MT_DICTIONARY.get(mt_key)
        if not self.mt_config:
            raise ValueError(f"No MT configuration found for language pair: {mt_key}")

    def extract_recognized_text(self, recognized_json) -> str:
        """
        Extract the recognized text from the ASR response.

        Args:
            recognized_json (dict or str): The JSON response from ASR

        Returns:
            str or None: The recognized text if found, else None
        """
        if isinstance(recognized_json, str):
            try:
                recognized_json = json.loads(recognized_json)
            except json.JSONDecodeError as e:
                print(f"Error parsing recognized JSON: {e}")
                return None
        
        try:
            recognized_text = recognized_json.get("data", {}).get("recognized_text")
            if recognized_text:
                return recognized_text
            else:
                print("No recognized text found in the response")
                return None
        except Exception as e:
            print(f"Error extracting recognized text: {e}")
            return None

    async def translate_text(self, channel: pika.channel.Channel, input_text: str) -> dict:
        """
        Perform text translation using the Machine Translation API with a timeout.

        Args:
            channel (pika.channel.Channel): RabbitMQ channel for logging
            input_text (str): The recognized text extracted from the ASR response

        Returns:
            dict: The JSON response from the MT API if successful, or None on error
        """
        url = self.mt_config["api_endpoint"]
        headers = {
            "access-token": self.mt_config["access_token"],
            "Content-Type": "application/json"
        }
        payload = {"input_text": input_text}
        timeout_value = MT_API_TIMEOUT

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout_value
            )
            # Raise an HTTPError if the response was unsuccessful
            response.raise_for_status()

            log_msg = f"Translation successful for {url}."
            await self.log_message(channel, log_msg, "TRANSLATION_SUCCESS")
            return response.json()

        except requests.exceptions.Timeout:
            log_msg = f"Translation Error: Request timed out after {timeout_value} seconds."
            await self.log_message(channel, log_msg, "TRANSLATION_ERROR")
            return None

        except requests.exceptions.HTTPError as e:
            # Check for 'Too Many Requests' or other HTTP error
            if e.response is not None and e.response.status_code == 429:
                log_msg = "Translation Error: Too Many Requests (429)."
            else:
                log_msg = f"Translation HTTP Error: {e}"
            await self.log_message(channel, log_msg, "TRANSLATION_ERROR")
            return None

        except requests.exceptions.RequestException as e:
            log_msg = f"Translation Error: {e}"
            await self.log_message(channel, log_msg, "TRANSLATION_ERROR")
            return None

        except Exception as e:
            log_msg = f"Unexpected Translation Error: {e}"
            await self.log_message(channel, log_msg, "TRANSLATION_ERROR")
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
        """Process a single message with error handling for Machine Translation."""
        try:
            log_msg = "Received MT request message"
            await self.log_message(channel, log_msg, "INFO")

            # The input message is expected to be the ASR JSON.
            try:
                recognized_json = json.loads(body)
            except Exception as e:
                log_msg = f"Failed to decode input JSON: {e}"
                await self.log_message(channel, log_msg, "ERROR")
                return False

            # Extract recognized text from the ASR JSON
            recognized_text = self.extract_recognized_text(recognized_json)
            if not recognized_text:
                log_msg = "No recognized text extracted from ASR response"
                await self.log_message(channel, log_msg, "ERROR")
                return False

            # Call the MT API with the recognized text.
            mt_response = await self.translate_text(channel,recognized_text)
            if not mt_response or mt_response.get("status") != "success":
                log_msg = f"MT failed: {mt_response.get('message', 'Unknown error') if mt_response else 'No response'}"
                await self.log_message(channel, log_msg, "ERROR")
                return False

            try:
                if isinstance(mt_response, dict):
                    mt_response = mt_response
                else:
                    mt_response = json.loads(mt_response)
                log_msg = f"Received valid MT JSON message: {mt_response}"
                await self.log_message(channel, log_msg, "INFO")
            except Exception as e:
                malformed_queue = f"{self.input_queue}_malformedjson"
                log_msg = f"Malformed MT JSON detected: {mt_response}"
                await self.log_message(channel, log_msg, "WARNING")
                try:
                    channel.queue_declare(queue=malformed_queue, durable=True)
                    channel.basic_publish(
                        exchange='',
                        routing_key=malformed_queue,
                        body=mt_response, 
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                    log_msg = f"Malformed MT JSON message pushed to '{malformed_queue}'"
                    await self.log_message(channel, log_msg, "INFO")
                    return True
                except Exception as e:
                    log_msg = f"Failed to push malformed MT JSON to '{malformed_queue}': {e}"
                    await self.log_message(channel, log_msg, "ERROR")
                    return False

            # Publish the MT result to the output queue.
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
                        body=json.dumps(mt_response),
                        properties=pika.BasicProperties(delivery_mode=2),
                        mandatory=True
                    )
                    log_msg = f"Successfully published MT result to {self.output_queue}"
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
                log_msg = f"Failed to publish MT message: {e}"
                await self.log_message(channel, log_msg, "ERROR")
                return False

        except Exception as e:
            log_msg = f"Processing MT Error: {e}"
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
