#!/usr/bin/env python3
"""
Manages docker-compose files for local development environments.
"""

import os
import yaml
from typing import Dict

TEMPLATES: Dict[str, Dict] = {
    "postgres": {
        "version": "3.8",
        "services": {
            "db": {
                "image": "postgres:15-alpine",
                "restart": "always",
                "environment": {
                    "POSTGRES_USER": "myuser",
                    "POSTGRES_PASSWORD": "mypassword",
                    "POSTGRES_DB": "mydatabase",
                },
                "ports": ["5432:5432"],
                "volumes": ["postgres_data:/var/lib/postgresql/data/"],
            }
        },
        "volumes": {"postgres_data": {}},
    },
    "redis": {
        "version": "3.8",
        "services": {
            "redis": {
                "image": "redis:7-alpine",
                "restart": "always",
                "ports": ["6379:6379"],
                "volumes": ["redis_data:/data"],
            }
        },
        "volumes": {"redis_data": {}},
    },
    "rabbitmq": {
        "version": "3.8",
        "services": {
            "rabbitmq": {
                "image": "rabbitmq:3-management-alpine",
                "restart": "always",
                "ports": ["5672:5672", "15672:15672"],
                "environment": {
                    "RABBITMQ_DEFAULT_USER": "myuser",
                    "RABBITA_DEFAULT_PASS": "mypassword",
                },
                "volumes": ["rabbitmq_data:/var/lib/rabbitmq/"],
            }
        },
        "volumes": {"rabbitmq_data": {}},
    },
}


def create_docker_compose(service: str, path: str = ".") -> str:
    """
    Creates a docker-compose.yml file for a given service in the specified path.

    Args:
        service: The name of the service (e.g., 'postgres').
        path: The directory where the file will be created.

    Returns:
        The full path to the created docker-compose.yml file.
    """
    if service not in TEMPLATES:
        raise ValueError(
            f"Service '{service}' not supported. Available services: {list(TEMPLATES.keys())}"
        )

    compose_path = os.path.join(path, "docker-compose.yml")

    if os.path.exists(compose_path):
        # We can decide whether to overwrite, merge, or fail.
        # For now, we'll fail to avoid accidental data loss.
        raise FileExistsError(
            f"A 'docker-compose.yml' already exists at {path}. Please remove it first."
        )

    with open(compose_path, "w") as f:
        yaml.dump(TEMPLATES[service], f, default_flow_style=False, sort_keys=False)

    return compose_path
