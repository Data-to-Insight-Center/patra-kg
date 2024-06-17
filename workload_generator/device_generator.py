from parser.json_mc_parser import parse_json_mc
from ingester.neo4j_ingester import MCIngester
import copy
import uuid
import random

def main():
    uri = "bolt://localhost:7689"
    user = "neo4j"
    password = "rootroot"

    mc_ingester = MCIngester(uri, user, password)

    device_json = {
        "id": "jetson-nano",
        "name": "Nvidia Jetson Nano",
        "description": "A small, powerful computer for embedded AI systems and IoT devices.",
        "cpu_architecture": "ARM Cortex-A57",
        "cpu_cores": 4,
        "cpu_max_frequency": "1.43 GHz",
        "gpu_architecture": "Nvidia Maxwell",
        "gpu_cuda_cores": 128,
        "gpu_memory": "4 GB LPDDR4",
        "ai_capabilities_deep_learning": True,
        "ai_capabilities_machine_learning": True,
        "ai_capabilities_computer_vision": True
    }

    device_pi3 = {
        "id": "raspberry-pi-3",
        "name": "Raspberry Pi 3",
        "description": "It is a low-cost, small form-factor solution for various computing projects.",
        "cpu_architecture": "ARM Cortex-A53",
        "cpu_cores": 4,
        "cpu_max_frequency": "1.2 GHz",
        "gpu_architecture": None,
        "gpu_cuda_cores": None,
        "gpu_memory": None,
        "ai_capabilities_deep_learning": False,
        "ai_capabilities_machine_learning": False,
        "ai_capabilities_computer_vision": False
    }

    mc_ingester.add_device(device_pi3)
    mc_ingester.add_device(device_json)

if __name__ == "__main__":
    main()
