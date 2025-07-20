# DataLens MVP - Database Structure

## 📊 Overview

**DataLens MVP** is a comprehensive inventory management and business intelligence platform built with Django. The database is designed to handle inventory tracking, demand forecasting, financial analysis, supplier management, and AI-powered insights.

### Database Stats
- **Engine**: SQLite3 (`db.sqlite3`)
- **Total Tables**: 117
- **Django Models**: 99
- **Total Relationships**: 157
- **Current Records**: 108
- **Database Size**: 4.90 MB

---

## 🏗️ Database Architecture

The database is organized into **7 main applications**, each handling specific business domains:

### 1. 🔐 Authentication (`authentication`)
**Core user and company management**

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `Company` | Multi-tenant company data | `name`, `ruc`, `industry`, `subscription_type` |
| `User` | User accounts with role-based access | `company`, `role`, `position`, `department` |

**Records**: 2 (1 company, 1 user)

---

### 2. 📦 Inventory (`inventory`)
**Complete inventory and supply chain management**

#### Core Inventory
| Model | Purpose | Records |
|-------|---------|---------|
| `Product` | Product catalog | 21 |
| `Category` | Product categorization | 1 |
| `Supplier` | Supplier management | 4 |
| `Customer` | Customer database | 1 |
| `Location` | Storage locations | 0 |
| `InventoryItem` | Stock tracking by location/batch | 0 |

#### Transactions & Operations
| Model | Purpose | Records |
|-------|---------|---------|
| `Transaction` | Inventory movements | 0 |
| `Sale` | Sales records | 0 |
| `PurchaseOrder` | Purchase order management | 21 |
| `PurchaseOrderTracking` | PO status tracking | 0 |

#### Email & Communication
| Model | Purpose | Records |
|-------|---------|---------|
| `EmailCampaign` | Email marketing campaigns | 4 |
| `TrackedEmail` | Email tracking analytics | 51 |
| `EmailClick` | Click tracking | 0 |
| `EmailPattern` | Email behavior patterns | 0 |
| `EmailInsight` | AI-generated email insights | 0 |

**Total Records**: 103

---

### 3. 🤖 Forecasting (`forecasting`)
**Advanced ML/AI forecasting and optimization**

#### Machine Learning Models
| Model Category | Models |
|---------------|---------|
| **Core ML** | `ForecastModel`, `MLModelVersion`, `MLExperiment`, `MLModelRegistry` |
| **Demand Forecasting** | `DemandForecast`, `ForecastAccuracy`, `ReorderRecommendation` |
| **Financial Forecasting** | `RevenueForecasting`, `CashFlowForecast`, `ProfitabilityAnalysis` |
| **Customer Analytics** | `CustomerLifetimeValue`, `ChurnPrediction`, `CustomerSegmentation` |
| **Supply Chain** | `SupplierPerformanceModel`, `ProcurementOptimization`, `InventoryOptimization` |
| **AI Integration** | `AIPromptVersion`, `AIAPIUsage`, `AIInsight`, `HybridMLAIPrediction` |

#### Key Features
- **50+ ML/AI models** for comprehensive business intelligence
- **Hybrid ML-AI predictions** combining traditional ML with LLM insights
- **Customer behavior analysis** (CLV, churn, segmentation)
- **Financial forecasting** (revenue, cash flow, profitability)
- **Supply chain optimization** (supplier ROI, procurement)
- **Price optimization** and elasticity analysis

**Current Records**: 0 (models ready for training)

---

### 4. 🚨 Alerts (`alerts`)
**Intelligent alerting system**

| Model | Purpose |
|-------|---------|
| `AlertRule` | Configurable alert conditions |
| `Alert` | Generated alerts |
| `AlertRecipient` | Alert distribution lists |
| `NotificationLog` | Alert delivery tracking |

**Features**: Multi-channel notifications (email, WhatsApp), auto-purchase order generation

---

### 5. 📊 Reports (`reports`)
**Business intelligence and KPI tracking**

| Model | Purpose |
|-------|---------|
| `ReportTemplate` | Reusable report configurations |
| `Report` | Generated reports |
| `KPIDefinition` | Custom KPI definitions |
| `KPIValue` | Historical KPI data |
| `ReportSchedule` | Automated report generation |

---

### 6. 📥 Data Import (`data_import`)
**Data integration and ETL**

