# 02 - Architecture

## 🏗️ System Architecture

NextDNS Optimized Analytics follows a microservices architecture pattern, where each component is a specialized "LEGO brick" that connects seamlessly with others while maintaining clear responsibilities.

## 🔧 High-Level Architecture

```mermaid
graph TB
    NextDNS[NextDNS API<br/>🌐 DNS Logs] --> Backend[Backend API<br/>🐍 FastAPI]
    Backend --> Database[(PostgreSQL<br/>🗄️ Data Storage)]
    Frontend[Frontend<br/>⚛️ React + Nginx] --> Backend
    
    subgraph "Docker Network"
        Backend
        Database
        Frontend
    end
    
    subgraph "External Services"
        NextDNS
        User[👤 User Browser]
    end
    
    User --> Frontend
    
    style NextDNS fill:#e1f5fe
    style Backend fill:#f3e5f5
    style Database fill:#e8f5e8
    style Frontend fill:#fff3e0
```

## 🐳 Container Architecture

```mermaid
graph LR
    subgraph "Docker Compose Stack"
        subgraph "Application Tier"
            Frontend[nextdns-frontend<br/>📱 React + Nginx<br/>Host Port: 5002]
            Backend[nextdns-backend<br/>🔌 FastAPI<br/>Host Port: 5001]
        end
        
        subgraph "Data Tier"
            Database[(nextdns-db<br/>🗃️ PostgreSQL<br/>Host Port: 5003)]
        end
        
        subgraph "Networking"
            Network[nextdns-network<br/>🔗 Bridge Network]
        end
    end
    
    Frontend -.->|Nginx Proxy /api/*| Backend
    Backend -->|SQL| Database
    Frontend --- Network
    Backend --- Network
    Database --- Network
    
    style Frontend fill:#e3f2fd
    style Backend fill:#f1f8e9
    style Database fill:#fce4ec
    style Network fill:#fff8e1
```

## 📊 Data Flow Architecture

```mermaid
sequenceDiagram
    participant N as NextDNS API
    participant B as Backend (FastAPI)
    participant D as Database (PostgreSQL)
    participant F as Frontend (React)
    participant U as User

    Note over N,D: Data Collection Flow
    B->>N: Fetch DNS logs (every N minutes)
    N-->>B: Return JSON logs
    B->>D: Store/Update logs
    D-->>B: Confirm storage
    
    Note over F,U: User Interaction Flow
    U->>F: Request analytics dashboard
    F->>B: API call with filters
    B->>D: Query filtered data
    D-->>B: Return results
    B-->>F: JSON response
    F-->>U: Rendered dashboard
    
    Note over B: Health Monitoring
    loop Health Check
        B->>D: Check connectivity
        D-->>B: Status response
    end
```

## 🧩 Component Details

### **Backend API (FastAPI)**

```mermaid
graph TB
    subgraph "Backend FastAPI Application"
        API[FastAPI App<br/>🚀 Main Application]
        Auth[API Key Authentication<br/>🔐 LOCAL_API_KEY]
        Scheduler[Background Scheduler<br/>⏰ APScheduler]
        Health[Health Endpoints<br/>🏥 /health /health/detailed]
        Endpoints[REST API Endpoints<br/>🔌 /stats /logs etc]
    end
    
    subgraph "External Integrations"
        NextDNS[NextDNS API<br/>📡 Log Source]
        DB[(PostgreSQL<br/>💾 Data Store)]
    end
    
    API --> Auth
    API --> Health
    API --> Endpoints
    API --> Scheduler
    Scheduler --> NextDNS
    Endpoints --> DB
    Scheduler --> DB
    Health --> DB
    
    style API fill:#e8f5e8
    style Auth fill:#fff3e0
    style Scheduler fill:#e1f5fe
    style Health fill:#fce4ec
```

**Key Responsibilities:**
- 🔌 **REST API Endpoints** - Serve DNS log data with filtering
- 🔄 **Data Fetching** - Automated NextDNS API integration
- 🔐 **Authentication** - Secure API key-based access control
- 🏥 **Health Monitoring** - System health and resource metrics
- 📊 **Data Processing** - Log parsing and analytics computation

