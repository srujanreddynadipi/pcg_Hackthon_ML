"""
Predictor - Makes predictions with all 4 models
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import hstack, csr_matrix
from config.settings import CATEGORY_RESOLVER_MAP, PRIORITY_MATRIX, DUPLICATE_SIMILARITY_THRESHOLD, CATEGORY_KEYWORDS

class TicketPredictor:
    def __init__(self, models):

        self.resolver_model = models['resolver_router']
        self.tfidf = models['tfidf_vectorizer']
        self.category_encoder = models['category_encoder']
        self.impact_encoder = models['impact_encoder']
        self.urgency_encoder = models['urgency_encoder']
        self.sentence_bert = models['sentence_bert']
        
        # Feature names for audit trail
        self.feature_names = self.tfidf.get_feature_names_out()
        
    def is_it_related(self, title, description):
        """Check if ticket is IT-related or irrelevant"""
        combined_text = f"{title} {description}".lower()
        
        # IT-related keywords
        it_keywords = [
            'software', 'hardware', 'application', 'system', 'server', 'network', 'computer',
            'laptop', 'desktop', 'printer', 'email', 'outlook', 'vpn', 'wifi', 'internet',
            'database', 'sql', 'cloud', 'azure', 'aws', 'access', 'login', 'password',
            'account', 'security', 'malware', 'virus', 'firewall', 'router', 'switch',
            'monitor', 'keyboard', 'mouse', 'scanner', 'phone', 'mobile', 'tablet',
            'error', 'issue', 'bug', 'crash', 'slow', 'not working', 'cannot connect',
            'installation', 'update', 'patch', 'upgrade', 'license', 'website', 'portal',
            'api', 'service', 'app', 'program', 'file', 'document', 'backup', 'recovery'
        ]
        
        # Non-IT keywords (facilities, HR, etc.)
        non_it_keywords = [
            'water', 'leakage', 'plumbing', 'bathroom', 'toilet', 'sink', 'faucet',
            'hvac', 'ac', 'heating', 'cooling', 'temperature', 'furniture', 'chair',
            'desk', 'table', 'door', 'lock', 'key', 'parking', 'elevator', 'stairs',
            'cleaning', 'janitor', 'trash', 'garbage', 'cafeteria', 'food', 'lunch',
            'payroll', 'salary', 'leave', 'vacation', 'sick', 'benefits', 'hr',
            'building', 'facility', 'maintenance', 'repair', 'construction'
        ]
        
        # Count IT vs non-IT keyword matches
        it_score = sum(1 for kw in it_keywords if kw in combined_text)
        non_it_score = sum(1 for kw in non_it_keywords if kw in combined_text)
        
        # Only reject if clearly non-IT (non-IT score is significantly higher)
        if non_it_score >= 3 and non_it_score > (it_score * 2):
            return False, "Non-IT ticket detected. Please submit to appropriate department (Facilities/HR/Admin)."
        
        # Otherwise, accept it (let the ML model handle classification)
        return True, None
    
    def extract_keywords(self, text):
        """Extract category-specific keywords from text - matching training format"""
        text_lower = text.lower()
        
        # Must match exact order from training script
        keyword_features = {
            'has_network_keyword': int(any(kw in text_lower for kw in ['network', 'vpn', 'wifi', 'connection', 'internet', 'router', 'firewall', 'dns', 'ip'])),
            'has_hardware_keyword': int(any(kw in text_lower for kw in ['laptop', 'desktop', 'computer', 'monitor', 'keyboard', 'mouse', 'printer', 'hardware', 'device'])),
            'has_database_keyword': int(any(kw in text_lower for kw in ['database', 'sql', 'query', 'db', 'table', 'replication', 'backup', 'connection pool'])),
            'has_cloud_keyword': int(any(kw in text_lower for kw in ['azure', 'aws', 'cloud', 'vm', 'container', 'kubernetes', 'docker', 's3', 'blob'])),
            'has_security_keyword': int(any(kw in text_lower for kw in ['security', 'malware', 'virus', 'phishing', 'breach', 'unauthorized', 'certificate', 'firewall'])),
            'has_devops_keyword': int(any(kw in text_lower for kw in ['cicd', 'pipeline', 'jenkins', 'git', 'docker', 'kubernetes', 'terraform', 'helm', 'deployment'])),
            'has_email_keyword': int(any(kw in text_lower for kw in ['email', 'outlook', 'mailbox', 'exchange', 'mail', 'inbox', 'outbox', 'smtp']))
        }
        
        return keyword_features
    
    def predict_category(self, title, description):
        """Predict ticket category using keyword matching"""
        combined_text = f"{title} {description}".lower()
        
        # Keyword features
        keyword_features = self.extract_keywords(combined_text)
        
        # Score each category based on keyword matches
        category_scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined_text)
            category_scores[category] = score
        
        # Get predicted category (highest score)
        if max(category_scores.values()) > 0:
            category = max(category_scores, key=category_scores.get)
            confidence = min(0.95, 0.65 + (category_scores[category] * 0.05))
        else:
            # Default to Software if no keywords match
            category = "Software"
            confidence = 0.55
        
        # Get top 3 predictions
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        top_3 = []
        for cat, score in sorted_categories[:3]:
            conf = min(0.95, 0.65 + (score * 0.05)) if score > 0 else 0.35
            top_3.append({"category": cat, "confidence": conf})
        
        # Ensure we have 3 items
        while len(top_3) < 3:
            remaining = [c for c in CATEGORY_KEYWORDS.keys() if c not in [t["category"] for t in top_3]]
            if remaining:
                top_3.append({"category": remaining[0], "confidence": 0.30})
            else:
                break
        
        # Ensure predicted category is first
        if top_3[0]["category"] != category:
            top_3 = [{"category": category, "confidence": confidence}] + [t for t in top_3 if t["category"] != category][:2]
        
        # Feature importance based on matched keywords
        feature_importance = []
        if category in CATEGORY_KEYWORDS:
            for kw in CATEGORY_KEYWORDS[category]:
                if kw in combined_text:
                    feature_importance.append({"feature": kw, "importance": 0.08})
        
        return {
            "category": category,
            "confidence": confidence,
            "top_3": top_3[:3],
            "keyword_matches": keyword_features,
            "feature_importance": feature_importance[:10]
        }
    
    def predict_priority(self, title, description, category):
        """Predict ticket priority based on impact and urgency"""
        combined_text = f"{title} {description}".lower()
        
        # Determine Impact
        impact = "Low"
        if any(word in combined_text for word in ["critical", "production", "outage", "down", "all users", "entire"]):
            impact = "High"
        elif any(word in combined_text for word in ["multiple", "several", "department", "important", "affecting"]):
            impact = "Medium"
        
        # Determine Urgency
        urgency = "Low"
        if any(word in combined_text for word in ["urgent", "asap", "immediately", "emergency", "critical", "cannot work"]):
            urgency = "High"
        elif any(word in combined_text for word in ["soon", "today", "need", "important", "affecting work"]):
            urgency = "Medium"
        
        # Calculate Priority
        priority = PRIORITY_MATRIX.get((impact, urgency), "Low")
        
        # Confidence based on keyword matches
        confidence = 0.85 if priority in ["Critical", "High"] else 0.75
        
        return {
            "priority": priority,
            "impact": impact,
            "urgency": urgency,
            "confidence": confidence,
            "reasoning": f"Impact={impact} (based on scope), Urgency={urgency} (based on time sensitivity)"
        }
    
    def predict_resolver(self, title, description, category, impact, urgency):
        """Predict resolver group using the trained resolver model"""
        combined_text = f"{title} {description}"
        
        # TF-IDF features
        tfidf_features = self.tfidf.transform([combined_text])
        
        # Keyword features (in exact order from training)
        keyword_dict = self.extract_keywords(combined_text)
        keyword_features = np.array([
            keyword_dict['has_network_keyword'],
            keyword_dict['has_hardware_keyword'],
            keyword_dict['has_database_keyword'],
            keyword_dict['has_cloud_keyword'],
            keyword_dict['has_security_keyword'],
            keyword_dict['has_devops_keyword'],
            keyword_dict['has_email_keyword']
        ]).reshape(1, -1)
        
        # Encode categorical features (including affected_users)
        category_encoded = self.category_encoder.transform([category]).reshape(1, -1)
        impact_encoded = self.impact_encoder.transform([impact]).reshape(1, -1)
        urgency_encoded = self.urgency_encoder.transform([urgency]).reshape(1, -1)
        affected_users = np.array([[1]])  # Default to 1 user affected
        
        # Combine all features in the same order as training:
        # [TF-IDF, category, impact, urgency, affected_users, keywords]
        combined_features = hstack([
            tfidf_features,
            csr_matrix(category_encoded),
            csr_matrix(impact_encoded),
            csr_matrix(urgency_encoded),
            csr_matrix(affected_users),
            csr_matrix(keyword_features)
        ])
        
        # Predict resolver
        resolver = self.resolver_model.predict(combined_features)[0]
        probabilities = self.resolver_model.predict_proba(combined_features)[0]
        
        # Get confidence for the predicted resolver
        resolver_classes = self.resolver_model.classes_
        resolver_idx = np.where(resolver_classes == resolver)[0][0]
        confidence = float(probabilities[resolver_idx])
        
        return {
            "resolver_group": resolver,
            "confidence": confidence,
            "reasoning": f"ML model predicted {resolver} with {confidence:.1%} confidence based on category={category}, impact={impact}, urgency={urgency}"
        }
    
    def find_duplicates(self, title, description, historical_tickets=None):
        """Find duplicate/similar tickets using Sentence-BERT"""
        current_text = f"{title} {description}"
        current_embedding = self.sentence_bert.encode([current_text])
        
        if historical_tickets is None or len(historical_tickets) == 0:
            # No historical data - return empty
            return {
                "has_duplicates": False,
                "similar_tickets": [],
                "duplicate_count": 0,
                "reasoning": "No historical tickets available for comparison"
            }
        
        # Get embeddings for historical tickets
        historical_texts = [
            f"{t.get('title', '')} {t.get('description', '')}" 
            for t in historical_tickets
        ]
        historical_embeddings = self.sentence_bert.encode(historical_texts)
        
        # Calculate similarities
        similarities = cosine_similarity(current_embedding, historical_embeddings)[0]
        
        # Find duplicates above threshold
        duplicate_indices = np.where(similarities >= DUPLICATE_SIMILARITY_THRESHOLD)[0]
        
        # Get top similar tickets
        top_indices = np.argsort(similarities)[-5:][::-1]
        similar_tickets = [
            {
                "ticket_id": historical_tickets[idx].get('ticket_id', f'TICKET-{idx}'),
                "title": historical_tickets[idx].get('title', ''),
                "similarity": float(similarities[idx]),
                "status": historical_tickets[idx].get('status', 'Unknown'),
                "resolution": historical_tickets[idx].get('resolution', '')
            }
            for idx in top_indices
            if similarities[idx] > 0.5  # Only show >50% similar
        ]
        
        return {
            "has_duplicates": len(duplicate_indices) > 0,
            "similar_tickets": similar_tickets,
            "duplicate_count": len(duplicate_indices),
            "reasoning": f"Found {len(duplicate_indices)} tickets with >{DUPLICATE_SIMILARITY_THRESHOLD*100}% similarity"
        }
    
    def _get_feature_importance(self, tfidf_features, predicted_class_idx):
        """Get top contributing features for the prediction"""
        # Get feature importances for this class
        if hasattr(self.resolver_model, 'feature_importances_'):
            importances = self.resolver_model.feature_importances_
        else:
            # For models without feature_importances_, use coefficients or return empty
            return []
        
        # Get non-zero features from TF-IDF
        feature_indices = tfidf_features.nonzero()[1]
        
        if len(feature_indices) == 0:
            return []
        
        # Get importance scores for these features
        feature_scores = [
            {
                "feature": self.feature_names[idx],
                "importance": float(importances[idx])
            }
            for idx in feature_indices
        ]
        
        # Sort by importance and return top 10
        feature_scores.sort(key=lambda x: x['importance'], reverse=True)
        return feature_scores[:10]
