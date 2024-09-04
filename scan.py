import os
import re
import asyncio
import socket
import itertools
import time

# Please edit config
TARGET_NODE = "4.233.61.8"
TARGET_PORT = 8080

class Seed:
    def __init__(self, ip=TARGET_NODE, port=TARGET_PORT):
        self.ip = ip
        self.port = port

    def __repr__(self):
        return f"Seed(ip='{self.ip}', port={self.port})"

def send_tcp_request(target_ip, target_port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)

    try:
        sock.connect((target_ip, target_port))
        sock.sendall(message.encode())
        response = sock.recv(4096)
        return response.decode()

    except Exception as e:
        print(f"Error -> {target_ip}:{target_port}: {e}")

    finally:
        sock.close()

async def fetch_ddos(command: str, seed: Seed):
    try:
        reader, writer = await asyncio.open_connection(seed.ip, seed.port)
        writer.write(command.encode())
        await writer.drain()
        response = await reader.read(4096) 
        print(f"Received response: {response.decode()}")
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"Error in fetch_ddos: {e}")

async def main():
    nodes_data = []
    primary_seed = Seed(ip=TARGET_NODE, port=TARGET_PORT)
    
    # Remove the previous file if it exists
    if os.path.exists("node_info.txt"):
        os.remove("node_info.txt")
    
    print(f"Target Node -> {primary_seed.ip}:{primary_seed.port}")
    primary_node_info = send_tcp_request(target_ip=primary_seed.ip, target_port=primary_seed.port, message="NODESTATUS\n")
    print(f"Target Node info -> \n{primary_node_info}")
    
    if primary_node_info.startswith("NODESTATUS"):
        nodes_list = send_tcp_request(target_ip=primary_seed.ip, target_port=primary_seed.port, message="NSLMNS\n")
        node_pattern = re.compile(r"(\d+\.\d+\.\d+\.\d+);(\d+):([A-Za-z0-9]+):(\d+)")
        
        for match in node_pattern.finditer(nodes_list):
            ip_address = match.group(1)
            port = match.group(2)
            nodes_data.append({
                "ip_address": ip_address,
                "port": port,
            })


    spinner = itertools.cycle(['|', '/', '-', '\\'])
    for node in nodes_data:
        try:
            ip_address = node["ip_address"]
            port = int(node["port"])
            node_status = send_tcp_request(target_ip=ip_address, target_port=port, message="NODESTATUS\n")
            status_pattern = re.compile(r"NODESTATUS \d+ (\d+) \d+ \d+ \w+ ([\d\.A-Za-z]+)")
            match = status_pattern.search(node_status)
            if match:
                block_number = match.group(1)
                version = match.group(2)
                line_to_write = f"{ip_address}:{port} | {block_number} | {version}\n"
                with open("node_info.txt", "a") as file:
                    file.write(line_to_write)
            # Add spinner animation
            print(next(spinner), end='\r')
            time.sleep(0.1)  # Delay for work simulation
        except Exception as e:
            print(f"Error sending request: {e}")

    # Clear the line with the spinner before printing the next line
    print(" ", end='\r')

    print("\n-------------------------")
    # Count the number of nodes
    node_count = len(nodes_data)
    print(f"Number of nodes: {node_count}")

    # ... (подальший код)

    # Count the number of lines in the file
    with open("node_info.txt", "r") as file:
        lines = file.readlines()
        line_count = len(lines)
    print(f"Number of lines in file: {line_count}")
    print("-------------------------")   
    
    # Check block synchronization
    block_numbers = [re.search(r"\| (\d+) \|", line).group(1) for line in lines]
    is_synced = all(block == block_numbers[0] for block in block_numbers)
    print(f"Network synchronization: {'Yes' if is_synced else 'No'}")
    print("-------------------------")
    
    # Count versions
    version_count = {}
    for line in lines:
        version = re.search(r"\| \d+ \| ([\d\.A-Za-z]+)\n", line).group(1)
        if version in version_count:
            version_count[version] += 1
        else:
            version_count[version] = 1
    
    for version, count in version_count.items():
        print(f"Version {version}: {count} times")

if __name__ == "__main__":
    asyncio.run(main())
