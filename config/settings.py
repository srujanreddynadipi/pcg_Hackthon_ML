"""
Configuration settings for ITSM AI API
"""

# HuggingFace Model Repository
HUGGINGFACE_REPO = "viveksai12/itsm-ticket-classifier"

# Model Files
MODEL_FILES = [
    "resolver_router.pkl",
    "tfidf_vectorizer.pkl",
    "category_encoder.pkl",
    "impact_encoder.pkl",
    "urgency_encoder.pkl"
]

# Category to Resolver Mapping (11 categories → 7 resolver groups)
CATEGORY_RESOLVER_MAP = {
    "Network": "Network Team",
    "Hardware": "Service Desk",
    "Software": "App Support",
    "Access": "Service Desk",
    "Database": "DBA Team",
    "Security": "Security Ops",
    "Cloud": "Cloud Ops",
    "DevOps": "DevOps Team",
    "Email": "Service Desk",
    "Monitoring": "Cloud Ops",
    "Service Request": "Service Desk"
}

# Priority Rules (Impact × Urgency matrix)
PRIORITY_MATRIX = {
    ("High", "High"): "Critical",
    ("High", "Medium"): "High",
    ("High", "Low"): "Medium",
    ("Medium", "High"): "High",
    ("Medium", "Medium"): "Medium",
    ("Medium", "Low"): "Low",
    ("Low", "High"): "Medium",
    ("Low", "Medium"): "Low",
    ("Low", "Low"): "Low"
}

# Duplicate Detection Settings
DUPLICATE_SIMILARITY_THRESHOLD = 0.70  # 70% similarity threshold
DUPLICATE_MAX_RESULTS = 5  # Return max 5 similar tickets

# Knowledge Base Settings
KB_TOP_K = 3  # Return top 3 knowledge base articles
KB_MIN_SIMILARITY = 0.65  # Minimum similarity for KB matching

# SentenceTransformer Model for Embeddings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# API Settings
API_TITLE = "ITSM AI-Driven Intelligent Ticketing API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
🎯 **AI-Powered ITSM Ticketing System** - Hackathon Track 4

**Features:**
- 🤖 **Autonomous Classification**: 11 categories with 100% accuracy
- ⚡ **Smart Prioritization**: Impact × Urgency matrix
- 🎯 **Intelligent Routing**: 7 resolver groups with proper mapping
- 🔍 **Duplicate Detection**: Find similar tickets using Sentence-BERT
- 📚 **Knowledge Base Search**: Auto-suggest solutions from past tickets
- ✍️ **Auto-Draft Responses**: Generate resolution templates
- 📊 **Proactive Insights**: Pattern detection and trend forecasting
- 🔍 **Detailed Audit Trail**: Feature importance + reasoning

**Models:**
- Random Forest (100% accuracy, 100K training samples)
- TF-IDF Vectorizer (2,208 features)
- Sentence-BERT (duplicate detection)
- HuggingFace Deployed: `viveksai12/itsm-ticket-classifier`
"""

# Keywords for Enhanced Classification
CATEGORY_KEYWORDS = {
    "Network": ["network", "vpn", "wifi", "connection", "internet", "router", "firewall", "dns", "ip", "connectivity"],
    "Hardware": ["laptop", "desktop", "monitor", "keyboard", "mouse", "printer", "hardware", "device", "screen"],
    "Software": ["application", "software", "program", "app", "install", "update", "license", "bug", "crash"],
    "Access": ["access", "permission", "login", "password", "account", "unlock", "rights", "credential"],
    "Database": ["database", "sql", "query", "db", "oracle", "mysql", "data", "table", "connection"],
    "Security": ["security", "vulnerability", "patch", "malware", "virus", "antivirus", "threat", "breach"],
    "Cloud": ["cloud", "aws", "azure", "s3", "ec2", "storage", "vm", "instance"],
    "DevOps": ["jenkins", "pipeline", "deployment", "ci/cd", "docker", "kubernetes", "build", "release"],
    "Email": ["email", "outlook", "exchange", "mailbox", "smtp", "inbox", "attachment"],
    "Monitoring": ["monitoring", "alert", "dashboard", "metrics", "grafana", "prometheus", "nagios"],
    "Service Request": ["request", "new user", "provisioning", "onboarding", "setup", "create"]
}

# Response Templates for Auto-Draft
RESPONSE_TEMPLATES = {
    "Network": """**Resolution Steps:**
