# ShortletsbyShar - System Architecture

## High-Level Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Browser]
        B[Mobile Browser]
    end
    
    subgraph "Frontend - React App"
        C[React Router]
        D[Redux Store]
        E[React Query]
        F[UI Components]
    end
    
    subgraph "Backend - Node.js/Express"
        G[API Gateway]
        H[Auth Middleware]
        I[Controllers]
        J[Services]
        K[Models]
    end
    
    subgraph "Database"
        L[(MongoDB Atlas)]
    end
    
    subgraph "External Services"
        M[Paystack API]
        N[Cloudinary CDN]
        O[Twilio WhatsApp]
        P[Email Service]
    end
    
    A --> C
    B --> C
    C --> D
    C --> E
    C --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    J --> M
    J --> N
    J --> O
    J --> P
```

## Detailed Component Flow

```mermaid
graph LR
    subgraph "User Journey"
        U1[Browse Apartments] --> U2[Select Apartment]
        U2 --> U3[Check Availability]
        U3 --> U4[Fill Booking Form]
        U4 --> U5[Make Payment]
        U5 --> U6[Receive Confirmation]
    end
    
    subgraph "System Processing"
        S1[Load Apartments] --> S2[Filter & Search]
        S2 --> S3[Calculate Pricing]
        S3 --> S4[Validate Booking]
        S4 --> S5[Process Payment]
        S5 --> S6[Send Notifications]
    end
    
    U1 -.-> S1
    U2 -.-> S2
    U3 -.-> S3
    U4 -.-> S4
    U5 -.-> S5
    U6 -.-> S6
