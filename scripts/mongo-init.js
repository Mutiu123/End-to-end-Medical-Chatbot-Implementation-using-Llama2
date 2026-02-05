// =============================================================================
// MongoDB Initialization Script
// Creates database, user, and indexes for Medical Chatbot
// =============================================================================

// Switch to the medical_chatbot database
db = db.getSiblingDB('medical_chatbot');

// Create application user with read/write permissions
db.createUser({
    user: 'chatbot_user',
    pwd: 'chatbot_password',  // Change in production
    roles: [
        {
            role: 'readWrite',
            db: 'medical_chatbot'
        }
    ]
});

// Create collections
db.createCollection('users');
db.createCollection('conversations');
db.createCollection('audit_logs');

// Create indexes for users collection
db.users.createIndex({ 'username': 1 }, { unique: true });
db.users.createIndex({ 'email': 1 }, { unique: true });
db.users.createIndex({ 'created_at': 1 });

// Create indexes for conversations collection
db.conversations.createIndex({ 'session_id': 1 }, { unique: true });
db.conversations.createIndex({ 'user_id': 1 });
db.conversations.createIndex({ 'created_at': 1 });
db.conversations.createIndex({ 'updated_at': 1 });

// Create indexes for audit_logs collection
db.audit_logs.createIndex({ 'timestamp': -1 });
db.audit_logs.createIndex({ 'user_id': 1 });
db.audit_logs.createIndex({ 'event_type': 1 });
db.audit_logs.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 7776000 }); // 90 days TTL

print('MongoDB initialization completed successfully');
