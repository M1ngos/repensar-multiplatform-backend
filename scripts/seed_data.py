#!/usr/bin/env python3
"""
Comprehensive data seeding script for Repensar Multiplatform Backend.

This script populates the database with realistic mock data by making HTTP requests
to the API endpoints. It creates multiple entities and validates relationships.

IMPORTANT: Set DISABLE_RATE_LIMITING=true in .env to bypass rate limits during seeding.

Usage:
    python scripts/seed_data.py [--api-url http://localhost:8000] [--dry-run] [--delay 0.1]

    # Quick test with minimal data (5 users, 5 volunteers, 3 projects, etc.)
    python scripts/seed_data.py --test

    # For faster seeding (requires DISABLE_RATE_LIMITING=true in .env)
    python scripts/seed_data.py --delay 0.05
"""

import argparse
import os
import random
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict

import httpx
from faker import Faker

# Initialize Faker for generating realistic mock data
fake = Faker('pt_BR')  # Use Portuguese locale

# Vocabulário ambiental em português
ADJETIVOS_AMBIENTAIS = [
    "Sustentável", "Verde", "Ecológico", "Renovável", "Orgânico", "Carbono Neutro",
    "Lixo Zero", "Resiliente ao Clima", "Biodiverso", "Conservacionista",
    "Regenerativo", "Positivo para a Natureza", "Baixo Impacto", "Economia Circular", "Baseado na Natureza"
]

SUBSTANTIVOS_AMBIENTAIS = [
    "Floresta", "Oceano", "Rio", "Mangue", "Recife de Coral", "Cerrado",
    "Ecossistema", "Corredor Ecológico", "Parque Urbano", "Horta Comunitária", "Bacia Hidrográfica",
    "Reserva Marinha", "Reserva Natural", "Jardim Botânico", "Mata Atlântica", "Pantanal"
]

ACOES_AMBIENTAIS = [
    "Restauração", "Conservação", "Proteção", "Reflorestamento", "Reabilitação",
    "Preservação", "Revitalização", "Regeneração", "Recuperação", "Valorização",
    "Monitoramento", "Gestão", "Cultivo", "Renaturalização", "Remediação"
]

TIPOS_PROJETO = [
    "Iniciativa de Plantio de Árvores", "Limpeza Costeira", "Restauração de Habitat",
    "Projeto de Arborização Urbana", "Programa Carbono Zero", "Campanha Redução de Resíduos",
    "Transição Energias Renováveis", "Monitoramento Qualidade da Água", "Jardim de Polinizadores",
    "Reintrodução de Espécies Nativas", "Programa de Compostagem", "Infraestrutura Verde",
    "Plano de Ação Climática", "Inventário de Biodiversidade", "Programa Educação Ambiental"
]

PREFIXOS_TAREFA = [
    "Plantar", "Monitorar", "Avaliar", "Inventariar", "Coletar", "Analisar", "Documentar",
    "Instalar", "Remover", "Limpar", "Restaurar", "Proteger", "Manter", "Educar",
    "Coordenar", "Organizar", "Implementar", "Avaliar", "Pesquisar", "Mapear"
]

OBJETOS_TAREFA = [
    "árvores nativas", "mudas", "espécies invasoras", "amostras de água", "qualidade do solo",
    "populações de fauna", "emissões de carbono", "fluxos de resíduos", "painéis solares",
    "jardins de chuva", "composteiras", "estações de reciclagem", "habitats", "trilhas",
    "sinalização educativa", "materiais didáticos", "sensores ambientais", "equipamentos de monitoramento"
]

ATIVIDADES_VOLUNTARIO = [
    "Plantou {} mudas de espécies nativas na zona ripária",
    "Removeu espécies invasoras de {} hectares de área úmida",
    "Coletou amostras de água em {} estações de monitoramento",
    "Conduziu oficina de educação ambiental para {} membros da comunidade",
    "Instalou {} painéis solares no centro comunitário",
    "Construiu {} canteiros elevados para agricultura urbana",
    "Removeu {} kg de resíduos marinhos da costa",
    "Realizou inventário de fauna identificando {} espécies",
    "Manteve {} sistemas de compostagem em escolas locais",
    "Mapeou {} km de trilhas ecológicas na área de conservação"
]

# Gamification templates
BADGE_TEMPLATES = [
    # Time-based badges
    {"name": "Primeiro Passo", "description": "Completou suas primeiras 10 horas de voluntariado", "category": "time", "rarity": "common", "points_value": 10, "color": "#4CAF50"},
    {"name": "Dedicado", "description": "Completou 50 horas de voluntariado", "category": "time", "rarity": "common", "points_value": 25, "color": "#8BC34A"},
    {"name": "Comprometido", "description": "Completou 100 horas de voluntariado", "category": "time", "rarity": "rare", "points_value": 50, "color": "#2196F3"},
    {"name": "Guardião Ambiental", "description": "Completou 250 horas de voluntariado", "category": "time", "rarity": "epic", "points_value": 100, "color": "#9C27B0"},
    {"name": "Lenda Verde", "description": "Completou 500 horas de voluntariado", "category": "time", "rarity": "legendary", "points_value": 250, "color": "#FFD700"},
    # Project badges
    {"name": "Colaborador", "description": "Participou de seu primeiro projeto", "category": "projects", "rarity": "common", "points_value": 15, "color": "#00BCD4"},
    {"name": "Multi-Projetos", "description": "Participou de 5 projetos diferentes", "category": "projects", "rarity": "rare", "points_value": 40, "color": "#3F51B5"},
    {"name": "Veterano de Projetos", "description": "Participou de 10 projetos diferentes", "category": "projects", "rarity": "epic", "points_value": 80, "color": "#673AB7"},
    # Skill badges
    {"name": "Aprendiz", "description": "Adquiriu sua primeira habilidade", "category": "skills", "rarity": "common", "points_value": 10, "color": "#FF9800"},
    {"name": "Versátil", "description": "Possui 5 habilidades diferentes", "category": "skills", "rarity": "rare", "points_value": 35, "color": "#FF5722"},
    {"name": "Especialista", "description": "Alcançou nível expert em uma habilidade", "category": "skills", "rarity": "epic", "points_value": 75, "color": "#E91E63"},
    # Leadership badges
    {"name": "Mentor", "description": "Ajudou a treinar novos voluntários", "category": "leadership", "rarity": "rare", "points_value": 45, "color": "#607D8B"},
    {"name": "Líder de Equipe", "description": "Liderou uma equipe em um projeto", "category": "leadership", "rarity": "epic", "points_value": 90, "color": "#795548"},
    # Special badges
    {"name": "Pioneiro", "description": "Um dos primeiros voluntários da plataforma", "category": "special", "rarity": "legendary", "points_value": 200, "color": "#F44336", "is_secret": True},
    {"name": "Maratonista Verde", "description": "Completou 8 horas em um único dia", "category": "special", "rarity": "rare", "points_value": 50, "color": "#009688"},
    {"name": "Consistente", "description": "Manteve uma sequência de 7 dias consecutivos", "category": "special", "rarity": "rare", "points_value": 40, "color": "#CDDC39"},
]

ACHIEVEMENT_TEMPLATES = [
    # Hours-based achievements
    {"name": "Primeiras 10 Horas", "description": "Complete 10 horas de voluntariado", "achievement_type": "hours_logged", "criteria": {"hours_required": 10}, "points_reward": 50},
    {"name": "50 Horas de Impacto", "description": "Complete 50 horas de voluntariado", "achievement_type": "hours_logged", "criteria": {"hours_required": 50}, "points_reward": 150},
    {"name": "Centurião Verde", "description": "Complete 100 horas de voluntariado", "achievement_type": "hours_logged", "criteria": {"hours_required": 100}, "points_reward": 300},
    {"name": "Mestre do Tempo", "description": "Complete 250 horas de voluntariado", "achievement_type": "hours_logged", "criteria": {"hours_required": 250}, "points_reward": 500},
    # Task-based achievements
    {"name": "Primeira Tarefa", "description": "Complete sua primeira tarefa", "achievement_type": "tasks_completed", "criteria": {"tasks_required": 1}, "points_reward": 25},
    {"name": "Realizador", "description": "Complete 10 tarefas", "achievement_type": "tasks_completed", "criteria": {"tasks_required": 10}, "points_reward": 100},
    {"name": "Super Realizador", "description": "Complete 50 tarefas", "achievement_type": "tasks_completed", "criteria": {"tasks_required": 50}, "points_reward": 250},
    # Project-based achievements
    {"name": "Primeiro Projeto", "description": "Participe de seu primeiro projeto", "achievement_type": "projects_completed", "criteria": {"projects_required": 1}, "points_reward": 30},
    {"name": "Explorador de Projetos", "description": "Participe de 5 projetos", "achievement_type": "projects_completed", "criteria": {"projects_required": 5}, "points_reward": 120},
    # Streak achievements
    {"name": "Semana Perfeita", "description": "Mantenha uma sequência de 7 dias", "achievement_type": "consecutive_days", "criteria": {"days_required": 7}, "points_reward": 75},
    {"name": "Mês de Dedicação", "description": "Mantenha uma sequência de 30 dias", "achievement_type": "consecutive_days", "criteria": {"days_required": 30}, "points_reward": 200},
    # Skill achievements
    {"name": "Primeira Habilidade", "description": "Adquira sua primeira habilidade", "achievement_type": "skills_acquired", "criteria": {"skills_required": 1}, "points_reward": 20},
    {"name": "Colecionador de Habilidades", "description": "Adquira 5 habilidades", "achievement_type": "skills_acquired", "criteria": {"skills_required": 5}, "points_reward": 100},
]

