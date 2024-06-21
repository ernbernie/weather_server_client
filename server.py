import socket
import threading
import requests
import json
import logging
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Public API URLs (OpenWeatherMap)
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
GEOCODING_API_URL = "http://api.openweathermap.org/geo/1.0/direct"

# Retrieve API key from environment variable
API_KEY = os.getenv("WEATHER_API_KEY")
if not API_KEY:
    raise ValueError("No API key found. Set the WEATHER_API_KEY environment variable in your .env file.")

connected_clients = 0
lock = threading.Lock()

def fetch_coordinates(city_name):
    params = {'q': city_name, 'appid': API_KEY}
    response = requests.get(GEOCODING_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]['lat'], data[0]['lon']
    return None, None

def fetch_weather(lat, lon):
    params = {'lat': lat, 'lon': lon, 'appid': API_KEY, 'units': 'metric'}
    response = requests.get(WEATHER_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        city_name = data['name']
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        return {'city': city_name, 'weather': weather_description, 'temperature': temperature}
    return None

def handle_client(client_socket):
    global connected_clients
    with client_socket:
        with lock:
            connected_clients += 1
        logging.info("Connected to client.")
        try:
            while True:
                # Receive data from the client
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                logging.info(f"Received request: {data}")

                # Parse the client's request
                request = json.loads(data)
                city = request.get('city')
                
                if not city:
                    response = json.dumps({"error": "No city provided"})
                    client_socket.sendall(response.encode('utf-8'))
                    continue

                logging.info(f"Fetching coordinates for city: {city}")
                lat, lon = fetch_coordinates(city)
                if not lat or not lon:
                    response = json.dumps({"error": f"Failed to fetch coordinates for city: {city}"})
                    client_socket.sendall(response.encode('utf-8'))
                    continue

                logging.info(f"Fetching weather data for coordinates: ({lat}, {lon})")
                weather_data = fetch_weather(lat, lon)
                if weather_data:
                    response = json.dumps(weather_data)
                    logging.info(f"Successfully retrieved weather data for coordinates: ({lat}, {lon})")
                else:
                    response = json.dumps({"error": "Failed to fetch weather data"})
                    logging.error(f"Failed to fetch weather data for coordinates: ({lat}, {lon})")

                # Send the response back to the client
                client_socket.sendall(response.encode('utf-8'))

        except json.JSONDecodeError:
            logging.error("Invalid JSON received.")
            client_socket.sendall(json.dumps({"error": "Invalid JSON"}).encode('utf-8'))
        except requests.RequestException as e:
            logging.error(f"Request to API failed: {e}")
            client_socket.sendall(json.dumps({"error": "API request failed"}).encode('utf-8'))
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            client_socket.sendall(json.dumps({"error": "Internal server error"}).encode('utf-8'))
        finally:
            with lock:
                connected_clients -= 1
            logging.info("Client disconnected.")

def server_status():
    while True:
        time.sleep(5)
        with lock:
            if connected_clients == 0:
                logging.info("No clients connected. Server is listening for connections.")
            elif connected_clients == 1:
                logging.info("1 client connected.")
            else:
                logging.info(f"{connected_clients} clients connected.")

def start_server(host='127.0.0.1', port=65432):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    logging.info(f"Server listening on {host}:{port}")

    status_thread = threading.Thread(target=server_status, daemon=True)
    status_thread.start()

    while True:
        client_socket, addr = server.accept()
        logging.info(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_server()