| Model | Purpose |
|-------|---------|
| `DataImportSession` | Import job tracking |
| `ColumnMapping` | Field mapping configurations |
| `ImportTemplate` | Reusable import templates |
| `FieldDefinition` | Import field definitions |

---

### 7. 🧠 Intelligence (`intelligence`)
**AI-powered business insights**

| Model | Purpose | Records |
|-------|---------|---------|
| `IntelligenceBriefing` | Daily business briefings | 3 |
| `IntelligenceInsight` | AI-generated insights | 0 |
| `IntelligenceMetric` | Intelligence metrics | 0 |

---

## 🔗 Key Relationships

### Core Entity Relationships
```
Company (1) → (N) User
Company (1) → (N) Product
Product (N) → (1) Category
Product (N) → (1) Supplier
Product (1) → (N) InventoryItem
Location (1) → (N) InventoryItem
```

### Forecasting Relationships
```
Company (1) → (N) ForecastModel
ForecastModel (1) → (N) DemandForecast
Product (1) → (N) DemandForecast
Customer (1) → (1) CustomerLifetimeValue
Customer (1) → (1) ChurnPrediction
```

### Alert System
```
Company (1) → (N) AlertRule
AlertRule (1) → (N) Alert
Product (1) → (N) Alert
Alert (1) → (N) NotificationLog
```

---

## 📈 Data Distribution

### Current Data Status
| Application | Records | Percentage |
|------------|---------|------------|
| **Inventory** | 103 | 95.4% |
| **Intelligence** | 3 | 2.8% |
| **Authentication** | 2 | 1.8% |
| **Other Apps** | 0 | 0% |

### Top Tables by Records
1. **TrackedEmail**: 51 records (47.2%)
2. **Product**: 21 records (19.4%)
3. **PurchaseOrder**: 21 records (19.4%)
4. **Supplier**: 4 records (3.7%)
5. **EmailCampaign**: 4 records (3.7%)

---

## 🔧 Technical Details

### Database Engine
- **Type**: SQLite3
- **File**: `db.sqlite3`
- **Size**: 4.90 MB
- **Avg Record Size**: 8.5 KB

### Performance Optimization
- **289 indexes** for query optimization
- **157 foreign key relationships** for data integrity
- **Unique constraints** on critical business fields
- **Composite indexes** on frequently queried combinations

### Data Integrity
- ✅ No integrity violations detected
- ✅ All foreign key constraints valid
- ✅ Unique constraints properly enforced

---

## 🚀 Getting Started

### Database Setup
```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (if available)
python manage.py loaddata fixtures/sample_data.json
```

### Key Configuration
- **Multi-tenancy**: All models are company-scoped
- **Audit trails**: Created/updated timestamps on all models
- **Soft deletes**: `is_active` flags for logical deletion
- **JSON fields**: Flexible metadata storage

---

## 📝 Model Conventions

### Naming Patterns
- **Primary Keys**: `BigAutoField` (64-bit integers)
- **Foreign Keys**: `company`, `created_by`, `updated_by`
- **Timestamps**: `created_at`, `updated_at`
- **Flags**: `is_active`, `is_deleted`

### Common Fields
```python
# Standard audit fields
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
is_active = models.BooleanField(default=True)

# Multi-tenancy
company = models.ForeignKey(Company, on_delete=models.CASCADE)

# User tracking
created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

---

## 🔮 Future Enhancements

### Planned Features
- **Real-time analytics** with streaming data
- **Advanced ML pipelines** for automated retraining
- **Multi-warehouse support** with complex location hierarchies
- **Integration APIs** for external systems
- **Mobile app support** with offline capabilities

### Scalability Considerations
- **Database migration** to PostgreSQL for production
- **Data partitioning** for historical data
- **Caching layer** with Redis
- **Search engine** integration (Elasticsearch)

---

## 📚 Documentation

### Related Documentation
- [API Documentation](./docs/api.md)
- [Model Reference](./docs/models.md)
- [Business Logic](./docs/business_logic.md)
- [Deployment Guide](./docs/deployment.md)

### Support
For questions about the database structure or data models, please refer to the technical documentation or contact the development team.

---

*Last Updated: July 19, 2025*
*Database Version: v1.0.0*
*Analysis Generated: 2025-07-19 15:45:48*