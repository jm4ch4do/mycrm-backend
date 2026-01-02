# CRM Project (Django + DRF + Postgres)

## Overview

This project is a **full-stack CRM system** built with Django, Django REST Framework (DRF), and PostgreSQL.  
It is designed as a **single-database, multi-app Django project** with domain-focused apps:

- **core** – CRM Core (Accounts, Contacts, Deals, Ownership)  
- **activities** – Engagement & timeline (interactions, notes, meetings, calls)  
- **automation** – Rules & workflows (triggers, automatic tasks, notifications)

The architecture leverages **Django-native features** to learn real-world best practices: models, managers, services, signals, DRF serializers/viewsets, permissions, and admin.

---

## Features

### CRM Core (`core` app)

- **Account entity** – Companies/organizations
- **Contacts** – People associated with Accounts
- **Deals** – Sales opportunities, pipelines, stages
- **Ownership & lifecycle tracking** – Created/updated by, owner assignment
- **Soft delete** – Non-destructive deletion
- **API endpoints** – CRUD, filtering, pagination
- **Admin interface** – List display, search, filters
- **Signals** – Domain events (prepared for future Kafka integration)

### Activities (`activities` app)

- Interaction tracking: meetings, calls, notes
- Timeline for accounts, contacts, and deals
- CRUD API endpoints

### Automation (`automation` app)

- Business rules and workflow triggers
- Notifications and automated tasks
- Kafka-ready event handling

---

## Tech Stack

- Python 3.11+  
- Django 5.x  
- Django REST Framework  
- PostgreSQL  
- DRF Filters & Pagination  
- Django Admin for internal UI  

---

## Getting Started

### 1. Clone Repository

```bash
git clone <repository_url>
cd crm-project
