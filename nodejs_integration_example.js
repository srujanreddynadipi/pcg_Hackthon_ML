/**
 * Node.js Integration Example
 * How to integrate ITSM AI API with Express.js + MongoDB backend
 */

const express = require('express');
const axios = require('axios');
const mongoose = require('mongoose');

// Mongoose Schema (from your existing backend)
const ticketSchema = new mongoose.Schema({
  ticket_id: { type: String, required: true, unique: true },
  user: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  category: String,
  priority: String,
  status: { type: String, default: 'Open' },
  resolver_group: String,
  ai_predictions: {
    category: Object,
    priority: Object,
    resolver: Object,
    duplicates: Object
  },
  ai_insights: {
    knowledge_base: Object,
    auto_response: Object,
    patterns: Object,
    proactive_insights: Object
  },
  audit_trail: Object,
  created_at: { type: Date, default: Date.now },
  updated_at: { type: Date, default: Date.now }
});

const Ticket = mongoose.model('Ticket', ticketSchema);

// AI API Configuration
const AI_API_URL = process.env.AI_API_URL || 'http://localhost:8000';

/**
 * Get historical tickets for duplicate detection
 */
async function getHistoricalTickets(limit = 100) {
  try {
    const tickets = await Ticket.find({ status: { $in: ['Open', 'Resolved'] } })
      .limit(limit)
      .sort({ created_at: -1 })
      .select('ticket_id title description status')
      .lean();
    
    return tickets;
  } catch (error) {
    console.error('Error fetching historical tickets:', error);
    return [];
  }
}

/**
 * Get knowledge base articles (mock - replace with your KB)
 */
async function getKnowledgeBase(category = null) {
  // Replace with actual KB query
  const mockKB = [
    {
      article_id: 'KB-001',
      title: 'VPN Connection Troubleshooting',
      solution: '1. Check internet connection\n2. Verify VPN credentials\n3. Restart VPN client\n4. Clear VPN cache',
      category: 'Network'
    },
    {
      article_id: 'KB-002',
      title: 'Password Reset Procedure',
      solution: '1. Go to password reset portal\n2. Enter email address\n3. Follow reset link\n4. Create new password',
      category: 'Access'
    }
  ];
  
  return category ? mockKB.filter(kb => kb.category === category) : mockKB;
}

/**
 * Call AI API for predictions
 */
async function getPredictions(ticketData) {
  try {
    const response = await axios.post(`${AI_API_URL}/predict`, {
      user: ticketData.user,
      title: ticketData.title,
      description: ticketData.description,
      historical_tickets: await getHistoricalTickets(),
      knowledge_base: await getKnowledgeBase()
    }, {
      timeout: 30000  // 30 second timeout
    });
    
    return response.data;
  } catch (error) {
    console.error('AI API Error:', error.message);
    
    // Fallback to default values if AI API fails
    return {
      predictions: {
        category: { predicted: 'Software', confidence: 0.5 },
        priority: { predicted: 'Medium', confidence: 0.5 },
        resolver_group: { assigned_to: 'Service Desk', confidence: 1.0 },
        duplicates: { has_duplicates: false, similar_tickets: [] }
      },
      rag_insights: {},
      audit_trail: {}
    };
  }
}

/**
 * Express.js Route - Create Ticket with AI Classification
 */
const app = express();
app.use(express.json());

app.post('/api/tickets', async (req, res) => {
  try {
    const { user, title, description } = req.body;
    
    // Validate input
    if (!user || !title || !description) {
      return res.status(400).json({
        error: 'Missing required fields: user, title, description'
      });
    }
    
    // Get AI predictions
    console.log('Getting AI predictions...');
    const aiResponse = await getPredictions({ user, title, description });
    
    // Create ticket with AI predictions
    const ticket = new Ticket({
      ticket_id: aiResponse.ticket_id,
      user,
      title,
      description,
      category: aiResponse.predictions.category.predicted,
      priority: aiResponse.predictions.priority.predicted,
      status: 'Open',
      resolver_group: aiResponse.predictions.resolver_group.assigned_to,
      ai_predictions: aiResponse.predictions,
      ai_insights: aiResponse.rag_insights,
      audit_trail: aiResponse.audit_trail
    });
    
    await ticket.save();
    
    console.log(`✅ Ticket created: ${ticket.ticket_id}`);
    
    // Return ticket with AI insights
    res.status(201).json({
      success: true,
      ticket: {
        ticket_id: ticket.ticket_id,
        user: ticket.user,
        title: ticket.title,
        description: ticket.description,
        category: ticket.category,
        priority: ticket.priority,
        status: ticket.status,
        resolver_group: ticket.resolver_group,
        created_at: ticket.created_at
      },
      ai_insights: {
        confidence: {
          category: aiResponse.predictions.category.confidence,
          priority: aiResponse.predictions.priority.confidence
        },
        duplicates: {
          found: aiResponse.predictions.duplicates.has_duplicates,
          count: aiResponse.predictions.duplicates.count,
          similar_tickets: aiResponse.predictions.duplicates.similar_tickets
        },
        auto_response: aiResponse.rag_insights.auto_response?.draft || null,
        proactive_insights: aiResponse.rag_insights.proactive_insights?.insights || []
      },
      processing_time_ms: aiResponse.processing_time_ms
    });
    
  } catch (error) {
    console.error('Error creating ticket:', error);
    res.status(500).json({
      error: 'Failed to create ticket',
      message: error.message
    });
  }
});

