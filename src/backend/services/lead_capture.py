#!/usr/bin/env python3
"""
Lead Capture Service

This service handles lead generation, contact form processing, and inquiry management
for MyKeyPair's cybersecurity consulting services. It integrates with local AI models
via Ollama for intelligent lead qualification and automated responses.
"""

import json
import logging
import sqlite3
import smtplib
from datetime import datetime, timezone
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import requests
from transformers import pipeline
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Lead:
    """Lead data structure"""
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    company: str = ""
    phone: str = ""
    service_interest: str = ""
    message: str = ""
    lead_source: str = ""
    qualification_score: float = 0.0
    ai_summary: str = ""
    status: str = "new"  # new, qualified, contacted, converted, closed
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class ConsultationRequest:
    """Consultation request data structure"""
    id: Optional[int] = None
    lead_id: Optional[int] = None
    service_type: str = ""  # pki, compliance, penetration-testing, security-assessment
    preferred_date: str = ""
    preferred_time: str = ""
    project_scope: str = ""
    budget_range: str = ""
    urgency_level: str = "medium"  # low, medium, high, urgent
    requirements: str = ""
    created_at: Optional[str] = None

class LeadCaptureService:
    """Main service for handling lead capture and management"""
    
    def __init__(self, db_path: str = "leads.db", ollama_url: str = "http://localhost:11434"):
        self.db_path = db_path
        self.ollama_url = ollama_url
        self.sentiment_analyzer = None
        self._init_database()
        self._init_ai_models()
    
    def _init_database(self):
        """Initialize SQLite database for lead storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create leads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                company TEXT,
                phone TEXT,
                service_interest TEXT,
                message TEXT,
                lead_source TEXT,
                qualification_score REAL DEFAULT 0.0,
                ai_summary TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create consultation requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consultation_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                service_type TEXT NOT NULL,
                preferred_date TEXT,
                preferred_time TEXT,
                project_scope TEXT,
                budget_range TEXT,
                urgency_level TEXT DEFAULT 'medium',
                requirements TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        """)
        
        # Create lead interactions table for tracking follow-ups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lead_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                interaction_type TEXT NOT NULL,
                notes TEXT,
                interaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def _init_ai_models(self):
        """Initialize AI models for lead qualification"""
        try:
            # Initialize local sentiment analysis model
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
            logger.info("AI models initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize AI models: {e}")
            self.sentiment_analyzer = None
    
    def _call_ollama(self, prompt: str, model: str = "llama3.2") -> Optional[str]:
        """Call local Ollama instance for AI processing"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                logger.warning(f"Ollama request failed: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not connect to Ollama: {e}")
            return None
    
    def qualify_lead(self, lead: Lead) -> float:
        """Qualify lead using AI analysis and scoring criteria"""
        score = 0.0
        
        # Basic qualification criteria
        if lead.company:
            score += 20.0
        if lead.phone:
            score += 10.0
        if lead.service_interest:
            score += 25.0
        if len(lead.message) > 50:
            score += 15.0
        
        # AI-powered sentiment and intent analysis
        if self.sentiment_analyzer and lead.message:
            try:
                sentiment = self.sentiment_analyzer(lead.message)[0]
                if sentiment['label'] == 'POSITIVE':
                    score += sentiment['score'] * 20.0
                elif sentiment['label'] == 'NEUTRAL':
                    score += sentiment['score'] * 10.0
            except Exception as e:
                logger.warning(f"Sentiment analysis failed: {e}")
        
        # Ollama-powered intent analysis
        if lead.message:
            intent_prompt = f"""
            Analyze this cybersecurity inquiry and rate the business intent from 0-10:
            
            Message: "{lead.message}"
            Company: {lead.company or "Not specified"}
            Service Interest: {lead.service_interest or "Not specified"}
            
            Consider:
            - Urgency and specificity of the request
            - Budget implications
            - Technical complexity mentioned
            - Timeline indicators
            
            Respond with only a number from 0-10:
            """
            
            intent_score = self._call_ollama(intent_prompt)
            if intent_score and intent_score.isdigit():
                score += float(intent_score) * 1.0
        
        return min(score, 100.0)  # Cap at 100
    
    def generate_ai_summary(self, lead: Lead) -> str:
        """Generate AI summary of the lead"""
        if not lead.message:
            return "No message provided"
        
        summary_prompt = f"""
        Summarize this cybersecurity lead inquiry in 2-3 sentences:
        
        Name: {lead.name}
        Company: {lead.company or "Not specified"}
        Service Interest: {lead.service_interest or "General inquiry"}
        Message: "{lead.message}"
        
        Focus on:
        - Key cybersecurity needs mentioned
        - Urgency level
        - Potential services required
        
        Keep it professional and concise:
        """
        
        summary = self._call_ollama(summary_prompt)
        return summary or f"Inquiry from {lead.name} regarding {lead.service_interest or 'cybersecurity services'}"
    
    def create_lead(self, lead_data: Dict[str, Any]) -> Optional[int]:
        """Create a new lead record"""
        try:
            lead = Lead(**lead_data)
            
            # AI qualification and summary
            lead.qualification_score = self.qualify_lead(lead)
            lead.ai_summary = self.generate_ai_summary(lead)
            
            # Set status based on qualification score
            if lead.qualification_score >= 80:
                lead.status = "hot"
            elif lead.qualification_score >= 60:
                lead.status = "warm"
            else:
                lead.status = "cold"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO leads (name, email, company, phone, service_interest, 
                                 message, lead_source, qualification_score, ai_summary, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.name, lead.email, lead.company, lead.phone, lead.service_interest,
                lead.message, lead.lead_source, lead.qualification_score, lead.ai_summary, lead.status
            ))
            
            lead_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Created lead {lead_id} with score {lead.qualification_score:.1f}")
            
            # Send notification for high-value leads
            if lead.qualification_score >= 80:
                self._notify_high_value_lead(lead_id)
            
            return lead_id
            
        except sqlite3.IntegrityError:
            logger.warning(f"Lead with email {lead_data.get('email')} already exists")
            return None
        except Exception as e:
            logger.error(f"Error creating lead: {e}")
            return None
    
    def create_consultation_request(self, request_data: Dict[str, Any]) -> Optional[int]:
        """Create a consultation request"""
        try:
            request = ConsultationRequest(**request_data)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO consultation_requests (lead_id, service_type, preferred_date,
                                                 preferred_time, project_scope, budget_range,
                                                 urgency_level, requirements)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.lead_id, request.service_type, request.preferred_date,
                request.preferred_time, request.project_scope, request.budget_range,
                request.urgency_level, request.requirements
            ))
            
            request_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Created consultation request {request_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"Error creating consultation request: {e}")
            return None
    
    def get_leads(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get leads with optional status filter"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                "SELECT * FROM leads WHERE status = ? ORDER BY qualification_score DESC, created_at DESC LIMIT ?",
                (status, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM leads ORDER BY qualification_score DESC, created_at DESC LIMIT ?",
                (limit,)
            )
        
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return leads
    
    def update_lead_status(self, lead_id: int, status: str, notes: str = "") -> bool:
        """Update lead status and add interaction note"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update lead status
            cursor.execute(
                "UPDATE leads SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, lead_id)
            )
            
            # Add interaction record
            cursor.execute("""
                INSERT INTO lead_interactions (lead_id, interaction_type, notes)
                VALUES (?, ?, ?)
            """, (lead_id, f"status_change_to_{status}", notes))
            
            conn.commit()
            conn.close()
            logger.info(f"Updated lead {lead_id} to status {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating lead status: {e}")
            return False
    
    def _notify_high_value_lead(self, lead_id: int):
        """Send notification for high-value leads"""
        # This would integrate with email/Slack/Teams notification system
        logger.info(f"HIGH VALUE LEAD ALERT: Lead ID {lead_id} scored 80+")
        # Implementation would depend on notification preferences
    
    def export_leads_csv(self, filepath: str = "leads_export.csv"):
        """Export leads to CSV for analysis"""
        import csv
        
        leads = self.get_leads(limit=1000)
        
        with open(filepath, 'w', newline='') as csvfile:
            if leads:
                fieldnames = leads[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(leads)
        
        logger.info(f"Exported {len(leads)} leads to {filepath}")
        return filepath

# API endpoints for integration
def create_lead_api(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """API endpoint for creating leads"""
    service = LeadCaptureService()
    lead_id = service.create_lead(request_data)
    
    if lead_id:
        return {"success": True, "lead_id": lead_id, "message": "Lead created successfully"}
    else:
        return {"success": False, "message": "Failed to create lead"}

def create_consultation_api(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """API endpoint for creating consultation requests"""
    service = LeadCaptureService()
    request_id = service.create_consultation_request(request_data)
    
    if request_id:
        return {"success": True, "request_id": request_id, "message": "Consultation request created"}
    else:
        return {"success": False, "message": "Failed to create consultation request"}

if __name__ == "__main__":
    # Example usage
    service = LeadCaptureService()
    
    # Test lead creation
    test_lead = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "company": "TechCorp Inc",
        "phone": "+1-555-0123",
        "service_interest": "PKI Implementation",
        "message": "We need help implementing a comprehensive PKI infrastructure for our organization. We have about 500 employees and handle sensitive financial data.",
        "lead_source": "website_form"
    }
    
    lead_id = service.create_lead(test_lead)
    if lead_id:
        print(f"Created test lead with ID: {lead_id}")
        
        # Get lead details
        leads = service.get_leads(limit=1)
        if leads:
            print(f"Lead qualification score: {leads[0]['qualification_score']:.1f}")
            print(f"AI Summary: {leads[0]['ai_summary']}")