```

## Database Relationships

```mermaid
erDiagram
    USERS ||--o{ BOOKINGS : makes
    USERS ||--o{ REVIEWS : writes
    APARTMENTS ||--o{ BOOKINGS : has
    APARTMENTS ||--o{ REVIEWS : receives
    BOOKINGS ||--|| REVIEWS : generates
    
    USERS {
        ObjectId _id
        string email
        string password
        string firstName
        string lastName
        string phone
        string role
        boolean verified
    }
    
    APARTMENTS {
        ObjectId _id
        string name
        string slug
        object location
        number bedrooms
        number bathrooms
        array images
        object pricing
        number rating
        boolean active
    }
    
    BOOKINGS {
        ObjectId _id
        string bookingReference
        ObjectId userId
        ObjectId apartmentId
        date checkIn
        date checkOut
        object pricing
        string status
        string paymentStatus
    }
    
    REVIEWS {
        ObjectId _id
        ObjectId userId
        ObjectId apartmentId
        ObjectId bookingId
        number rating
        string comment
        date createdAt
    }
```

## Booking Flow Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant DB as Database
    participant P as Paystack
    participant W as WhatsApp
    participant E as Email
    
    U->>F: Select apartment & dates
    F->>B: Check availability
    B->>DB: Query bookings
    DB-->>B: Return conflicts
    B-->>F: Availability status
    
    U->>F: Fill booking form
    F->>B: Submit booking
    B->>DB: Create pending booking
    DB-->>B: Booking created
    
    B->>P: Initialize payment
    P-->>B: Payment URL
    B-->>F: Redirect to payment
    
    U->>P: Complete payment
    P->>B: Webhook notification
    B->>DB: Update booking status
    
    B->>W: Send WhatsApp confirmation
    B->>E: Send email confirmation
    
    B-->>F: Booking confirmed
    F-->>U: Show confirmation page
```

## Admin Panel Architecture

```mermaid
graph TB
    subgraph "Admin Dashboard"
        AD[Dashboard Home]
        AD --> AM[Apartment Management]
        AD --> BM[Booking Management]
        AD --> UM[User Management]
        AD --> RM[Review Management]
        AD --> AN[Analytics]
    end
    
    subgraph "Apartment Management"
        AM --> AM1[List Apartments]
        AM --> AM2[Add New]
        AM --> AM3[Edit Existing]
        AM --> AM4[Upload Images]
        AM --> AM5[Set Availability]
    end
    
    subgraph "Booking Management"
        BM --> BM1[View All Bookings]
        BM --> BM2[Confirm Bookings]
        BM --> BM3[Check-in/Check-out]
        BM --> BM4[Calendar View]
        BM --> BM5[Handle Cancellations]
    end
```

## Payment Processing Flow

```mermaid
stateDiagram-v2
    [*] --> BookingCreated: User submits booking
    BookingCreated --> PaymentInitialized: Initialize Paystack
    PaymentInitialized --> PaymentPending: Redirect to Paystack
    PaymentPending --> PaymentSuccess: Payment completed
    PaymentPending --> PaymentFailed: Payment declined
    PaymentSuccess --> BookingConfirmed: Update booking
    BookingConfirmed --> NotificationsSent: Send emails/WhatsApp
    NotificationsSent --> [*]
    PaymentFailed --> BookingCancelled: Cancel booking
    BookingCancelled --> [*]
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant DB as Database
    
    U->>F: Enter credentials
    F->>B: POST /api/auth/login
    B->>DB: Find user by email
    DB-->>B: User data
    B->>B: Verify password
    B->>B: Generate JWT token
    B-->>F: Return token + user data
    F->>F: Store token in localStorage
    F-->>U: Redirect to dashboard
    
    Note over F,B: Subsequent requests
    F->>B: API request with token
    B->>B: Verify JWT token
    B->>DB: Fetch protected data
    DB-->>B: Return data
    B-->>F: Return response
```

## File Upload Process

```mermaid
graph LR
    A[User selects images] --> B[Frontend validation]
    B --> C[Upload to backend]
    C --> D[Multer processes file]
    D --> E[Upload to Cloudinary]
    E --> F[Get image URL]
    F --> G[Save URL to database]
    G --> H[Return success]
```

## Search & Filter Architecture

```mermaid
graph TB
    A[User Input] --> B{Filter Type}
    B -->|Location| C[City Filter]
    B -->|Bedrooms| D[Bedroom Count]
    B -->|Price| E[Price Range]
    B -->|Amenities| F[Feature Filter]
    B -->|Dates| G[Availability Check]
    
    C --> H[Build Query]
    D --> H
    E --> H
    F --> H
    G --> H
    
    H --> I[Execute MongoDB Query]
    I --> J[Sort Results]
    J --> K[Paginate]
    K --> L[Return to Frontend]
```

## Notification System

```mermaid
graph TB
    A[Trigger Event] --> B{Event Type}
    B -->|New Booking| C[Booking Notification]
    B -->|Payment Success| D[Confirmation Notification]
    B -->|Check-in Reminder| E[Reminder Notification]
    B -->|Review Request| F[Review Notification]
    
    C --> G[Email Service]
    C --> H[WhatsApp Service]
    C --> I[Admin Dashboard]
    
    D --> G
    D --> H
    
    E --> G
    E --> H
    
    F --> G
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        A[GitHub Repository]
        A --> B[Vercel - Frontend]
        A --> C[Railway - Backend]
        
        B --> D[CDN Distribution]
        C --> E[MongoDB Atlas]
        C --> F[Cloudinary]
        C --> G[Paystack]
        C --> H[Twilio]
        
        D --> I[Users Worldwide]
        
        J[Custom Domain] --> B
        K[SSL Certificate] --> B
    end
```

## Security Layers

```mermaid
graph TB
    A[User Request] --> B[HTTPS/SSL]
    B --> C[Rate Limiting]
    C --> D[CORS Policy]
    D --> E[JWT Verification]
    E --> F[Input Validation]
    F --> G[Authorization Check]
    G --> H[Database Query]
    H --> I[Response Sanitization]
    I --> J[Secure Response]
```

## Mobile Responsive Strategy

```mermaid
graph LR
    A[Design] --> B{Screen Size}
    B -->|Mobile < 640px| C[Mobile Layout]
    B -->|Tablet 641-1024px| D[Tablet Layout]
    B -->|Desktop > 1024px| E[Desktop Layout]
    
    C --> F[Stack Vertically]
    C --> G[Touch Optimized]
    C --> H[Bottom Navigation]
    
    D --> I[2-Column Grid]
    D --> J[Collapsible Sidebar]
    
    E --> K[3-Column Grid]
    E --> L[Fixed Sidebar]
```

## Caching Strategy

```mermaid
graph TB
    A[User Request] --> B{Cache Check}
    B -->|Hit| C[Return Cached Data]
    B -->|Miss| D[Fetch from Database]
    D --> E[Store in Cache]
    E --> F[Return Fresh Data]
    
    G[Cache Invalidation] --> H{Event Type}
    H -->|Apartment Updated| I[Clear Apartment Cache]
    H -->|Booking Created| J[Clear Availability Cache]
    H -->|Review Added| K[Clear Review Cache]
```

## Error Handling Flow

```mermaid
graph TB
    A[Error Occurs] --> B{Error Type}
    B -->|Validation Error| C[400 Bad Request]
    B -->|Auth Error| D[401 Unauthorized]
    B -->|Permission Error| E[403 Forbidden]
    B -->|Not Found| F[404 Not Found]
    B -->|Server Error| G[500 Internal Error]
    
    C --> H[Log Error]
    D --> H
    E --> H
    F --> H
    G --> H
    
    H --> I[Send to Error Tracking]
    H --> J[Return User-Friendly Message]
```

---

## Technology Stack Visualization

```mermaid
graph TB
    subgraph "Frontend Stack"
        A1[React 18]
        A2[TypeScript]
        A3[Tailwind CSS]
        A4[Redux Toolkit]
        A5[React Query]
        A6[React Router]
    end
    
    subgraph "Backend Stack"
        B1[Node.js]
        B2[Express.js]
        B3[MongoDB]
        B4[Mongoose]
        B5[JWT]
        B6[Bcrypt]
    end
    
    subgraph "DevOps"
        C1[Git/GitHub]
        C2[Vercel]
        C3[Railway]
        C4[MongoDB Atlas]
    end
    
    subgraph "External APIs"
        D1[Paystack]
        D2[Cloudinary]
        D3[Twilio]
        D4[SendGrid]
    end
```

---

These diagrams provide a comprehensive visual overview of the ShortletsbyShar booking platform architecture, showing how all components interact and work together to create a seamless booking experience.