/**
 * Get Ticket with AI Insights
 */
app.get('/api/tickets/:ticket_id', async (req, res) => {
  try {
    const ticket = await Ticket.findOne({ ticket_id: req.params.ticket_id });
    
    if (!ticket) {
      return res.status(404).json({ error: 'Ticket not found' });
    }
    
    res.json({
      ticket: {
        ticket_id: ticket.ticket_id,
        user: ticket.user,
        title: ticket.title,
        description: ticket.description,
        category: ticket.category,
        priority: ticket.priority,
        status: ticket.status,
        resolver_group: ticket.resolver_group,
        created_at: ticket.created_at,
        updated_at: ticket.updated_at
      },
      ai_insights: ticket.ai_insights,
      ai_predictions: ticket.ai_predictions,
      audit_trail: ticket.audit_trail
    });
    
  } catch (error) {
    console.error('Error fetching ticket:', error);
    res.status(500).json({ error: 'Failed to fetch ticket' });
  }
});

/**
 * Re-classify Ticket (if user provides feedback)
 */
app.post('/api/tickets/:ticket_id/reclassify', async (req, res) => {
  try {
    const ticket = await Ticket.findOne({ ticket_id: req.params.ticket_id });
    
    if (!ticket) {
      return res.status(404).json({ error: 'Ticket not found' });
    }
    
    // Get new predictions
    const aiResponse = await getPredictions({
      user: ticket.user,
      title: ticket.title,
      description: ticket.description
    });
    
    // Update ticket
    ticket.category = aiResponse.predictions.category.predicted;
    ticket.priority = aiResponse.predictions.priority.predicted;
    ticket.resolver_group = aiResponse.predictions.resolver_group.assigned_to;
    ticket.ai_predictions = aiResponse.predictions;
    ticket.ai_insights = aiResponse.rag_insights;
    ticket.audit_trail = aiResponse.audit_trail;
    ticket.updated_at = new Date();
    
    await ticket.save();
    
    res.json({
      success: true,
      message: 'Ticket re-classified',
      ticket: {
        ticket_id: ticket.ticket_id,
        category: ticket.category,
        priority: ticket.priority,
        resolver_group: ticket.resolver_group
      }
    });
    
  } catch (error) {
    console.error('Error re-classifying ticket:', error);
    res.status(500).json({ error: 'Failed to re-classify ticket' });
  }
});

/**
 * Get Similar Tickets (Duplicate Check)
 */
app.post('/api/tickets/check-duplicates', async (req, res) => {
  try {
    const { title, description } = req.body;
    
    if (!title || !description) {
      return res.status(400).json({ error: 'Missing title or description' });
    }
    
    // Call AI API for duplicate detection
    const response = await axios.post(`${AI_API_URL}/predict`, {
      user: 'system',
      title,
      description,
      historical_tickets: await getHistoricalTickets()
    });
    
    res.json({
      has_duplicates: response.data.predictions.duplicates.has_duplicates,
      count: response.data.predictions.duplicates.count,
      similar_tickets: response.data.predictions.duplicates.similar_tickets
    });
    
  } catch (error) {
    console.error('Error checking duplicates:', error);
    res.status(500).json({ error: 'Failed to check duplicates' });
  }
});

/**
 * Health Check
 */
app.get('/api/health', async (req, res) => {
  try {
    // Check AI API health
    const aiHealth = await axios.get(`${AI_API_URL}/health`, { timeout: 5000 });
    
    // Check MongoDB connection
    const dbStatus = mongoose.connection.readyState === 1 ? 'connected' : 'disconnected';
    
    res.json({
      status: 'healthy',
      services: {
        api: 'healthy',
        database: dbStatus,
        ai_service: aiHealth.data.status
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

// Start server
const PORT = process.env.PORT || 3000;

mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/itsm', {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
.then(() => {
  console.log('✅ Connected to MongoDB');
  app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
    console.log(`🤖 AI API: ${AI_API_URL}`);
  });
})
.catch(err => {
  console.error('❌ MongoDB connection error:', err);
  process.exit(1);
});

module.exports = app;
