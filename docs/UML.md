# UML Diagrams & System Models
## Smart Canteen Ordering System (ABL 1)

This document contains standard UML diagrams modeled in **Mermaid** and **PlantUML** format for viva presentations, architectural reviews, and project documentation.

---

## 1. Use Case Diagram

```mermaid
flowchart LR
    Student((Student))
    Staff((Canteen Staff))
    Admin((System Admin))

    subgraph SmartCanteen ["Smart Canteen Ordering System"]
        UC1[Register & Login]
        UC2[Browse Menu & Search]
        UC3[Manage Cart]
        UC4[Select Pickup Slot]
        UC5[Make Payment Wallet/UPI/Cash]
        UC6[Track Live Order Status]
        UC7[Cancel Order]
        UC8[Reorder Past Items]
        UC9[Manage Kitchen Queue]
        UC10[Update Order Status]
        UC11[Update Stock & Toggle Availability]
        UC12[View Sales Analytics & Export CSV]
    end

    Student --> UC1
    Student --> UC2
    Student --> UC3
    Student --> UC4
    Student --> UC5
    Student --> UC6
    Student --> UC7
    Student --> UC8

    Staff --> UC1
    Staff --> UC9
    Staff --> UC10
    Staff --> UC11

    Admin --> UC1
    Admin --> UC11
    Admin --> UC12
```

---

## 2. Class Diagram

```mermaid
classDiagram
    class User {
        +int id
        +string username
        +string email
        +string password_hash
        +string role
        +float wallet_balance
        +datetime created_at
        +set_password(password)
        +check_password(password) bool
        +to_dict() dict
    }

    class Category {
        +int id
        +string name
        +string description
        +to_dict() dict
    }

    class MenuItem {
        +int id
        +int category_id
        +string name
        +string description
        +float price
        +int stock
        +bool is_available
        +int prep_time_minutes
        +datetime created_at
        +is_in_stock bool
        +to_dict() dict
    }

    class Order {
        +int id
        +int user_id
        +string status
        +string pickup_slot
        +string payment_method
        +string payment_status
        +float total_amount
        +int estimated_wait_minutes
        +string idempotency_key
        +datetime created_at
        +datetime updated_at
        +to_dict() dict
    }

    class OrderItem {
        +int id
        +int order_id
        +int menu_item_id
        +int quantity
        +float unit_price
        +float subtotal
        +to_dict() dict
    }

    class PickupSlotConfig {
        +int id
        +string slot_time
        +int max_orders
        +bool is_active
        +to_dict() dict
    }

    class OrderService {
        +get_pickup_slots() list
        +calculate_estimated_wait_time(items) int
        +place_order(user_id, items, slot, method) Order
        +update_order_status(order_id, status) Order
        +cancel_order(order_id, user_id) Order
        +get_queue_position(order_id) int
    }

    User "1" -- "*" Order : places
    Category "1" -- "*" MenuItem : categorizes
    MenuItem "1" -- "*" OrderItem : appears_in
    Order "1" -- "*" OrderItem : contains
    OrderService ..> Order : manages
    OrderService ..> MenuItem : updates_stock
```

---

## 3. Sequence Diagram: Place Order Flow

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Browser as Client Browser (cart.js)
    participant Route as Student Route (/checkout)
    participant Svc as OrderService
    participant DB as SQLite / PostgreSQL Database

    Student->>Browser: Selects Pickup Slot & Clicks "Place Order"
    Browser->>Route: POST /checkout (cart_data, slot, payment, token)
    Route->>Svc: place_order(user_id, items, slot, payment, token)
    
    rect rgb(240, 248, 255)
        note over Svc,DB: Atomic Database Transaction
        Svc->>DB: Check idempotency_key (duplicate submit guard)
        Svc->>DB: Query slot booked count vs max capacity
        alt Slot Full
            Svc-->>Route: Raise InvalidSlotError
            Route-->>Browser: Flash "Slot fully booked"
        end
        
        loop For each item in cart
            Svc->>DB: SELECT FOR UPDATE menuItem WHERE id = item_id
            alt Stock < Requested Qty or is_available = False
                Svc->>DB: ROLLBACK Transaction
                Svc-->>Route: Raise OutOfStockError
                Route-->>Browser: Flash "Item out of stock"
            else Stock Sufficient
                Svc->>DB: Decrement item.stock (auto sold-out if stock=0)
            end
        end

        alt Payment == Wallet
            alt Balance < Total Amount
                Svc->>DB: ROLLBACK Transaction
                Svc-->>Route: Raise InsufficientFundsError
            else Balance Sufficient
                Svc->>DB: Deduct user.wallet_balance
            end
        end

        Svc->>DB: INSERT INTO orders & order_items
        Svc->>DB: COMMIT Transaction
    end

    Svc-->>Route: Return new Order instance
    Route-->>Browser: 302 Redirect to /orders/<order_id>
    Browser->>Student: Render Live Order Status View
```

---

## 4. Activity Diagram: Order Lifecycle & Kitchen State Machine

```mermaid
stateDiagram-v2
    [*] --> Placed: Student completes checkout
    
    Placed --> Accepted: Kitchen Staff accepts order
    Placed --> Cancelled: Student/Staff cancels (Stock Restored & Wallet Refunded)
    
    Accepted --> Preparing: Kitchen starts cooking
    Accepted --> Cancelled: Student/Staff cancels (Stock Restored & Wallet Refunded)
    
    Preparing --> Ready: Food preparation completed
    note right of Preparing: Cancellations are strictly forbidden once cooking begins
    
    Ready --> Collected: Student shows confirmation & receives food
    
    Collected --> [*]
    Cancelled --> [*]
```

---

## 5. Deployment Diagram (Kubernetes & Container Topology)

```mermaid
flowchart TD
    subgraph Users ["Client Tier"]
        Browser["User Browser (Student / Staff / Admin)"]
    end

    subgraph K8sCluster ["Kubernetes Cluster (Minikube / Cloud)"]
        Ingress["NGINX Ingress Controller (canteen.local)"]
        Service["NodePort Service :30080 (smart-canteen-service)"]
        
        subgraph Pod1 ["Pod 1 (Replica 1)"]
            Container1["smart-canteen:1.0 (Non-root user 10001)<br/>Gunicorn WSGI (2 Workers) + Flask"]
            Probe1["Probes: Liveness & Readiness (/health)"]
        end
        
        subgraph Pod2 ["Pod 2 (Replica 2)"]
            Container2["smart-canteen:1.0 (Non-root user 10001)<br/>Gunicorn WSGI (2 Workers) + Flask"]
            Probe2["Probes: Liveness & Readiness (/health)"]
        end

        ConfigMap["ConfigMap: smart-canteen-config"]
        Secret["Secret: smart-canteen-secret"]
        DataVol[("EmptyDir / PersistentVolume (/app/instance)")]
    end

    Browser -->|HTTP Port 80 / 30080| Ingress
    Ingress --> Service
    Service --> Pod1
    Service --> Pod2
    ConfigMap -.-> Container1
    ConfigMap -.-> Container2
    Secret -.-> Container1
    Secret -.-> Container2
    Container1 --- DataVol
    Container2 --- DataVol
```
