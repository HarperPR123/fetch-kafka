from kafka import KafkaConsumer, KafkaProducer  
import json  
from datetime import datetime  
from collections import defaultdict 
import logging 

# Configure logging to display info and error messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize a Kafka consumer to read messages from the 'user-login' topic
consumer = KafkaConsumer(
    'user-login',  # Topic to consume messages from
    bootstrap_servers='localhost:29092',  # Kafka broker address
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # Deserialize messages from JSON
)

# Initialize a Kafka producer to send messages to another topic
producer = KafkaProducer(
    bootstrap_servers='localhost:29092',  # Kafka broker address
    value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Serialize messages to JSON
)

# Dictionaries to count occurrences of device types and locales
device_type_count = defaultdict(int)
locale_count = defaultdict(int)

# List to keep track of transformed data for insight updates
transformed_data_list = []

try:
    # Main loop to consume messages from the Kafka topic
    for message in consumer:
        try:
            data = message.value  # Extract the message content

            # Extract relevant information from the message
            user_id = data.get("user_id")
            app_version = data.get("app_version")
            device_type = data.get("device_type")
            ip = data.get("ip")
            locale = data.get("locale")
            device_id = data.get("device_id")
            timestamp = data.get("timestamp")

            # Convert the Unix timestamp to a human-readable format
            if timestamp is not None:
                readable_time = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                readable_time = "Unknown time"

            # Update counts for device types and locales
            device_type_count[device_type] += 1
            locale_count[locale] += 1

            # Log a message with the extracted information
            print(f"User {user_id} logged in using {device_type} at {readable_time} from IP {ip}, locale: {locale}")

            # Prepare the transformed data to be sent to the new Kafka topic
            transformed_data = {
                "user_id": user_id,
                "device_type": device_type,
                "readable_time": readable_time,
                "ip": ip
            }

            # Send the transformed data to the 'processed-user-login' topic
            producer.send('processed-user-login', transformed_data)
            print("Data sent to Kafka topic: processed-user-login")

            # Append the transformed data to the list
            transformed_data_list.append(transformed_data)

            # Update insights every 100 messages
            if len(transformed_data_list) % 100 == 0:
                # Determine the most popular device type and locale
                most_popular_device = max(device_type_count, key=device_type_count.get)
                print(f"Most popular device type: {most_popular_device} with {device_type_count[most_popular_device]} logins")

                most_appearing_locale = max(locale_count, key=locale_count.get)
                print(f"Most appearing locale: {most_appearing_locale} with {locale_count[most_appearing_locale]} logins")

        # Handle any exceptions that occur during message processing
        except Exception as e:
            logger.error(f"Error processing message: {e}")

# Gracefully handle script termination 
except KeyboardInterrupt:
    logger.info("Stopping the consumer gracefully")

# Ensure that the Kafka producer is closed when the script ends
finally:
    producer.close()
    logger.info("Kafka producer closed")