### **Frontend Dashboard (React/TypeScript)**

```mermaid
graph TB
    subgraph "Frontend Architecture"
        Router[React Router<br/>🧭 Navigation]
        Dashboard[Dashboard Views<br/>📊 Analytics UI]
        API[API Client<br/>🔌 HTTP Client]
        State[State Management<br/>🗄️ React Hooks]
    end
    
    subgraph "UI Components"
        Charts[Chart Components<br/>📈 Data Visualization]
        Filters[Filter Controls<br/>🔍 User Input]
        Tables[Data Tables<br/>📋 Log Display]
    end
    
    Router --> Dashboard
    Dashboard --> Charts
    Dashboard --> Filters
    Dashboard --> Tables
    Dashboard --> API
    API --> State
    State --> Dashboard
    
    style Router fill:#e3f2fd
    style Dashboard fill:#f1f8e9
    style API fill:#fff3e0
    style State fill:#fce4ec
```

**Key Responsibilities:**
- 📱 **Responsive UI** - Modern React-based interface
- 📊 **Data Visualization** - Charts and analytics displays
- 🔍 **Advanced Filtering** - Domain exclusion and time-range filtering
- 🔌 **API Integration** - Seamless backend communication
- 🎨 **User Experience** - Intuitive navigation and controls

### **Database Layer (PostgreSQL)**

```mermaid
erDiagram
    DNS_LOGS {
        bigint id PK
        timestamp timestamptz
        string domain
        string action
        string device
        string client_ip
        string query_type
        boolean blocked
        string profile_id
        jsonb data
        timestamptz created_at
    }
```

**Key Responsibilities:**
- 💾 **Data Persistence** - Long-term DNS log storage with JSON metadata
- 🔍 **Query Performance** - Optimized indexes on domain, timestamp, profile_id
- 🔄 **Data Integrity** - ACID compliance and duplicate prevention
- 📊 **Analytics Support** - Efficient aggregation queries for dashboard metrics
- 🗂️ **Schema Management** - Alembic-based migrations for version control

**Note:** System metrics (CPU, memory, disk) are collected in real-time via the `/health/detailed` endpoint using `psutil` - they are not persisted to the database.

## 🌐 Network Architecture

```mermaid
graph TB
    subgraph "External Network"
        Internet[🌐 Internet]
        NextDNS[NextDNS API<br/>api.nextdns.io]
    end
    
    subgraph "Host System"
        Ports[Host Ports<br/>5001, 5002, 5003]
    end
    
    subgraph "Docker Network: nextdns-network"
        subgraph "Frontend Container"
            Nginx[Nginx + React<br/>:80]
        end
        
        subgraph "Backend Container"
            FastAPI[FastAPI + Uvicorn<br/>:5000]
        end
        
        subgraph "Database Container"
            PostgreSQL[PostgreSQL<br/>:5432]
        end
    end
    
    Internet --> Ports
    Ports --> Nginx
    Nginx -.->|/api/* proxy| FastAPI
    FastAPI --> PostgreSQL
    FastAPI --> NextDNS
    
    style Internet fill:#e1f5fe
    style Ports fill:#fff3e0
    style Nginx fill:#e8f5e8
    style FastAPI fill:#f3e5f5
    style PostgreSQL fill:#fce4ec
```

## 📦 Deployment Patterns

### **Docker Compose Deployment**

```mermaid
graph TB
    subgraph "Development Environment"
        DC1[docker-compose.yml<br/>🔧 Local Development]
    end
    
    subgraph "Production Environment"
        DC2[docker-compose.prod.yml<br/>🚀 Production Ready]
    end
    
    subgraph "Portainer Deployment"
        Portal[Portainer Stack<br/>🐳 Web Interface]
        Template[portainer-stack.yml.template<br/>📝 Configuration Template]
    end
    
    subgraph "Manual Deployment"
        Manual[Individual Containers<br/>⚙️ Custom Setup]
    end
    
    DC1 -.-> DC2
    Template --> Portal
    Portal -.-> DC2
    Manual -.-> DC2
    
    style DC1 fill:#e8f5e8
    style DC2 fill:#f3e5f5
    style Portal fill:#e1f5fe
    style Template fill:#fff3e0
```