POINTS_EVENT_DESCRIPTIONS = [
    "Horas de voluntariado registradas",
    "Tarefa completada com sucesso",
    "Participação em projeto ambiental",
    "Treinamento concluído",
    "Conquista desbloqueada",
    "Insígnia conquistada",
    "Bônus de sequência diária",
    "Reconhecimento especial",
]

def generate_environmental_project_name():
    """Gera nome de projeto ambiental em português."""
    templates = [
        f"{random.choice(ADJETIVOS_AMBIENTAIS)} {random.choice(SUBSTANTIVOS_AMBIENTAIS)} - {random.choice(ACOES_AMBIENTAIS)}",
        f"{random.choice(TIPOS_PROJETO)}",
        f"Iniciativa {random.choice(ACOES_AMBIENTAIS)} {fake.city()}",
        f"Programa {random.choice(SUBSTANTIVOS_AMBIENTAIS)} {random.choice(ADJETIVOS_AMBIENTAIS)}"
    ]
    return random.choice(templates)

def generate_environmental_description():
    """Gera descrição de projeto ambiental em português."""
    templates = [
        f"Iniciativa comunitária para restaurar e proteger ecossistemas de {random.choice(SUBSTANTIVOS_AMBIENTAIS).lower()} através de atividades de {random.choice(ACOES_AMBIENTAIS).lower()} e engajamento voluntário.",
        f"Este projeto foca em criar soluções {random.choice(ADJETIVOS_AMBIENTAIS).lower()}s para conservação de {random.choice(SUBSTANTIVOS_AMBIENTAIS).lower()} e resiliência climática.",
        f"Trabalhando com comunidades locais para implementar práticas {random.choice(ADJETIVOS_AMBIENTAIS).lower()}s que melhoram a biodiversidade e saúde dos ecossistemas.",
        f"Programa abrangente de {random.choice(ACOES_AMBIENTAIS).lower()} visando a reabilitação de {random.choice(SUBSTANTIVOS_AMBIENTAIS).lower()} e sustentabilidade de longo prazo."
    ]
    return random.choice(templates)

def generate_task_title():
    """Gera título de tarefa ambiental em português."""
    return f"{random.choice(PREFIXOS_TAREFA)} {random.choice(OBJETOS_TAREFA)}"