1. Verify network connectivity and firewall rules
2. Check VPN configuration and certificates
3. Test DNS resolution and IP connectivity
4. Review network logs for connection errors
5. Escalate to Network Team if infrastructure issue

**Expected Resolution Time:** 2-4 hours
**Priority:** Based on business impact and number of affected users""",
    
    "Hardware": """**Resolution Steps:**
1. Verify hardware status and diagnostics
2. Check device drivers and firmware updates
3. Test hardware components (RAM, disk, peripherals)
4. Remote troubleshooting or arrange on-site support
5. Replace hardware if faulty

**Expected Resolution Time:** 4-8 hours (depending on parts availability)
**Priority:** Based on user role and device criticality""",
    
    "Software": """**Resolution Steps:**
1. Verify application version and licensing
2. Check for known bugs and available patches
3. Review application logs and error messages
4. Apply software updates or reinstall if needed
5. Escalate to App Support for complex issues

**Expected Resolution Time:** 2-6 hours
**Priority:** Based on application criticality and user impact""",
    
    "Access": """**Resolution Steps:**
1. Verify user identity and authorization
2. Check Active Directory/IAM permissions
3. Reset password or unlock account
4. Grant required access rights
5. Document changes and notify user

**Expected Resolution Time:** 1-2 hours
**Priority:** High if blocking critical business functions""",
    
    "Database": """**Resolution Steps:**
1. Verify database connectivity and credentials
2. Check database logs for errors or locks
3. Analyze query performance and optimization
4. Review backup/restore status if needed
5. Escalate to DBA Team for schema changes

**Expected Resolution Time:** 2-6 hours
**Priority:** Critical if affecting production databases""",
    
    "Security": """**Resolution Steps:**
1. Assess security threat level and scope
2. Isolate affected systems if needed
3. Apply security patches immediately
4. Run antivirus/malware scans
5. Document incident and notify Security Ops

**Expected Resolution Time:** Immediate (0-2 hours)
**Priority:** Always High or Critical - security incidents are top priority""",
    
    "Cloud": """**Resolution Steps:**
1. Check cloud service status and health
2. Verify resource quotas and scaling
3. Review cloud logs (CloudWatch, Azure Monitor)
4. Adjust cloud configurations or permissions
5. Escalate to Cloud Ops for infrastructure issues

**Expected Resolution Time:** 2-4 hours
**Priority:** Based on service criticality and SLA""",
    
    "DevOps": """**Resolution Steps:**
1. Check CI/CD pipeline status and logs
2. Verify build configurations and dependencies
3. Review deployment history and rollback if needed
4. Test pipeline stages individually
5. Escalate to DevOps Team for complex issues

**Expected Resolution Time:** 2-6 hours
**Priority:** High if blocking releases or deployments""",
    
    "Email": """**Resolution Steps:**
1. Verify email server connectivity
2. Check mailbox size and quotas
3. Review email client configuration
4. Test SMTP/IMAP/POP3 settings
5. Escalate to Service Desk for server issues

**Expected Resolution Time:** 1-3 hours
**Priority:** Medium unless blocking critical communications""",
    
    "Monitoring": """**Resolution Steps:**
1. Verify monitoring agent status
2. Check alert thresholds and configurations
3. Review metric collection and dashboards
4. Test alerting channels (email, Slack, PagerDuty)
5. Escalate to Cloud Ops for infrastructure monitoring

**Expected Resolution Time:** 2-4 hours
**Priority:** Medium-High (prevents detection of other issues)""",
    
    "Service Request": """**Resolution Steps:**
1. Verify request details and authorization
2. Check resource availability
3. Provision requested service/access
4. Document changes and notify requester
5. Close ticket after user confirmation

**Expected Resolution Time:** 4-24 hours (depends on approval process)
**Priority:** Low-Medium unless urgent business need"""
}
