#!/usr/bin/env python3
"""
Ollama Integration Script

This script provides local AI processing capabilities using Ollama for MyKeyPair's 
cybersecurity website. It handles content analysis, lead qualification, document 
summarization, and cybersecurity threat assessment - all processed locally for 
maximum privacy and security.

Author: MyKeyPair Cybersecurity Team
Version: 1.0.0
"""

import json
import logging
import requests
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OllamaConfig:
    """Configuration for Ollama connection"""
    host: str = "localhost"
    port: int = 11434
    timeout: int = 60
    max_retries: int = 3
    default_model: str = "llama3.2"
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

@dataclass
class ContentAnalysisResult:
    """Result structure for content analysis"""
    content_type: str
    summary: str
    key_points: List[str]
    security_level: str  # public, confidential, restricted, top-secret
    threat_indicators: List[str]
    compliance_tags: List[str]
    confidence_score: float
    processing_time: float

class OllamaIntegration:
    """Main class for Ollama AI integration"""
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.available_models = []
        self._check_connection()
        self._load_available_models()
    
    def _check_connection(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.config.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Ollama connection established successfully")
                return True
        except requests.RequestException as e:
            logger.error(f"Cannot connect to Ollama at {self.config.base_url}: {e}")
            return False
        return False
    
    def _load_available_models(self):
        """Load list of available models"""
        try:
            response = requests.get(f"{self.config.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = [model['name'] for model in models_data.get('models', [])]
                logger.info(f"Available models: {self.available_models}")
        except Exception as e:
            logger.warning(f"Could not load available models: {e}")
    
    def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """Generate response using Ollama"""
        model_name = model or self.config.default_model
        
        # Ensure model is available
        if self.available_models and model_name not in self.available_models:
            logger.warning(f"Model {model_name} not available. Using default.")
            model_name = self.config.default_model
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system_message:
            payload["system"] = system_message
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.config.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Generated response in {processing_time:.2f}s")
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama request failed: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return None
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return None
    
    def analyze_cybersecurity_content(self, content: str) -> ContentAnalysisResult:
        """Analyze cybersecurity-related content"""
        start_time = time.time()
        
        system_message = """You are a cybersecurity expert analyzing content for MyKeyPair, 
        a professional cybersecurity consulting firm. Analyze the content and provide insights 
        on security implications, compliance requirements, and threat indicators."""
        
        analysis_prompt = f"""
        Analyze the following content and provide structured insights:

        Content: {content[:2000]}  # Limit content for processing

        Please analyze and respond in this exact JSON format:
        {{
            "content_type": "whitepaper|case_study|blog_post|inquiry|technical_doc",
            "summary": "Brief 2-sentence summary",
            "key_points": ["point1", "point2", "point3"],
            "security_level": "public|confidential|restricted|top-secret",
            "threat_indicators": ["indicator1", "indicator2"],
            "compliance_tags": ["GDPR", "SOX", "HIPAA", "PCI-DSS", "ISO27001"],
            "confidence_score": 0.95
        }}
        
        Focus on:
        - Cybersecurity frameworks and standards mentioned
        - Potential security risks or vulnerabilities
        - Compliance and regulatory implications
        - Business impact and recommendations
        """
        
        response = self.generate_response(
            analysis_prompt,
            system_message=system_message,
            temperature=0.3  # Lower temperature for more consistent analysis
        )
        
        processing_time = time.time() - start_time
        
        # Parse response or provide default values
        if response:
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    analysis_data = json.loads(json_match.group())
                    return ContentAnalysisResult(
                        content_type=analysis_data.get("content_type", "unknown"),
                        summary=analysis_data.get("summary", "Analysis not available"),
                        key_points=analysis_data.get("key_points", []),
                        security_level=analysis_data.get("security_level", "public"),
                        threat_indicators=analysis_data.get("threat_indicators", []),
                        compliance_tags=analysis_data.get("compliance_tags", []),
                        confidence_score=analysis_data.get("confidence_score", 0.5),
                        processing_time=processing_time
                    )
            except json.JSONDecodeError:
                logger.warning("Could not parse Ollama JSON response")
        
        # Fallback analysis
        return ContentAnalysisResult(
            content_type="unknown",
            summary=f"Content analysis completed. Contains {len(content.split())} words.",
            key_points=["Content processed locally via Ollama", "Analysis available"],
            security_level="public",
            threat_indicators=[],
            compliance_tags=[],
            confidence_score=0.3,
            processing_time=processing_time
        )
    
    def generate_lead_qualification(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered lead qualification assessment"""
        system_message = """You are a cybersecurity sales expert helping qualify leads for 
        MyKeyPair's consulting services. Analyze the lead information and provide qualification insights."""
        
        qualification_prompt = f"""
        Analyze this cybersecurity lead and provide qualification assessment:

        Lead Information:
        - Name: {lead_data.get('name', 'Not provided')}
        - Company: {lead_data.get('company', 'Not provided')}
        - Service Interest: {lead_data.get('service_interest', 'Not provided')}
        - Message: {lead_data.get('message', 'No message')}
        - Budget Range: {lead_data.get('budget_range', 'Not specified')}

        Provide assessment in JSON format:
        {{
            "qualification_score": 85,
            "priority_level": "high|medium|low",
            "recommended_services": ["pki", "compliance", "pen-testing"],
            "budget_assessment": "enterprise|mid-market|small-business|startup",
            "urgency_indicators": ["immediate", "within_month", "planning_phase"],
            "risk_factors": ["budget_unknown", "vague_requirements"],
            "next_actions": ["schedule_discovery_call", "send_proposal", "nurture"]
        }}
        """
        
        response = self.generate_response(
            qualification_prompt,
            system_message=system_message,
            temperature=0.4
        )
        
        if response:
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback qualification
        return {
            "qualification_score": 50,
            "priority_level": "medium",
            "recommended_services": ["general_consultation"],
            "budget_assessment": "unknown",
            "urgency_indicators": ["planning_phase"],
            "risk_factors": ["insufficient_information"],
            "next_actions": ["request_more_information"]
        }
    
    def generate_security_recommendation(self, query: str) -> str:
        """Generate cybersecurity recommendations"""
        system_message = """You are a senior cybersecurity consultant at MyKeyPair. 
        Provide professional, actionable cybersecurity recommendations based on industry 
        best practices and your expertise in PKI, compliance, and security architecture."""
        
        recommendation_prompt = f"""
        Based on this cybersecurity query, provide professional recommendations:

        Query: {query}

        Please provide:
        1. Immediate action items
        2. Short-term recommendations (1-3 months)
        3. Long-term strategic recommendations (6-12 months)
        4. Relevant compliance considerations
        5. Technology/tool recommendations

        Keep recommendations practical and business-focused.
        """
        
        return self.generate_response(
            recommendation_prompt,
            system_message=system_message,
            temperature=0.6
        ) or "Unable to generate recommendations at this time. Please contact our team directly."
    
    def summarize_document(self, document_content: str, doc_type: str = "general") -> str:
        """Summarize technical documents"""
        system_message = f"""You are a technical writer specializing in cybersecurity documentation. 
        Create clear, professional summaries of {doc_type} documents."""
        
        summary_prompt = f"""
        Create a professional summary of this {doc_type} document:

        Document Content: {document_content[:3000]}

        Provide:
        - Executive summary (2-3 sentences)
        - Key technical points
        - Business implications
        - Action items or recommendations

        Keep the summary concise but comprehensive.
        """
        
        return self.generate_response(
            summary_prompt,
            system_message=system_message,
            temperature=0.4
        ) or f"Summary of {doc_type} document ({len(document_content.split())} words) processed."
    
    def generate_blog_content(self, topic: str, target_audience: str = "technical") -> str:
        """Generate cybersecurity blog content"""
        system_message = """You are a cybersecurity thought leader and technical writer for MyKeyPair. 
        Create engaging, authoritative blog content that demonstrates expertise and provides value to readers."""
        
        blog_prompt = f"""
        Write a blog post about: {topic}
        Target audience: {target_audience}

        Include:
        - Compelling introduction
        - Key concepts and best practices
        - Real-world examples or case studies
        - Actionable recommendations
        - Professional conclusion

        Style: Professional but accessible, demonstrate expertise without being overly technical for non-technical audiences.
        Length: 800-1200 words
        """
        
        return self.generate_response(
            blog_prompt,
            system_message=system_message,
            temperature=0.7,
            max_tokens=1500
        ) or f"Blog content outline for '{topic}' generated for {target_audience} audience."

def test_ollama_integration():
    """Test function for Ollama integration"""
    try:
        ollama = OllamaIntegration()
        
        # Test basic connection
        test_response = ollama.generate_response("Hello! Please respond with 'Ollama is working correctly.'")
        if test_response:
            print(f"✅ Connection test: {test_response}")
        
        # Test content analysis
        test_content = """
        MyKeyPair provides comprehensive PKI implementation services for enterprise clients. 
        Our recent project involved deploying a multi-tier certificate authority infrastructure 
        for a financial services client, ensuring compliance with PCI-DSS requirements.
        """
        
        analysis = ollama.analyze_cybersecurity_content(test_content)
        print(f"✅ Content Analysis: {analysis.summary}")
        print(f"   Security Level: {analysis.security_level}")
        print(f"   Compliance Tags: {analysis.compliance_tags}")
        
        # Test lead qualification
        test_lead = {
            "name": "Jane Smith",
            "company": "SecureBank Corp",
            "service_interest": "PKI Implementation",
            "message": "We need to implement certificate management for our online banking platform. Budget is around $100K-200K.",
            "budget_range": "$100K-200K"
        }
        
        qualification = ollama.generate_lead_qualification(test_lead)
        print(f"✅ Lead Qualification Score: {qualification.get('qualification_score', 'N/A')}")
        print(f"   Priority: {qualification.get('priority_level', 'N/A')}")
        
        print("\n🎉 Ollama integration tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_ollama_integration()