## 🔄 Data Processing Pipeline

```mermaid
flowchart TD
    Start([Scheduled Task<br/>Every N Minutes]) --> Fetch[Fetch from NextDNS API<br/>📡 HTTP Request]
    Fetch --> Parse[Parse JSON Response<br/>🔍 Data Validation]
    Parse --> Filter[Apply Filters<br/>🧹 Deduplication]
    Filter --> Transform[Transform Data<br/>🔄 Format Conversion]
    Transform --> Store[Store in Database<br/>💾 PostgreSQL Insert]
    Store --> Log[Update Metrics<br/>📊 Performance Tracking]
    Log --> End([Complete<br/>✅ Success])
    
    Fetch -->|Error| Retry[Retry Logic<br/>🔄 Exponential Backoff]
    Retry --> Fetch
    Retry -->|Max Retries| Error[Log Error<br/>❌ Alert System]
    
    style Start fill:#e8f5e8
    style Fetch fill:#e1f5fe
    style Parse fill:#fff3e0
    style Store fill:#f3e5f5
    style End fill:#e8f5e8
    style Error fill:#ffebee
```

## 🏥 Health Monitoring Architecture

```mermaid
graph TB
    subgraph "Health Check System"
        HealthAPI[Health Endpoints<br/>🏥 /health, /health/detailed]
        Metrics[System Metrics<br/>📊 CPU, Memory, Disk]
        DBHealth[Database Health<br/>🗄️ Connection Status]
        APIHealth[API Health<br/>🔌 Service Status]
    end
    
    subgraph "Monitoring Integrations"
        Docker[Docker Health<br/>🐳 Container Status]
        Portainer[Portainer UI<br/>🖥️ Visual Monitoring]
        External[External Monitoring<br/>📡 Uptime Services]
    end
    
    HealthAPI --> Metrics
    HealthAPI --> DBHealth
    HealthAPI --> APIHealth
    Docker --> HealthAPI
    Portainer --> Docker
    External --> HealthAPI
    
    style HealthAPI fill:#e8f5e8
    style Metrics fill:#e1f5fe
    style Docker fill:#f3e5f5
    style Portainer fill:#fff3e0
```

## 🔐 Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        Auth[API Authentication<br/>🔐 Bearer Token]
        CORS[CORS Protection<br/>🛡️ Origin Control]
        Headers[Security Headers<br/>📋 HTTP Protection]
        Env[Environment Config<br/>🔒 Secret Management]
    end
    
    subgraph "Network Security"
        Network[Docker Network<br/>🔗 Isolated Communication]
        Ports[Port Management<br/>🚆 Only Required Ports]
        Container[Container Isolation<br/>🐳 Process Separation]
    end
    
    subgraph "Data Security"
        Local[Local Storage<br/>🏠 No External Data]
        Encryption[Data Protection<br/>🔐 HTTPS/TLS]
        Backup[Backup Strategy<br/>💾 Volume Persistence]
    end
    
    Auth --> Network
    CORS --> Container
    Headers --> Container
    Env --> Local
    Network --> Encryption
    
    style Auth fill:#ffebee
    style Network fill:#e8f5e8
    style Local fill:#e1f5fe
```

## 🚀 Scalability Considerations

The current architecture is designed for single-instance deployment with the following scaling options:

- **Vertical Scaling**: Increase CPU/memory resources for containers
- **Database Optimization**: Tune PostgreSQL performance and add indexes  
- **Caching**: Add Redis for frequently accessed data
- **CDN**: Serve static frontend assets via CDN for global distribution

## 📏 Performance Characteristics

| Component | Response Time | Throughput | Resource Usage |
|-----------|---------------|------------|----------------|
| **Backend API** | < 100ms | 1000+ req/min | Low CPU, Moderate Memory |
| **Database** | < 50ms (queries) | 10K+ ops/min | Moderate CPU, High I/O |
| **Frontend** | < 2s (load) | Static serving | Minimal resources |
| **Data Fetching** | 1-5s (NextDNS) | Configurable interval | Low background load |

---

**Next:** [API Reference](./03-api-reference.md) → Detailed endpoint documentation