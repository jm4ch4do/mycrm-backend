# Architecture Overview

## Request/Response Flow

### Incoming Request (JSON → Database)

```text
HTTP REQUEST (JSON)
    ↓
URL Router (core/api/urls.py)
    ↓
ViewSet (core/api/views/)
    ↓
Serializer (core/api/serializers/) - DESERIALIZE & VALIDATE
    ↓
Service (core/services/domain/) - BUSINESS LOGIC
    ↓
Manager (core/managers/) - CUSTOM QUERIES
    ↓
Model (core/models/) - ORM & CONSTRAINTS
    ↓
DATABASE (Persistent Storage)
```

### Outgoing Response (Database → JSON)

```text
DATABASE
    ↓
Model (return object)
    ↓
Service (process/enrich if needed)
    ↓
Serializer - SERIALIZE to JSON
    ↓
ViewSet (format HTTP response)
    ↓
HTTP RESPONSE (JSON)
```

## Layer Responsibilities

### 1. **ViewSet** (Presentation Layer)

- **Location**: `core/api/views/`
- **Responsibility**: HTTP request/response handling
- **What it does**:
  - Routes requests to appropriate actions (create, list, retrieve, update, destroy)
  - Handles HTTP status codes and headers
  - Error handling and formatting error responses
  - Delegates business logic to Service layer
- **Example**: `AccountViewSet` provides REST endpoints for `/accounts`

### 2. **Serializer** (Data Conversion & Validation Layer)

- **Location**: `core/api/serializers/`
- **Responsibility**: Data format conversion and validation
- **What it does**:
  - **Incoming**: Converts JSON → Python dictionary
  - **Outgoing**: Converts Python objects → JSON
  - Validates data against field rules (required, type, format)
  - Custom field validators for complex logic
  - Maps API representation to model representation
- **Example**: `AccountSerializer` handles Account model JSON serialization

### 3. **Service** (Business Logic Layer)

- **Location**: `core/services/domain/`
- **Responsibility**: Core domain business logic
- **What it does**:
  - Enforces business rules and constraints
  - Coordinates operations across multiple models
  - Handles transactions and data consistency
  - Audit field management (created_by, updated_by)
  - Complex data transformations
- **Example**: `AccountService.create_account()` sets owner and audit fields

### 4. **Manager** (Custom Query Layer)

- **Location**: `core/managers/`
- **Responsibility**: Complex data retrieval patterns
- **What it does**:
  - Defines custom querysets for common filtering/searching
  - Optimizes database queries (select_related, prefetch_related)
  - Encapsulates complex WHERE clauses
  - Alternative to raw SQL queries
- **Example**: `AccountManager` could provide methods like `get_active_accounts()`

### 5. **Model** (ORM & Schema Layer)

- **Location**: `core/models/`
- **Responsibility**: Database schema and ORM mapping
- **What it does**:
  - Defines fields and field types
  - Enforces field constraints (unique, null, blank)
  - Defines relationships (ForeignKey, ManyToMany)
  - Model-level validation (Meta options, indexing)
  - Custom managers attachment
- **Example**: `Account` model with all field definitions

### 6. **Database**

- **Responsibility**: Persistent data storage
- **What it does**:
  - Stores actual data
  - Enforces schema constraints
  - Handles transactions and locks
  - Provides query execution

## Additional Django Patterns

### Signals (Event System)

- **Location**: `core/signals.py`
- **Responsibility**: Decouple event handling from business logic
- **What it does**:
  - Listens for model events (post_save, post_delete, etc.)
  - Triggers actions when events occur
  - Enables domain-driven design
  - Prepares for event streaming (Kafka, etc.)
- **Example**: Account creation signal sends welcome email notification
- **Use For**: Audit logging, notifications, cascade operations, event tracking

### Middleware (Request Processing Pipeline)

- **Location**: `core/middleware.py`
- **Responsibility**: Process requests/responses globally
- **What it does**:
  - Intercepts every HTTP request and response
  - Performs pre/post processing
  - Handles cross-cutting concerns
  - Logs audit trails
- **Example**: `AuditMiddleware` logs user, timestamp, endpoint, changes
- **Use For**: Logging, authentication checks, CORS, rate limiting, request validation

### Managers & QuerySets (Data Access Abstraction)

- **Location**: `core/managers/`
- **Responsibility**: Abstract and encapsulate data access logic
- **What it does**:
  - Defines custom QuerySet methods for filtering and chaining
  - Provides named query methods (e.g., `active()`, `by_owner()`)
  - Encapsulates complex queries away from views/services
  - Improves testability and reusability
  - Enables query optimization (select_related, prefetch_related)
- **Components**:
  - **QuerySet**: Chainable query methods (`active()`, `filter_by_params()`)
  - **Manager**: Attaches QuerySet to Model (`objects = AccountManager()`)
- **Example**: `AccountManager` with `AccountQuerySet` provides `Account.objects.active().by_owner(user)`
- **Use For**: Complex queries, filtering patterns, query optimization, ORM abstraction

## Data Flow Example: Creating an Account

### Request Phase

```text
1. Client sends: POST /api/accounts
   {
     "name": "Acme Corp",
     "status": "prospect",
     "website": "https://acme.com"
   }

2. URL Router matches /accounts → AccountViewSet.create()

3. ViewSet calls perform_create(serializer)

4. Serializer.validated_data converts JSON to dict:
   {
     'name': 'Acme Corp',
     'status': 'prospect',
     'website': 'https://acme.com'
   }
   (validates website format, status choice, etc.)

5. Service.create_account(validated_data, user) executes:
   - Sets owner_user = current user
   - Sets created_by = current user
   - Calls Account.objects.create()

6. Manager returns queryset (if custom create logic exists)

7. Model creates instance with ORM:
   - Validates field types
   - Enforces constraints
   - Assigns auto fields (id, created_at)

8. Database INSERT: writes to accounts table
```

### Response Phase

```text
1. Model instance returned from create

2. Service may enrich/transform data

3. Serializer.to_representation(instance) converts to:
   {
     "id": "uuid-123",
     "name": "Acme Corp",
     "status": "prospect",
     "website": "https://acme.com",
     "created_at": "2025-01-07T10:30:00Z",
     "created_by": "uuid-user-1",
     ...
   }

4. ViewSet wraps in Response with HTTP 201 status

5. Client receives JSON response with location header
```

## Key Principles

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Unidirectional Flow**: Data flows through layers in one direction
3. **Service-Driven**: Business logic lives in services, not views or models
4. **Validation at Serializer**: Data validation happens early in the request pipeline
5. **Database Agnostic**: Services/ViewSets don't need to know SQL
6. **Testability**: Each layer can be tested independently

## When to Use Each Layer

| Layer | Use For |
| --- | --- |
| **ViewSet** | HTTP method routing, pagination, error formatting |
| **Serializer** | Data validation, format conversion, field mapping |
| **Service** | Business rules, transactions, audit trails, calculations |
| **Manager** | Complex queries, optimization, filtering patterns |
| **Model** | Field definitions, constraints, relationships, meta options |

## Best Practices

✅ **DO:**

- Keep ViewSets thin (delegate to Service)
- Leverage serializer validators for input validation
- Put business logic in Services
- Use Models for schema and basic constraints
- Write tests for Service layer (where logic lives)

❌ **DON'T:**

- Put business logic in ViewSets
- Perform complex queries in ViewSets
- Override Model.save() for business logic
- Write raw SQL in queries
- Skip validation at serializer level
