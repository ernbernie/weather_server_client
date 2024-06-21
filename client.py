import socket
import json
from termcolor import colored

def print_banner():
    banner = """
    ========================================
               Weather CLI Client
    ========================================
    """
    print(colored(banner, 'cyan'))

def get_weather_request(city):
    request = json.dumps({"city": city})
    return request

def main():
    host = '127.0.0.1'
    port = 65432
    print_banner()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        print(colored("Connected to the server.", 'cyan'))

        while True:
            city = input(colored("Enter city name (or 'exit' to quit): ", 'green'))
            if city.lower() == 'exit':
                print(colored("Exiting the Weather CLI Client. Goodbye!", 'red'))
                break

            request = get_weather_request(city)
            client_socket.sendall(request.encode('utf-8'))
            print(colored("Request sent to the server.", 'cyan'))

            response = client_socket.recv(4096).decode('utf-8')
            data = json.loads(response)

            if 'error' in data:
                print(colored(f"Error: {data['error']}", 'red'))
            else:
                city_name = data['city']
                weather_description = data['weather']
                temperature = data['temperature']
                print(colored(f"Weather in {city_name}:", 'yellow'))
                print(colored(f"{weather_description}, {temperature}°C", 'cyan'))

if __name__ == "__main__":
    main()