def generate_volunteer_activity():
    """Gera descrição de atividade voluntária em português."""
    activity = random.choice(ATIVIDADES_VOLUNTARIO)
    number = random.randint(5, 100)
    return activity.format(number)

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class SeedingStats:
    """Track statistics during the seeding process."""

    def __init__(self):
        self.created = defaultdict(int)
        self.failed = defaultdict(int)
        self.assertions_passed = 0
        self.assertions_failed = 0
        self.errors = []

    def record_created(self, entity_type: str):
        self.created[entity_type] += 1

    def record_failed(self, entity_type: str, error: str, status_code: Optional[int] = None):
        self.failed[entity_type] += 1
        if status_code:
            self.errors.append(f"[{entity_type}] HTTP {status_code}: {error}")
        else:
            self.errors.append(f"[{entity_type}] {error}")

    def assert_true(self, condition: bool, message: str):
        """Assert a condition and track the result."""
        if condition:
            self.assertions_passed += 1
        else:
            self.assertions_failed += 1
            self.errors.append(f"ASSERTION FAILED: {message}")
            print(f"{Colors.RED}✗ Assertion failed: {message}{Colors.RESET}")

    def print_summary(self):
        """Print a summary of the seeding process."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}SEEDING SUMMARY{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*80}{Colors.RESET}\n")

        print(f"{Colors.BOLD}Entities Created:{Colors.RESET}")
        for entity_type, count in sorted(self.created.items()):
            print(f"  {Colors.GREEN}✓{Colors.RESET} {entity_type}: {count}")

        if self.failed:
            print(f"\n{Colors.BOLD}Entities Failed:{Colors.RESET}")
            for entity_type, count in sorted(self.failed.items()):
                print(f"  {Colors.RED}✗{Colors.RESET} {entity_type}: {count}")

        print(f"\n{Colors.BOLD}Assertions:{Colors.RESET}")
        print(f"  {Colors.GREEN}Passed:{Colors.RESET} {self.assertions_passed}")
        if self.assertions_failed > 0:
            print(f"  {Colors.RED}Failed:{Colors.RESET} {self.assertions_failed}")

        if self.errors:
            print(f"\n{Colors.BOLD}{Colors.RED}Errors:{Colors.RESET}")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  {Colors.RED}•{Colors.RESET} {error}")
            if len(self.errors) > 10:
                print(f"  {Colors.YELLOW}... and {len(self.errors) - 10} more errors{Colors.RESET}")

        print(f"\n{Colors.CYAN}{'='*80}{Colors.RESET}")

        # Return exit code based on success
        return 0 if self.assertions_failed == 0 and not self.failed else 1


class DataSeeder:
    """Main class for seeding data into the Repensar backend."""

    def __init__(self, api_url: str, dry_run: bool = False, verbose: bool = False, delay: float = 0.1):
        self.api_url = api_url.rstrip('/')
        self.dry_run = dry_run
        self.verbose = verbose
        self.delay = delay  # Delay between requests to avoid overwhelming the API
        self.client = httpx.Client(timeout=30.0)
        self.stats = SeedingStats()

        # Storage for created entities (for relationship validation)
        self.users = []
        self.volunteers = []
        self.projects = []
        self.tasks = []
        self.resources = []
        self.skills = []
        self.conversations = []
        self.badges = []
        self.achievements = []

        # Authentication tokens
        self.admin_token = None
        self.manager_token = None
        self.staff_token = None
        self.volunteer_token = None

        # Credential tracking for gen_creds.txt
        self.credentials = []

        # Error tracking per entity type (to limit console spam)
        self.error_counts = defaultdict(int)
        self.max_errors_per_type = 3  # Only show first 3 errors per entity type

        print(f"{Colors.BOLD}{Colors.BLUE}Repensar Data Seeding Script{Colors.RESET}")
        print(f"API URL: {Colors.CYAN}{self.api_url}{Colors.RESET}")
        print(f"Dry Run: {Colors.YELLOW if dry_run else Colors.GREEN}{dry_run}{Colors.RESET}")
        print(f"Verbose: {Colors.YELLOW if verbose else Colors.GREEN}{verbose}{Colors.RESET}\n")

    def _make_request(self, method: str, endpoint: str, entity_type: Optional[str] = None, **kwargs) -> Optional[httpx.Response]:
        """Make an HTTP request with error handling."""
        if self.dry_run and method.upper() not in ['GET', 'HEAD']:
            print(f"{Colors.YELLOW}[DRY RUN]{Colors.RESET} {method} {endpoint}")
            return None

        url = f"{self.api_url}{endpoint}"
        try:
            response = self.client.request(method, url, **kwargs)

            # Log errors for failed requests
            if response.status_code >= 400:
                # Check if we should log this error
                should_log = self.verbose
                if entity_type:
                    self.error_counts[entity_type] += 1
                    should_log = should_log or self.error_counts[entity_type] <= self.max_errors_per_type

                if should_log:
                    error_detail = ""
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("detail", str(error_json))
                    except:
                        error_detail = response.text[:200]  # First 200 chars

                    print(f"\n{Colors.RED}✗ {method} {endpoint} - Status {response.status_code}{Colors.RESET}")
                    print(f"  {Colors.YELLOW}Error: {error_detail}{Colors.RESET}")
                elif entity_type and self.error_counts[entity_type] == self.max_errors_per_type + 1:
                    print(f"\n{Colors.YELLOW}[Suppressing further {entity_type} errors...]{Colors.RESET}")

            return response
        except Exception as e:
            print(f"\n{Colors.RED}Request failed: {method} {endpoint}{Colors.RESET}")
            print(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")
            return None

    def _get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authorization headers with token."""
        return {"Authorization": f"Bearer {token}"}

    def _log_progress(self, entity_type: str, current: int, total: int):
        """Log progress for entity creation."""
        percentage = (current / total) * 100
        bar_length = 40
        filled = int(bar_length * current / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\r{Colors.CYAN}{entity_type}:{Colors.RESET} [{bar}] {current}/{total} ({percentage:.1f}%)", end='', flush=True)
        if current == total:
            print()  # New line when complete

    def authenticate_users(self):
        """Create and authenticate test users for different roles."""
        print(f"\n{Colors.BOLD}Step 1: Authenticating Users{Colors.RESET}")

        # Admin user
        admin_data = {
            "name": "Admin User",
            "email": "admin@repensar.org",
            "password": "AdminPass123!",
            "phone": "+1234567890",
            "user_type": "admin"
        }

        # Register admin (may fail if already exists, which is fine)
        response = self._make_request("POST", "/auth/register", json=admin_data)
        if response and response.status_code in [200, 201]:
            print(f"{Colors.GREEN}✓{Colors.RESET} Admin user registered")
            self.stats.record_created("Admin User")
            self.credentials.append({"type": "admin", "name": admin_data["name"], "email": admin_data["email"], "password": admin_data["password"]})
        elif response and response.status_code == 400:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Admin user already exists, attempting login")
            self.credentials.append({"type": "admin", "name": admin_data["name"], "email": admin_data["email"], "password": admin_data["password"]})
        else:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Admin registration returned status {response.status_code if response else 'None'}, attempting login anyway")

        # Login admin
        login_response = self._make_request("POST", "/auth/login", json={
            "email": admin_data["email"],
            "password": admin_data["password"]
        })

        if login_response and login_response.status_code == 200:
            self.admin_token = login_response.json()["access_token"]
            print(f"{Colors.GREEN}✓{Colors.RESET} Admin authenticated")
            self.stats.assert_true(self.admin_token is not None, "Admin token should be set")
        else:
            print(f"{Colors.RED}✗{Colors.RESET} Admin authentication failed - cannot proceed")
            self.stats.record_failed("Admin User", "Authentication failed")
            raise Exception("Failed to authenticate admin user. Please check credentials and API availability.")

        # Project Manager user
        manager_data = {
            "name": "Project Manager",
            "email": "manager@repensar.org",
            "password": "ManagerPass123!",
            "phone": "+1234567891",
            "user_type": "project_manager"
        }

        response = self._make_request("POST", "/auth/register", json=manager_data)
        if response and response.status_code in [200, 201]:
            print(f"{Colors.GREEN}✓{Colors.RESET} Manager user registered")
            self.stats.record_created("Manager User")
            self.credentials.append({"type": "project_manager", "name": manager_data["name"], "email": manager_data["email"], "password": manager_data["password"]})
        elif response and response.status_code == 400:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Manager user already exists, attempting login")
            self.credentials.append({"type": "project_manager", "name": manager_data["name"], "email": manager_data["email"], "password": manager_data["password"]})

        login_response = self._make_request("POST", "/auth/login", json={
            "email": manager_data["email"],
            "password": manager_data["password"]
        })

        if login_response and login_response.status_code == 200:
            self.manager_token = login_response.json()["access_token"]
            print(f"{Colors.GREEN}✓{Colors.RESET} Manager authenticated")
            self.stats.assert_true(self.manager_token is not None, "Manager token should be set")
        else:
            print(f"{Colors.RED}✗{Colors.RESET} Manager authentication failed - cannot proceed")
            raise Exception("Failed to authenticate manager user. Please check credentials and API availability.")

        # Staff Member user
        staff_data = {
            "name": "Staff Member",
            "email": "staff@repensar.org",
            "password": "StaffPass123!",
            "phone": "+1234567892",
            "user_type": "staff_member"
        }

        response = self._make_request("POST", "/auth/register", json=staff_data)
        if response and response.status_code in [200, 201]:
            print(f"{Colors.GREEN}✓{Colors.RESET} Staff user registered")
            self.stats.record_created("Staff User")
            self.credentials.append({"type": "staff_member", "name": staff_data["name"], "email": staff_data["email"], "password": staff_data["password"]})
        elif response and response.status_code == 400:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Staff user already exists, attempting login")
            self.credentials.append({"type": "staff_member", "name": staff_data["name"], "email": staff_data["email"], "password": staff_data["password"]})

        login_response = self._make_request("POST", "/auth/login", json={
            "email": staff_data["email"],
            "password": staff_data["password"]
        })

        if login_response and login_response.status_code == 200:
            self.staff_token = login_response.json()["access_token"]
            print(f"{Colors.GREEN}✓{Colors.RESET} Staff authenticated")
        else:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Staff authentication failed (non-critical, continuing)")

    def seed_users(self, count: int = 100):
        """Seed regular users."""
        print(f"\n{Colors.BOLD}Step 2: Seeding Users ({count} users){Colors.RESET}")

        user_types = ["staff_member", "volunteer"]

        for i in range(count):
            user_data = {
                "name": fake.name(),
                "email": fake.unique.email(),
                "password": "Password123!",
                "phone": fake.phone_number()[:15],
                "user_type": random.choice(user_types)
            }

            response = self._make_request("POST", "/auth/register", entity_type="User", json=user_data)

            if response and response.status_code in [200, 201]:
                user = response.json()
                self.users.append(user)
                self.stats.record_created("User")
                self.credentials.append({"type": user_data["user_type"], "name": user_data["name"], "email": user_data["email"], "password": user_data["password"]})
            else:
                status = response.status_code if response else None
                self.stats.record_failed("User", f"Failed to create user: {user_data['email']}", status)

            self._log_progress("Users", i + 1, count)

            # Add delay to avoid rate limiting
            if i < count - 1 and self.delay > 0:
                time.sleep(self.delay)

        self.stats.assert_true(len(self.users) >= count * 0.9, f"At least 90% of users should be created (expected {count * 0.9}, got {len(self.users)})")

        # Fetch all users to get their IDs (register endpoint doesn't return user object)
        print(f"{Colors.CYAN}Fetching created users...{Colors.RESET}")
        response = self._make_request(
            "GET",
            "/users/?page_size=100",
            entity_type="UserFetch",
            headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
        )
        if response and response.status_code == 200:
            response_data = response.json()
            fetched_users = response_data.get("items", [])
            # Filter out admin/manager/staff test users
            self.users = [u for u in fetched_users if u.get("email") not in [
                "admin@repensar.org", "manager@repensar.org", "staff@repensar.org"
            ]]
            print(f"{Colors.GREEN}✓{Colors.RESET} Fetched {len(self.users)} user records with IDs")
        else:
            print(f"{Colors.RED}✗{Colors.RESET} Failed to fetch users (status: {response.status_code if response else 'None'})")
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Project teams, milestones, and metrics will not be created")

    def seed_volunteers(self, count: int = 80):
        """Seed volunteers (linked to users)."""
        print(f"\n{Colors.BOLD}Step 3: Seeding Volunteers ({count} volunteers){Colors.RESET}")

        genders = ["male", "female", "non_binary", "prefer_not_to_say"]

        for i in range(count):
            # Register a new volunteer with user account (flat structure)
            volunteer_data = {
                "name": fake.name(),
                "email": fake.unique.email(),
                "password": "VolunteerPass123!",
                "phone": fake.phone_number()[:15],
                "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=70).isoformat(),
                "gender": random.choice(genders),
                "address": fake.street_address(),
                "city": fake.city(),
                "emergency_contact_name": fake.name(),
                "emergency_contact_phone": fake.phone_number()[:15]
            }

            response = self._make_request(
                "POST",
                "/volunteers/register",
                entity_type="Volunteer",
                json=volunteer_data,
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )

            if response and response.status_code in [200, 201]:
                volunteer = response.json()
                self.volunteers.append(volunteer)
                self.stats.record_created("Volunteer")
                self.credentials.append({"type": "volunteer", "name": volunteer_data["name"], "email": volunteer_data["email"], "password": volunteer_data["password"]})
            else:
                status = response.status_code if response else None
                self.stats.record_failed("Volunteer", f"Failed to create volunteer", status)

            self._log_progress("Volunteers", i + 1, count)

            # Add delay to avoid rate limiting
            if i < count - 1 and self.delay > 0:
                time.sleep(self.delay)

        self.stats.assert_true(len(self.volunteers) >= count * 0.9, f"At least 90% of volunteers should be created")

        # Fetch all volunteers to get their full details with IDs
        print(f"{Colors.CYAN}Fetching created volunteers...{Colors.RESET}")
        response = self._make_request(
            "GET",
            "/volunteers/?limit=100",
            entity_type="VolunteerFetch",
            headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
        )
        if response and response.status_code == 200:
            fetched_volunteers = response.json()
            # Update volunteers list with full details including database IDs
            if isinstance(fetched_volunteers, list) and len(fetched_volunteers) > 0:
                # Filter to only recently created volunteers (avoid old data)
                self.volunteers = fetched_volunteers[-count:] if len(fetched_volunteers) > count else fetched_volunteers
                print(f"{Colors.GREEN}✓{Colors.RESET} Fetched {len(self.volunteers)} volunteer records with IDs")
            else:
                print(f"{Colors.YELLOW}⚠{Colors.RESET} No volunteers found or unexpected response format")
        else:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Failed to fetch volunteers (status: {response.status_code if response else 'None'})")
            print(f"{Colors.YELLOW}  Skill assignments and time logs may fail{Colors.RESET}")

        # Validate volunteer-user relationship
        if self.volunteers:
            sample_volunteer = self.volunteers[0]
            volunteer_id = sample_volunteer.get("id")
            if volunteer_id:
                response = self._make_request(
                    "GET",
                    f"/volunteers/{volunteer_id}",
                    headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
                )
                if response and response.status_code == 200:
                    data = response.json()
                    self.stats.assert_true("user" in data or "user_id" in data, "Volunteer should have user relationship")

    def seed_volunteer_skills(self, count: int = 25):
        """Fetch existing volunteer skills (API doesn't support skill creation via HTTP)."""
        print(f"\n{Colors.BOLD}Step 4: Fetching Volunteer Skills{Colors.RESET}")

        # Try to fetch available skills from the API
        response = self._make_request(
            "GET",
            "/volunteers/skills/available?limit=100",
            headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
        )

        if response and response.status_code == 200:
            self.skills = response.json()
            print(f"{Colors.GREEN}✓{Colors.RESET} Fetched {len(self.skills)} existing skills")

            if len(self.skills) == 0:
                print(f"{Colors.YELLOW}⚠{Colors.RESET} No skills found in database. Skills need to be seeded via database migration or admin panel.")
                print(f"{Colors.YELLOW}  Skill assignments will be skipped.{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Failed to fetch skills. Skill assignments will be skipped.")

    def seed_volunteer_skill_assignments(self):
        """Assign skills to volunteers."""
        print(f"\n{Colors.BOLD}Step 5: Assigning Skills to Volunteers{Colors.RESET}")

        if not self.volunteers or not self.skills:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping skill assignments (no volunteers or skills)")
            return

        proficiency_levels = ["beginner", "intermediate", "advanced", "expert"]
        assignments_count = 0

        for volunteer in self.volunteers:
            volunteer_id = volunteer.get("id")
            if not volunteer_id:
                continue

            # Assign 2-5 random skills to each volunteer
            num_skills = random.randint(2, 5)
            selected_skills = random.sample(self.skills, min(num_skills, len(self.skills)))

            for skill in selected_skills:
                skill_id = skill.get("id")
                if not skill_id:
                    continue

                assignment_data = {
                    "skill_id": skill_id,
                    "proficiency_level": random.choice(proficiency_levels),
                    "years_experience": random.randint(0, 10),
                    "certified": random.choice([True, False])
                }

                response = self._make_request(
                    "POST",
                    f"/volunteers/{volunteer_id}/skills",
                    json=assignment_data,
                    headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
                )

                if response and response.status_code in [200, 201]:
                    assignments_count += 1
                    self.stats.record_created("VolunteerSkillAssignment")

        print(f"{Colors.GREEN}✓{Colors.RESET} Created {assignments_count} skill assignments")
        self.stats.assert_true(assignments_count > 0, "At least one skill assignment should be created")

        # Validate skill assignments for a sample volunteer
        if self.volunteers:
            sample_volunteer = self.volunteers[0]
            volunteer_id = sample_volunteer.get("id")
            response = self._make_request(
                "GET",
                f"/volunteers/{volunteer_id}/skills",
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )
            if response and response.status_code == 200:
                skills = response.json()
                self.stats.assert_true(isinstance(skills, list), "Volunteer skills should return a list")

    def seed_projects(self, count: int = 30):
        """Seed projects."""
        print(f"\n{Colors.BOLD}Step 6: Seeding Projects ({count} projects){Colors.RESET}")

        categories = [
            "reforestation", "environmental_education", "waste_management",
            "conservation", "research", "community_engagement", "climate_action",
            "biodiversity", "other"
        ]
        statuses = ["planning", "in_progress", "suspended", "completed", "cancelled"]
        priorities = ["low", "medium", "high", "critical"]

        for i in range(count):
            # Build project data, omitting None values
            requires_volunteers = random.choice([True, False])

            project_data = {
                "name": generate_environmental_project_name(),
                "description": generate_environmental_description(),
                "category": random.choice(categories),
                "status": random.choice(statuses),
                "priority": random.choice(priorities),
                "start_date": (date.today() - timedelta(days=random.randint(0, 365))).isoformat(),
                "end_date": (date.today() + timedelta(days=random.randint(30, 365))).isoformat(),
                "budget": round(random.uniform(5000, 100000), 2),
                "location_name": fake.city(),
                "latitude": float(fake.latitude()),
                "longitude": float(fake.longitude()),
                "requires_volunteers": requires_volunteers
            }

            # Only add min/max volunteers if the project requires volunteers
            if requires_volunteers:
                project_data["min_volunteers"] = random.randint(5, 10)
                project_data["max_volunteers"] = random.randint(20, 50)

            response = self._make_request(
                "POST",
                "/projects/",
                entity_type="Project",
                json=project_data,
                headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
            )

            if response and response.status_code in [200, 201]:
                project = response.json()
                self.projects.append(project)
                self.stats.record_created("Project")
            else:
                status = response.status_code if response else None
                self.stats.record_failed("Project", f"Failed to create project", status)

            self._log_progress("Projects", i + 1, count)

            # Add delay to avoid rate limiting
            if i < count - 1 and self.delay > 0:
                time.sleep(self.delay)

        self.stats.assert_true(len(self.projects) >= count * 0.9, f"At least 90% of projects should be created")

    def seed_project_teams(self):
        """Assign users to project teams."""
        print(f"\n{Colors.BOLD}Step 7: Creating Project Teams{Colors.RESET}")

        if not self.projects or not self.users:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping project teams (no projects or users)")
            return

        roles = ["Project Manager", "Team Lead", "Coordinator", "Member", "Specialist"]
        assignments_count = 0

        for project in self.projects:
            project_id = project.get("id")
            if not project_id:
                continue

            # Assign 3-8 team members to each project
            num_members = random.randint(3, 8)
            selected_users = random.sample(self.users, min(num_members, len(self.users)))

            for user in selected_users:
                user_id = user.get("id")
                if not user_id:
                    continue

                team_data = {
                    "user_id": user_id,
                    "role": random.choice(roles),
                    "is_volunteer": False,
                    "is_active": True
                }

                response = self._make_request(
                    "POST",
                    f"/projects/{project_id}/team",
                    json=team_data,
                    headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
                )

                if response and response.status_code in [200, 201]:
                    assignments_count += 1
                    self.stats.record_created("ProjectTeam")

        print(f"{Colors.GREEN}✓{Colors.RESET} Created {assignments_count} project team assignments")
        self.stats.assert_true(assignments_count > 0, "At least one project team assignment should be created")

    def seed_milestones(self):
        """Create project milestones."""
        print(f"\n{Colors.BOLD}Step 8: Creating Project Milestones{Colors.RESET}")

        if not self.projects:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping milestones (no projects)")
            return

        milestone_templates = [
            "Lançamento do Projeto", "Planejamento Concluído", "50% de Execução",
            "Avaliação de Impacto", "Revisão Final", "Projeto Concluído",
            "Primeira Colheita", "Meta de Plantio Atingida", "Certificação Ambiental"
        ]
        statuses = ["pending", "achieved", "missed", "cancelled"]
        milestones_count = 0

        for project in self.projects:
            project_id = project.get("id")
            if not project_id:
                continue

            # Create 2-4 milestones per project
            num_milestones = random.randint(2, 4)

            for j in range(num_milestones):
                milestone_data = {
                    "project_id": project_id,  # Required by schema
                    "name": random.choice(milestone_templates),
                    "description": f"Marco importante para {random.choice(ACOES_AMBIENTAIS).lower()} e {random.choice(['monitoramento', 'avaliação', 'expansão'])} do projeto.",
                    "target_date": (date.today() + timedelta(days=random.randint(30, 365))).isoformat(),
                    "status": random.choice(statuses)
                }

                response = self._make_request(
                    "POST",
                    f"/projects/{project_id}/milestones",
                    json=milestone_data,
                    headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
                )

                if response and response.status_code in [200, 201]:
                    milestones_count += 1
                    self.stats.record_created("Milestone")

        print(f"{Colors.GREEN}✓{Colors.RESET} Created {milestones_count} milestones")
        self.stats.assert_true(milestones_count > 0, "At least one milestone should be created")

    def seed_environmental_metrics(self):
        """Create environmental metrics for projects."""
        print(f"\n{Colors.BOLD}Step 9: Creating Environmental Metrics{Colors.RESET}")

        if not self.projects:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping environmental metrics (no projects)")
            return

        metric_types = [
            {"name": "Árvores Plantadas", "type": "count", "unit": "árvores"},
            {"name": "Carbono Compensado", "type": "measurement", "unit": "kg CO2"},
            {"name": "Resíduos Reciclados", "type": "measurement", "unit": "kg"},
            {"name": "Área Restaurada", "type": "measurement", "unit": "hectares"},
            {"name": "Água Economizada", "type": "measurement", "unit": "litros"},
            {"name": "Espécies Protegidas", "type": "count", "unit": "espécies"},
            {"name": "Mudas Distribuídas", "type": "count", "unit": "mudas"},
            {"name": "Voluntários Engajados", "type": "count", "unit": "pessoas"},
            {"name": "Biodiversidade Recuperada", "type": "measurement", "unit": "índice"}
        ]

        metrics_count = 0

        for project in self.projects:
            project_id = project.get("id")
            if not project_id:
                continue

            # Create 2-4 metrics per project
            num_metrics = random.randint(2, 4)
            selected_metrics = random.sample(metric_types, min(num_metrics, len(metric_types)))

            for metric_template in selected_metrics:
                metric_data = {
                    "project_id": project_id,  # Required by schema
                    "metric_name": metric_template["name"],
                    "metric_type": metric_template["type"],
                    "unit": metric_template["unit"],
                    "current_value": round(random.uniform(0, 1000), 2),
                    "target_value": round(random.uniform(1000, 5000), 2),
                    "measurement_date": date.today().isoformat()
                }

                response = self._make_request(
                    "POST",
                    f"/projects/{project_id}/metrics",
                    json=metric_data,
                    headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
                )

                if response and response.status_code in [200, 201]:
                    metrics_count += 1
                    self.stats.record_created("EnvironmentalMetric")

        print(f"{Colors.GREEN}✓{Colors.RESET} Created {metrics_count} environmental metrics")
        self.stats.assert_true(metrics_count > 0, "At least one environmental metric should be created")

    def seed_tasks(self, count: int = 150):
        """Seed tasks."""
        print(f"\n{Colors.BOLD}Step 10: Seeding Tasks ({count} tasks){Colors.RESET}")

        if not self.projects:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping tasks (no projects)")
            return

        statuses = ["not_started", "in_progress", "completed", "cancelled"]
        priorities = ["low", "medium", "high", "critical"]

        for i in range(count):
            project = random.choice(self.projects)
            project_id = project.get("id")

            # Ensure at least half the tasks are suitable for volunteers
            # First half are always suitable, second half are random
            suitable_for_volunteers = (i < count // 2) or random.choice([True, False])

            task_data = {
                "project_id": project_id,
                "title": generate_task_title(),
                "description": generate_environmental_description(),
                "status": random.choice(statuses),
                "priority": random.choice(priorities),
                "suitable_for_volunteers": suitable_for_volunteers,
                "volunteer_spots": random.randint(1, 10) if suitable_for_volunteers else 0,
                "estimated_hours": round(random.uniform(1, 40), 1),
                "start_date": (date.today() + timedelta(days=random.randint(0, 30))).isoformat(),
                "due_date": (date.today() + timedelta(days=random.randint(30, 90))).isoformat()
            }

            response = self._make_request(
                "POST",
                "/tasks/",
                entity_type="Task",
                json=task_data,
                headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
            )

            if response and response.status_code in [200, 201]:
                task = response.json()
                self.tasks.append(task)
                self.stats.record_created("Task")
            else:
                status = response.status_code if response else None
                self.stats.record_failed("Task", f"Failed to create task", status)

            self._log_progress("Tasks", i + 1, count)

            # Add delay to avoid rate limiting
            if i < count - 1 and self.delay > 0:
                time.sleep(self.delay)

        self.stats.assert_true(len(self.tasks) >= count * 0.9, f"At least 90% of tasks should be created")

        # Validate task-project relationship
        if self.tasks:
            sample_task = self.tasks[0]
            task_id = sample_task.get("id")
            response = self._make_request(
                "GET",
                f"/tasks/{task_id}",
                headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
            )
            if response and response.status_code == 200:
                data = response.json()
                self.stats.assert_true("project_id" in data, "Task should have project_id")

    def seed_task_volunteers(self):
        """Assign volunteers to tasks."""
        print(f"\n{Colors.BOLD}Step 11: Assigning Volunteers to Tasks{Colors.RESET}")

        if not self.tasks or not self.volunteers:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping task volunteers (no tasks or volunteers)")
            return

        assignments_count = 0

        # Filter tasks suitable for volunteers
        volunteer_tasks = [t for t in self.tasks if t.get("suitable_for_volunteers")]
        print(f"{Colors.CYAN}Found {len(volunteer_tasks)} tasks suitable for volunteers{Colors.RESET}")

        if not volunteer_tasks:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} No tasks marked as suitable for volunteers")
            return

        for task in volunteer_tasks:
            task_id = task.get("id")
            if not task_id:
                continue

            # Assign 1-3 volunteers to each task (reduced to avoid duplicate assignments)
            num_volunteers = random.randint(1, min(3, len(self.volunteers)))
            selected_volunteers = random.sample(self.volunteers, num_volunteers)

            for volunteer in selected_volunteers:
                volunteer_id = volunteer.get("id")
                if not volunteer_id:
                    continue

                # API only accepts volunteer_id for TaskVolunteerCreate
                assignment_data = {
                    "volunteer_id": volunteer_id
                }

                response = self._make_request(
                    "POST",
                    f"/tasks/{task_id}/volunteers",
                    entity_type="TaskVolunteer",
                    json=assignment_data,
                    headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
                )

                if response and response.status_code in [200, 201]:
                    assignments_count += 1
                    self.stats.record_created("TaskVolunteer")

        print(f"{Colors.GREEN}✓{Colors.RESET} Created {assignments_count} task-volunteer assignments")
        if volunteer_tasks:
            self.stats.assert_true(assignments_count > 0, "At least one task-volunteer assignment should be created")

    def seed_task_dependencies(self):
        """Create task dependencies."""
        print(f"\n{Colors.BOLD}Step 12: Creating Task Dependencies{Colors.RESET}")

        if len(self.tasks) < 10:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping task dependencies (not enough tasks)")
            return

        dependency_types = ["finish_to_start", "start_to_start", "finish_to_finish", "start_to_finish"]
        dependencies_count = 0

        # Create dependencies for about 20% of tasks
        num_dependencies = len(self.tasks) // 5

        for _ in range(num_dependencies):
            # Pick two random tasks
            task1, task2 = random.sample(self.tasks, 2)
            task1_id = task1.get("id")
            task2_id = task2.get("id")

            if not task1_id or not task2_id:
                continue

            dependency_data = {
                "successor_task_id": task2_id,
                "dependency_type": random.choice(dependency_types)
            }

            response = self._make_request(
                "POST",
                f"/tasks/{task1_id}/dependencies",
                json=dependency_data,
                headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
            )

            if response and response.status_code in [200, 201]:
                dependencies_count += 1
                self.stats.record_created("TaskDependency")

        print(f"{Colors.GREEN}✓{Colors.RESET} Created {dependencies_count} task dependencies")

    def seed_resources(self, count: int = 50):
        """Seed resources."""
        print(f"\n{Colors.BOLD}Step 13: Seeding Resources ({count} resources){Colors.RESET}")

        resource_types = ["human", "equipment", "material", "financial"]

        resource_templates = {
            "human": ["Coordenador Ambiental", "Supervisor de Campo", "Especialista em Biodiversidade", "Educador Ambiental"],
            "equipment": ["GPS para Mapeamento", "Câmera Trap", "Kit Análise de Água", "Ferramentas de Plantio", "Veículo 4x4"],
            "material": ["Sementes Nativas", "Mudas Florestais", "Adubo Orgânico", "Composto", "Cobertura Morta", "Substrato"],
            "financial": ["Financiamento Verde", "Doação Ambiental", "Patrocínio Sustentável", "Fundo Conservação"]
        }

        for i in range(count):
            resource_type = random.choice(resource_types)

            resource_data = {
                "name": random.choice(resource_templates[resource_type]),
                "type": resource_type,
                "description": f"Recurso essencial para {random.choice(ACOES_AMBIENTAIS).lower()} e {random.choice(['conservação', 'monitoramento', 'educação'])} ambiental.",
                "unit": random.choice(["unidade", "kg", "litros", "horas", "BRL"]),
                "unit_cost": round(random.uniform(10, 1000), 2) if resource_type != "human" else None,
                "available_quantity": round(random.uniform(10, 500), 2),
                "location": fake.city(),
                "is_active": True
            }

            response = self._make_request(
                "POST",
                "/resources/",
                entity_type="Resource",
                json=resource_data,
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )

            if response and response.status_code in [200, 201]:
                resource = response.json()
                self.resources.append(resource)
                self.stats.record_created("Resource")
            else:
                status = response.status_code if response else None
                self.stats.record_failed("Resource", f"Failed to create resource", status)

            self._log_progress("Resources", i + 1, count)

            # Add delay to avoid rate limiting
            if i < count - 1 and self.delay > 0:
                time.sleep(self.delay)

        self.stats.assert_true(len(self.resources) >= count * 0.9, f"At least 90% of resources should be created")

    def seed_project_resources(self):
        """Allocate resources to projects."""
        print(f"\n{Colors.BOLD}Step 14: Allocating Resources to Projects{Colors.RESET}")

        if not self.projects or not self.resources:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping project resources (no projects or resources)")
            return

        allocations_count = 0

        for project in self.projects:
            project_id = project.get("id")
            if not project_id:
                continue

            # Allocate 3-8 resources to each project
            num_resources = random.randint(3, 8)
            selected_resources = random.sample(self.resources, min(num_resources, len(self.resources)))

            for resource in selected_resources:
                resource_id = resource.get("id")
                if not resource_id:
                    continue

                allocation_data = {
                    "resource_id": resource_id,
                    "quantity_allocated": round(random.uniform(1, 50), 2),
                    "quantity_used": round(random.uniform(0, 30), 2),
                    "allocation_date": date.today().isoformat()
                }

                response = self._make_request(
                    "POST",
                    f"/resources/projects/{project_id}/resources",
                    json=allocation_data,
                    headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
                )

                if response and response.status_code in [200, 201]:
                    allocations_count += 1
                    self.stats.record_created("ProjectResource")

        print(f"{Colors.GREEN}✓{Colors.RESET} Created {allocations_count} resource allocations")
        self.stats.assert_true(allocations_count > 0, "At least one resource allocation should be created")

    def seed_volunteer_time_logs(self, count: int = 500):
        """Seed volunteer time logs."""
        print(f"\n{Colors.BOLD}Step 15: Seeding Volunteer Time Logs ({count} logs){Colors.RESET}")

        if not self.volunteers:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping time logs (no volunteers)")
            return

        for i in range(count):
            volunteer = random.choice(self.volunteers)
            volunteer_id = volunteer.get("id")

            # Randomly select a task (if available)
            task_id = None
            project_id = None

            if self.tasks and random.choice([True, False]):
                task = random.choice(self.tasks)
                task_id = task.get("id")
                project_id = task.get("project_id")
            elif self.projects:
                project = random.choice(self.projects)
                project_id = project.get("id")

            log_data = {
                "volunteer_id": volunteer_id,
                "date": (date.today() - timedelta(days=random.randint(0, 365))).isoformat(),
                "hours": round(random.uniform(1, 8), 2),
                "activity_description": generate_volunteer_activity()
            }

            if task_id:
                log_data["task_id"] = task_id
            if project_id:
                log_data["project_id"] = project_id

            response = self._make_request(
                "POST",
                f"/volunteers/{volunteer_id}/hours",
                json=log_data,
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )

            if response and response.status_code in [200, 201]:
                self.stats.record_created("VolunteerTimeLog")
            else:
                status = response.status_code if response else None
                self.stats.record_failed("VolunteerTimeLog", f"Failed to create time log", status)

            self._log_progress("Time Logs", i + 1, count)

            # Add delay to avoid rate limiting
            if i < count - 1 and self.delay > 0:
                time.sleep(self.delay)

        # Validate time logs for a sample volunteer
        if self.volunteers:
            sample_volunteer = self.volunteers[0]
            volunteer_id = sample_volunteer.get("id")
            response = self._make_request(
                "GET",
                f"/volunteers/{volunteer_id}/hours",
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )
            if response and response.status_code == 200:
                logs = response.json()
                self.stats.assert_true(isinstance(logs, (list, dict)), "Time logs should return a list or paginated object")

    def seed_notifications(self, count: int = 100):
        """Seed notifications."""
        print(f"\n{Colors.BOLD}Step 16: Seeding Notifications ({count} notifications){Colors.RESET}")

        if not self.users:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping notifications (no users)")
            return

        notification_types = ["info", "success", "warning", "error"]

        notification_templates = [
            {"title": "Bem-vindo!", "message": "Bem-vindo à plataforma Repensar! Juntos por um futuro sustentável.", "type": "info"},
            {"title": "Nova Tarefa Ambiental", "message": "Você foi designado para uma nova atividade de conservação.", "type": "info"},
            {"title": "Horas Aprovadas", "message": "Suas horas voluntárias foram aprovadas. Obrigado pelo seu impacto positivo!", "type": "success"},
            {"title": "Atualização de Projeto", "message": "Um projeto ambiental que você participa foi atualizado.", "type": "info"},
            {"title": "Lembrete", "message": "Não esqueça de registrar suas horas de voluntariado.", "type": "warning"},
            {"title": "Meta Alcançada!", "message": "Parabéns! Seu projeto atingiu uma meta ambiental importante.", "type": "success"},
            {"title": "Novo Plantio", "message": "Uma nova atividade de plantio está disponível na sua região.", "type": "info"}
        ]

        for i in range(count):
            user = random.choice(self.users)
            user_id = user.get("id")

            template = random.choice(notification_templates)

            notification_data = {
                "user_id": user_id,
                "title": template["title"],
                "message": template["message"],
                "type": template["type"],
                "project_id": random.choice(self.projects).get("id") if self.projects and random.choice([True, False]) else None,
                "task_id": random.choice(self.tasks).get("id") if self.tasks and random.choice([True, False]) else None
            }

            response = self._make_request(
                "POST",
                "/notifications/create",
                json=notification_data,
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )

            if response and response.status_code in [200, 201]:
                self.stats.record_created("Notification")
            else:
                status = response.status_code if response else None
                self.stats.record_failed("Notification", f"Failed to create notification", status)

            self._log_progress("Notifications", i + 1, count)

            # Add delay to avoid rate limiting
            if i < count - 1 and self.delay > 0:
                time.sleep(self.delay)

    def validate_relationships(self):
        """Perform comprehensive relationship validation."""
        print(f"\n{Colors.BOLD}Step 17: Validating Relationships{Colors.RESET}")

        # Validate volunteer-user relationship
        if self.volunteers:
            print(f"{Colors.CYAN}Validating Volunteer → User relationship...{Colors.RESET}")
            volunteer = self.volunteers[0]
            volunteer_id = volunteer.get("id")
            response = self._make_request(
                "GET",
                f"/volunteers/{volunteer_id}",
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )
            if response and response.status_code == 200:
                data = response.json()
                has_user = "user" in data or "user_id" in data
                self.stats.assert_true(has_user, "Volunteer should have user relationship")
                print(f"{Colors.GREEN}✓{Colors.RESET} Volunteer → User relationship validated")

        # Validate volunteer skills
        if self.volunteers and self.skills:
            print(f"{Colors.CYAN}Validating Volunteer → Skills relationship...{Colors.RESET}")
            volunteer = self.volunteers[0]
            volunteer_id = volunteer.get("id")
            response = self._make_request(
                "GET",
                f"/volunteers/{volunteer_id}/skills",
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )
            if response and response.status_code == 200:
                data = response.json()
                self.stats.assert_true(isinstance(data, list), "Volunteer skills should return a list")
                print(f"{Colors.GREEN}✓{Colors.RESET} Volunteer → Skills relationship validated")

        # Validate project-task relationship
        if self.projects and self.tasks:
            print(f"{Colors.CYAN}Validating Project → Tasks relationship...{Colors.RESET}")
            project = self.projects[0]
            project_id = project.get("id")
            response = self._make_request(
                "GET",
                f"/projects/{project_id}/tasks",
                headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
            )
            if response and response.status_code == 200:
                data = response.json()
                self.stats.assert_true(isinstance(data, (list, dict)), "Project tasks should return a list or paginated object")
                print(f"{Colors.GREEN}✓{Colors.RESET} Project → Tasks relationship validated")

        # Validate project team
        if self.projects:
            print(f"{Colors.CYAN}Validating Project → Team relationship...{Colors.RESET}")
            project = self.projects[0]
            project_id = project.get("id")
            response = self._make_request(
                "GET",
                f"/projects/{project_id}/team",
                headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
            )
            if response and response.status_code == 200:
                data = response.json()
                self.stats.assert_true(isinstance(data, list), "Project team should return a list")
                print(f"{Colors.GREEN}✓{Colors.RESET} Project → Team relationship validated")

        # Validate task-volunteers relationship
        if self.tasks:
            print(f"{Colors.CYAN}Validating Task → Volunteers relationship...{Colors.RESET}")
            # Find a task that should have volunteers
            for task in self.tasks:
                if task.get("suitable_for_volunteers"):
                    task_id = task.get("id")
                    response = self._make_request(
                        "GET",
                        f"/tasks/{task_id}/volunteers",
                        headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
                    )
                    if response and response.status_code == 200:
                        data = response.json()
                        self.stats.assert_true(isinstance(data, list), "Task volunteers should return a list")
                        print(f"{Colors.GREEN}✓{Colors.RESET} Task → Volunteers relationship validated")
                        break

        # Validate volunteer time logs
        if self.volunteers:
            print(f"{Colors.CYAN}Validating Volunteer → Time Logs relationship...{Colors.RESET}")
            volunteer = self.volunteers[0]
            volunteer_id = volunteer.get("id")
            response = self._make_request(
                "GET",
                f"/volunteers/{volunteer_id}/hours",
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )
            if response and response.status_code == 200:
                data = response.json()
                self.stats.assert_true(isinstance(data, (list, dict)), "Volunteer hours should return a list or paginated object")
                print(f"{Colors.GREEN}✓{Colors.RESET} Volunteer → Time Logs relationship validated")

        # Validate project resources
        if self.projects:
            print(f"{Colors.CYAN}Validating Project → Resources relationship...{Colors.RESET}")
            project = self.projects[0]
            project_id = project.get("id")
            response = self._make_request(
                "GET",
                f"/projects/{project_id}/resources",
                headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
            )
            if response and response.status_code == 200:
                data = response.json()
                self.stats.assert_true(isinstance(data, list), "Project resources should return a list")
                print(f"{Colors.GREEN}✓{Colors.RESET} Project → Resources relationship validated")

        # Validate project milestones
        if self.projects:
            print(f"{Colors.CYAN}Validating Project → Milestones relationship...{Colors.RESET}")
            project = self.projects[0]
            project_id = project.get("id")
            response = self._make_request(
                "GET",
                f"/projects/{project_id}/milestones",
                headers=self._get_auth_headers(self.manager_token) if self.manager_token else {}
            )
            if response and response.status_code == 200:
                data = response.json()
                self.stats.assert_true(isinstance(data, list), "Project milestones should return a list")
                print(f"{Colors.GREEN}✓{Colors.RESET} Project → Milestones relationship validated")

    # ============================================================
    # GAMIFICATION SEEDING
    # ============================================================

    def seed_badges(self):
        """Seed badge definitions."""
        print(f"\n{Colors.BOLD}Step 18: Seeding Badges ({len(BADGE_TEMPLATES)} badges){Colors.RESET}")

        for i, badge_data in enumerate(BADGE_TEMPLATES):
            response = self._make_request(
                "POST",
                "/gamification/badges",
                entity_type="Badge",
                json=badge_data,
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )

            if response and response.status_code in [200, 201]:
                badge = response.json()
                self.badges.append(badge)
                self.stats.record_created("Badge")
            elif response and response.status_code == 400:
                # Badge might already exist, try to fetch it
                pass
            else:
                status = response.status_code if response else None
                self.stats.record_failed("Badge", f"Failed to create badge: {badge_data['name']}", status)

            self._log_progress("Badges", i + 1, len(BADGE_TEMPLATES))

        # Fetch all badges to get their IDs
        response = self._make_request(
            "GET",
            "/gamification/badges?limit=100",
            headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
        )
        if response and response.status_code == 200:
            self.badges = response.json()
            print(f"{Colors.GREEN}✓{Colors.RESET} Fetched {len(self.badges)} badges")

    def seed_achievements(self):
        """Seed achievement definitions."""
        print(f"\n{Colors.BOLD}Step 19: Seeding Achievements ({len(ACHIEVEMENT_TEMPLATES)} achievements){Colors.RESET}")

        for i, achievement_data in enumerate(ACHIEVEMENT_TEMPLATES):
            # Optionally link to a badge
            if self.badges and random.choice([True, False]):
                matching_badges = [b for b in self.badges if b.get("category") == "time" or b.get("rarity") == "common"]
                if matching_badges:
                    achievement_data = {**achievement_data, "badge_id": random.choice(matching_badges).get("id")}

            response = self._make_request(
                "POST",
                "/gamification/achievements",
                entity_type="Achievement",
                json=achievement_data,
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )

            if response and response.status_code in [200, 201]:
                achievement = response.json()
                self.achievements.append(achievement)
                self.stats.record_created("Achievement")
            elif response and response.status_code == 400:
                # Achievement might already exist
                pass
            else:
                status = response.status_code if response else None
                self.stats.record_failed("Achievement", f"Failed to create achievement: {achievement_data['name']}", status)

            self._log_progress("Achievements", i + 1, len(ACHIEVEMENT_TEMPLATES))

        # Fetch all achievements to get their IDs
        response = self._make_request(
            "GET",
            "/gamification/achievements?limit=100",
            headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
        )
        if response and response.status_code == 200:
            self.achievements = response.json()
            print(f"{Colors.GREEN}✓{Colors.RESET} Fetched {len(self.achievements)} achievements")

    def seed_volunteer_badges(self):
        """Award badges to volunteers."""
        print(f"\n{Colors.BOLD}Step 20: Awarding Badges to Volunteers{Colors.RESET}")

        if not self.volunteers or not self.badges:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping badge awards (no volunteers or badges)")
            return

        awards_count = 0
        common_badges = [b for b in self.badges if b.get("rarity") == "common"]
        rare_badges = [b for b in self.badges if b.get("rarity") == "rare"]

        for volunteer in self.volunteers:
            volunteer_id = volunteer.get("id")
            if not volunteer_id:
                continue

            # Award 1-3 common badges to each volunteer
            num_badges = random.randint(1, min(3, len(common_badges)))
            selected_badges = random.sample(common_badges, num_badges) if common_badges else []

            # Some volunteers also get rare badges
            if random.random() < 0.3 and rare_badges:
                selected_badges.append(random.choice(rare_badges))

            for badge in selected_badges:
                badge_id = badge.get("id")
                if not badge_id:
                    continue

                award_data = {
                    "badge_id": badge_id,
                    "earned_reason": f"Reconhecimento por {random.choice(['dedicação', 'contribuição', 'participação', 'esforço'])} em atividades ambientais"
                }

                response = self._make_request(
                    "POST",
                    f"/gamification/volunteers/{volunteer_id}/badges/award",
                    json=award_data,
                    headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
                )

                if response and response.status_code in [200, 201]:
                    awards_count += 1
                    self.stats.record_created("VolunteerBadge")

        print(f"{Colors.GREEN}✓{Colors.RESET} Awarded {awards_count} badges to volunteers")
        self.stats.assert_true(awards_count > 0, "At least one badge should be awarded")

    def seed_volunteer_points(self):
        """Award points to volunteers and create points history."""
        print(f"\n{Colors.BOLD}Step 21: Awarding Points to Volunteers{Colors.RESET}")

        if not self.volunteers:
            print(f"{Colors.YELLOW}⚠{Colors.RESET} Skipping points awards (no volunteers)")
            return

        points_count = 0
        event_types = ["hours_logged", "task_completed", "project_completed", "achievement_earned", "manual_adjustment"]

        for volunteer in self.volunteers:
            volunteer_id = volunteer.get("id")
            if not volunteer_id:
                continue

            # Award 3-8 points entries to each volunteer
            num_awards = random.randint(3, 8)

            for _ in range(num_awards):
                points_data = {
                    "points": random.randint(5, 100),
                    "event_type": random.choice(event_types),
                    "description": random.choice(POINTS_EVENT_DESCRIPTIONS),
                    "reference_type": random.choice(["task", "project", "training", None])
                }

                # Add reference_id if reference_type is set
                if points_data["reference_type"] == "task" and self.tasks:
                    points_data["reference_id"] = random.choice(self.tasks).get("id")
                elif points_data["reference_type"] == "project" and self.projects:
                    points_data["reference_id"] = random.choice(self.projects).get("id")
                else:
                    points_data["reference_type"] = None

                response = self._make_request(
                    "POST",
                    f"/gamification/volunteers/{volunteer_id}/points/award",
                    json=points_data,
                    headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
                )

                if response and response.status_code in [200, 201]:
                    points_count += 1
                    self.stats.record_created("PointsAward")

            # Add delay to avoid rate limiting
            if self.delay > 0:
                time.sleep(self.delay)

        print(f"{Colors.GREEN}✓{Colors.RESET} Created {points_count} points awards")
        self.stats.assert_true(points_count > 0, "At least one points award should be created")

    def seed_leaderboards(self):
        """Generate leaderboards."""
        print(f"\n{Colors.BOLD}Step 22: Generating Leaderboards{Colors.RESET}")

        response = self._make_request(
            "POST",
            "/gamification/leaderboards/generate",
            headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
        )

        if response and response.status_code == 200:
            result = response.json()
            print(f"{Colors.GREEN}✓{Colors.RESET} {result.get('message', 'Leaderboards generated')}")
            self.stats.record_created("Leaderboard")
        else:
            status = response.status_code if response else None
            self.stats.record_failed("Leaderboard", "Failed to generate leaderboards", status)

    def validate_gamification(self):
        """Validate gamification data."""
        print(f"\n{Colors.BOLD}Step 23: Validating Gamification Data{Colors.RESET}")

        # Validate volunteer points
        if self.volunteers:
            print(f"{Colors.CYAN}Validating Volunteer → Points relationship...{Colors.RESET}")
            volunteer = self.volunteers[0]
            volunteer_id = volunteer.get("id")
            response = self._make_request(
                "GET",
                f"/gamification/volunteers/{volunteer_id}/points",
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )
            if response and response.status_code == 200:
                data = response.json()
                self.stats.assert_true("total_points" in data, "Volunteer should have points data")
                print(f"{Colors.GREEN}✓{Colors.RESET} Volunteer → Points relationship validated")

        # Validate volunteer badges
        if self.volunteers:
            print(f"{Colors.CYAN}Validating Volunteer → Badges relationship...{Colors.RESET}")
            volunteer = self.volunteers[0]
            volunteer_id = volunteer.get("id")
            response = self._make_request(
                "GET",
                f"/gamification/volunteers/{volunteer_id}/badges",
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )
            if response and response.status_code == 200:
                data = response.json()
                self.stats.assert_true("badges" in data or isinstance(data, list), "Volunteer should have badges data")
                print(f"{Colors.GREEN}✓{Colors.RESET} Volunteer → Badges relationship validated")

        # Validate gamification stats (admin)
        print(f"{Colors.CYAN}Validating Gamification Stats endpoint...{Colors.RESET}")
        response = self._make_request(
            "GET",
            "/gamification/stats",
            headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
        )
        if response and response.status_code == 200:
            data = response.json()
            self.stats.assert_true("total_badges" in data, "Stats should include total_badges")
            self.stats.assert_true("total_achievements" in data, "Stats should include total_achievements")
            print(f"{Colors.GREEN}✓{Colors.RESET} Gamification Stats endpoint validated")

        # Validate volunteer gamification summary
        if self.volunteers:
            print(f"{Colors.CYAN}Validating Volunteer Gamification Summary...{Colors.RESET}")
            volunteer = self.volunteers[0]
            volunteer_id = volunteer.get("id")
            response = self._make_request(
                "GET",
                f"/gamification/stats/volunteer/{volunteer_id}",
                headers=self._get_auth_headers(self.admin_token) if self.admin_token else {}
            )
            if response and response.status_code == 200:
                data = response.json()
                self.stats.assert_true("volunteer_id" in data, "Summary should include volunteer_id")
                self.stats.assert_true("badges_earned" in data, "Summary should include badges_earned")
                print(f"{Colors.GREEN}✓{Colors.RESET} Volunteer Gamification Summary validated")

    def run(self, test_mode: bool = False):
        """Execute the complete seeding process.

        Args:
            test_mode: If True, use minimal counts for quick testing
        """
        # Set counts based on mode
        if test_mode:
            print(f"{Colors.YELLOW}Running in TEST MODE with minimal data{Colors.RESET}\n")
            user_count = 5
            volunteer_count = 5
            project_count = 3
            task_count = 10
            resource_count = 5
            time_log_count = 10
            notification_count = 5
        else:
            user_count = 50
            volunteer_count = 40
            project_count = 20
            task_count = 80
            resource_count = 30
            time_log_count = 200
            notification_count = 50

        try:
            self.authenticate_users()
            self.seed_users(user_count)
            self.seed_volunteers(volunteer_count)
            self.seed_volunteer_skills(25)
            self.seed_volunteer_skill_assignments()
            self.seed_projects(project_count)
            self.seed_project_teams()
            self.seed_milestones()
            self.seed_environmental_metrics()
            self.seed_tasks(task_count)
            self.seed_task_volunteers()
            self.seed_task_dependencies()
            self.seed_resources(resource_count)
            self.seed_project_resources()
            self.seed_volunteer_time_logs(time_log_count)
            self.seed_notifications(notification_count)
            self.validate_relationships()

            # Gamification seeding
            self.seed_badges()
            self.seed_achievements()
            self.seed_volunteer_badges()
            self.seed_volunteer_points()
            self.seed_leaderboards()
            self.validate_gamification()

            # Save credentials to file
            self.save_credentials()

            # Print summary and return exit code
            return self.stats.print_summary()

        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Seeding interrupted by user{Colors.RESET}")
            return 1
        except Exception as e:
            print(f"\n\n{Colors.RED}Fatal error during seeding:{Colors.RESET}")
            print(f"{Colors.RED}{str(e)}{Colors.RESET}")
            return 1
        finally:
            self.client.close()

    def save_credentials(self):
        """Save generated credentials to gen_creds.txt."""
        if not self.credentials:
            return

        creds_file = Path(__file__).parent.parent / "gen_creds.txt"

        print(f"\n{Colors.BOLD}Saving credentials to gen_creds.txt{Colors.RESET}")

        with open(creds_file, "w") as f:
            f.write("=" * 70 + "\n")
            f.write("GENERATED CREDENTIALS - Repensar Seeding Script\n")
            f.write(f"Generated at: {datetime.now().isoformat()}\n")
            f.write("=" * 70 + "\n\n")

            # Group by type
            by_type = defaultdict(list)
            for cred in self.credentials:
                by_type[cred["type"]].append(cred)

            for user_type, creds in by_type.items():
                f.write(f"--- {user_type.upper()} ({len(creds)}) ---\n")
                for cred in creds:
                    f.write(f"  Name: {cred['name']}\n")
                    f.write(f"  Email: {cred['email']}\n")
                    f.write(f"  Password: {cred['password']}\n")
                    f.write("\n")
                f.write("\n")

        print(f"{Colors.GREEN}✓{Colors.RESET} Saved {len(self.credentials)} credentials to {creds_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed the Repensar backend with comprehensive mock data"
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_URL", "http://localhost:8000"),
        help="Base URL for the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without actually creating data"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show all error messages (default: show first 3 per entity type)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay in seconds between requests (default: 0.1, increase if hitting rate limits)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run with minimal data for quick testing (5 users, 5 volunteers, 3 projects, etc.)"
    )

    args = parser.parse_args()

    seeder = DataSeeder(
        api_url=args.api_url,
        dry_run=args.dry_run,
        verbose=args.verbose,
        delay=args.delay
    )
    exit_code = seeder.run(test_mode=args.test)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
