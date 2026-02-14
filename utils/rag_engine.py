"""
RAG Engine - Knowledge Base Search and Auto-Response Generation
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from config.settings import KB_TOP_K, KB_MIN_SIMILARITY, RESPONSE_TEMPLATES, CATEGORY_KEYWORDS

class RAGEngine:
    def __init__(self, sentence_bert):
        self.sentence_bert = sentence_bert
        
    def search_knowledge_base(self, title, description, category, knowledge_base=None):
        """Search knowledge base for similar issues and solutions"""
        current_text = f"{title} {description}"
        current_embedding = self.sentence_bert.encode([current_text])
        
        if knowledge_base is None or len(knowledge_base) == 0:
            # Return category-based generic solution
            return {
                "kb_articles": [],
                "has_known_solution": False,
                "reasoning": "No knowledge base available - using template-based response"
            }
        
        # Get embeddings for KB articles
        kb_texts = [
            f"{article.get('title', '')} {article.get('solution', '')}" 
            for article in knowledge_base
        ]
        kb_embeddings = self.sentence_bert.encode(kb_texts)
        
        # Calculate similarities
        similarities = cosine_similarity(current_embedding, kb_embeddings)[0]
        
        # Find top K articles above minimum similarity
        top_indices = np.argsort(similarities)[-KB_TOP_K:][::-1]
        kb_articles = [
            {
                "article_id": knowledge_base[idx].get('article_id', f'KB-{idx}'),
                "title": knowledge_base[idx].get('title', ''),
                "solution": knowledge_base[idx].get('solution', ''),
                "similarity": float(similarities[idx]),
                "category": knowledge_base[idx].get('category', '')
            }
            for idx in top_indices
            if similarities[idx] >= KB_MIN_SIMILARITY
        ]
        
        return {
            "kb_articles": kb_articles,
            "has_known_solution": len(kb_articles) > 0,
            "reasoning": f"Found {len(kb_articles)} relevant KB articles with >{KB_MIN_SIMILARITY*100}% similarity"
        }
    
    def generate_auto_response(self, category, title, description, kb_articles=None):
        """Generate auto-draft response based on category and KB"""
        # Get category-specific template
        template = RESPONSE_TEMPLATES.get(category, RESPONSE_TEMPLATES["Software"])
        
        # If KB articles exist, incorporate their solutions
        if kb_articles and len(kb_articles) > 0:
            kb_solutions = "\n\n**Related Solutions from Knowledge Base:**\n"
            for i, article in enumerate(kb_articles[:3], 1):
                kb_solutions += f"\n{i}. **{article['title']}** ({article['similarity']*100:.0f}% match)\n"
                kb_solutions += f"   {article['solution'][:200]}...\n"
            
            response = f"{template}\n{kb_solutions}"
        else:
            response = template
        
        # Add ticket-specific context
        response = f"**Ticket:** {title}\n\n{response}"
        
        return {
            "auto_response": response,
            "template_used": category,
            "kb_incorporated": len(kb_articles) > 0 if kb_articles else False,
            "confidence": 0.85 if kb_articles else 0.70
        }
    
    def detect_patterns(self, category, similar_tickets):
        """Detect patterns and trends in similar tickets"""
        if not similar_tickets or len(similar_tickets) < 3:
            return {
                "pattern_detected": False,
                "pattern_type": None,
                "insights": "Not enough historical data for pattern detection"
            }
        
        # Analyze similar tickets
        statuses = [t.get('status', '') for t in similar_tickets]
        resolved_count = sum(1 for s in statuses if s.lower() in ['resolved', 'closed'])
        
        # Pattern detection logic
        pattern_detected = False
        pattern_type = None
        insights = ""
        
        if len(similar_tickets) >= 5:
            pattern_detected = True
            pattern_type = "Recurring Incident"
            insights = f"⚠️ **Pattern Alert:** {len(similar_tickets)} similar {category} tickets found. "
            insights += f"This may indicate a recurring issue. "
            insights += f"{resolved_count}/{len(similar_tickets)} similar tickets were resolved. "
            
            if resolved_count > 0:
                insights += f"\n\n**Recommendation:** Review resolution history of similar tickets for faster resolution."
            else:
                insights += f"\n\n**Recommendation:** Escalate to management - unresolved recurring issue."
        
        return {
            "pattern_detected": pattern_detected,
            "pattern_type": pattern_type,
            "similar_count": len(similar_tickets),
            "resolved_count": resolved_count,
            "insights": insights
        }
    
    def generate_proactive_insights(self, category, priority, similar_tickets, kb_articles):
        """Generate proactive insights and recommendations"""
        insights = []
        
        # Priority-based insights
        if priority == "Critical":
            insights.append({
                "type": "SLA_RISK",
                "severity": "HIGH",
                "message": "🚨 Critical priority - SLA breach risk. Immediate action required.",
                "recommendation": "Assign to senior engineer and escalate to management."
            })
        
        # Pattern-based insights
        if similar_tickets and len(similar_tickets) >= 5:
            insights.append({
                "type": "RECURRING_ISSUE",
                "severity": "MEDIUM",
                "message": f"⚠️ {len(similar_tickets)} similar tickets found - recurring issue detected.",
                "recommendation": "Perform root cause analysis and implement permanent fix."
            })
        
        # KB-based insights
        if kb_articles and len(kb_articles) > 0:
            insights.append({
                "type": "KNOWN_SOLUTION",
                "severity": "LOW",
                "message": f"✅ {len(kb_articles)} KB articles match this issue - known solution available.",
                "recommendation": "Follow KB solution steps for faster resolution."
            })
        
        # Category-specific insights
        category_insights = {
            "Network": "Monitor network infrastructure for broader connectivity issues.",
            "Security": "Coordinate with Security Ops - potential security incident.",
            "Database": "Check database performance metrics and backup status.",
            "Cloud": "Review cloud service health dashboard for ongoing incidents."
        }
        
        if category in category_insights:
            insights.append({
                "type": "CATEGORY_SPECIFIC",
                "severity": "INFO",
                "message": f"💡 Category: {category}",
                "recommendation": category_insights[category]
            })
        
        return {
            "insights": insights,
            "insight_count": len(insights),
            "has_critical_insights": any(i['severity'] == 'HIGH' for i in insights)
        }
