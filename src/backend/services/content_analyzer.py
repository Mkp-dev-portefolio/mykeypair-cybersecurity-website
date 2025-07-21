#!/usr/bin/env python3
"""
Content Analyzer Service

This service uses HuggingFace transformers to analyze cybersecurity-related content,
including lead qualification, document classification, sentiment analysis, and 
compliance detection. It provides fast, lightweight AI processing for content analysis.

Author: MyKeyPair Cybersecurity Team
Version: 1.0.0
"""

import logging
import json
import re
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

# HuggingFace imports
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    pipeline, AutoModel
)
import torch
from sentence_transformers import SentenceTransformer, util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentAnalysisConfig:
    """Configuration for content analysis models"""
    cache_dir: str = "./model_cache"
    device: str = "auto"  # auto, cpu, cuda
    max_length: int = 512
    batch_size: int = 8
    confidence_threshold: float = 0.7
    
    def __post_init__(self):
        # Create cache directory
        Path(self.cache_dir).mkdir(exist_ok=True)
        
        # Determine device
        if self.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

@dataclass
class ContentMetrics:
    """Metrics for analyzed content"""
    sentiment_score: float
    sentiment_label: str
    technical_complexity: float
    business_impact: float
    urgency_score: float
    compliance_confidence: float
    security_risk_level: str
    processing_time: float

@dataclass
class ComplianceDetection:
    """Compliance framework detection results"""
    frameworks: List[str]
    confidence_scores: Dict[str, float]
    mentioned_standards: List[str]
    regulatory_keywords: List[str]

class ContentAnalyzer:
    """Main content analyzer using HuggingFace transformers"""
    
    def __init__(self, config: Optional[ContentAnalysisConfig] = None):
        self.config = config or ContentAnalysisConfig()
        self.models = {}
        self.tokenizers = {}
        self.pipelines = {}
        
        # Initialize models
        self._initialize_models()
        
        # Compliance framework patterns
        self.compliance_patterns = {
            'GDPR': [
                'gdpr', 'general data protection regulation', 'data protection',
                'privacy by design', 'data subject rights', 'data controller'
            ],
            'SOX': [
                'sarbanes-oxley', 'sox', 'financial reporting', 'audit controls',
                'internal controls', 'financial disclosure'
            ],
            'HIPAA': [
                'hipaa', 'health insurance portability', 'phi', 'protected health information',
                'healthcare data', 'medical records'
            ],
            'PCI-DSS': [
                'pci-dss', 'pci dss', 'payment card industry', 'cardholder data',
                'payment processing', 'card data security'
            ],
            'ISO27001': [
                'iso 27001', 'iso27001', 'information security management',
                'isms', 'security controls', 'iso certification'
            ],
            'NIST': [
                'nist', 'cybersecurity framework', 'nist csf', 'security controls',
                'nist 800-53', 'risk management framework'
            ],
            'CCPA': [
                'ccpa', 'california consumer privacy act', 'consumer privacy',
                'personal information', 'data sales disclosure'
            ]
        }
    
    def _initialize_models(self):
        """Initialize all required models"""
        try:
            logger.info("Initializing content analysis models...")
            
            # Sentiment analysis
            self.pipelines['sentiment'] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.config.device == "cuda" else -1,
                model_kwargs={"cache_dir": self.config.cache_dir}
            )
            
            # Text classification for cybersecurity content
            self.pipelines['security_classifier'] = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",  # Fallback to general model
                device=0 if self.config.device == "cuda" else -1,
                model_kwargs={"cache_dir": self.config.cache_dir}
            )
            
            # Sentence embeddings for semantic similarity
            self.sentence_model = SentenceTransformer(
                'all-MiniLM-L6-v2',
                cache_folder=self.config.cache_dir,
                device=self.config.device
            )
            
            # Zero-shot classification for service categorization
            self.pipelines['zero_shot'] = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if self.config.device == "cuda" else -1,
                model_kwargs={"cache_dir": self.config.cache_dir}
            )
            
            logger.info("✅ Content analysis models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            # Initialize with fallback lightweight models
            self._initialize_fallback_models()
    
    def _initialize_fallback_models(self):
        """Initialize lightweight fallback models"""
        try:
            logger.info("Initializing fallback models...")
            
            self.pipelines['sentiment'] = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=0 if self.config.device == "cuda" else -1
            )
            
            # Use basic text processing for other features
            logger.info("✅ Fallback models initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize fallback models: {e}")
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Analyze sentiment of text"""
        try:
            if 'sentiment' in self.pipelines:
                result = self.pipelines['sentiment'](text[:self.config.max_length])
                if isinstance(result, list):
                    result = result[0]
                return result['label'], result['score']
            else:
                # Fallback simple sentiment
                positive_words = ['good', 'great', 'excellent', 'pleased', 'satisfied', 'interested', 'urgent', 'need']
                negative_words = ['bad', 'poor', 'unsatisfied', 'problem', 'issue', 'urgent', 'breach', 'attack']
                
                text_lower = text.lower()
                pos_count = sum(1 for word in positive_words if word in text_lower)
                neg_count = sum(1 for word in negative_words if word in text_lower)
                
                if pos_count > neg_count:
                    return "POSITIVE", 0.7
                elif neg_count > pos_count:
                    return "NEGATIVE", 0.7
                else:
                    return "NEUTRAL", 0.6
                    
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return "NEUTRAL", 0.5
    
    def detect_compliance_frameworks(self, text: str) -> ComplianceDetection:
        """Detect mentioned compliance frameworks"""
        text_lower = text.lower()
        detected_frameworks = []
        confidence_scores = {}
        mentioned_standards = []
        regulatory_keywords = []
        
        for framework, patterns in self.compliance_patterns.items():
            matches = 0
            matched_patterns = []
            
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    matches += 1
                    matched_patterns.append(pattern)
            
            if matches > 0:
                confidence = min(matches / len(patterns), 1.0)
                if confidence >= 0.1:  # Low threshold for detection
                    detected_frameworks.append(framework)
                    confidence_scores[framework] = confidence
                    mentioned_standards.extend(matched_patterns)
        
        # Additional regulatory keywords
        reg_keywords = [
            'compliance', 'audit', 'regulatory', 'certification', 'standard',
            'framework', 'policy', 'procedure', 'control', 'governance'
        ]
        
        for keyword in reg_keywords:
            if keyword in text_lower:
                regulatory_keywords.append(keyword)
        
        return ComplianceDetection(
            frameworks=detected_frameworks,
            confidence_scores=confidence_scores,
            mentioned_standards=list(set(mentioned_standards)),
            regulatory_keywords=list(set(regulatory_keywords))
        )
    
    def classify_service_type(self, text: str) -> Dict[str, float]:
        """Classify the type of cybersecurity service needed"""
        service_labels = [
            "PKI Implementation",
            "Compliance Consulting",
            "Security Assessment",
            "Penetration Testing",
            "Incident Response",
            "Security Architecture",
            "Risk Management",
            "Security Training",
            "General Consultation"
        ]
        
        try:
            if 'zero_shot' in self.pipelines:
                result = self.pipelines['zero_shot'](text, service_labels)
                
                # Convert to probability dictionary
                service_probs = {}
                for label, score in zip(result['labels'], result['scores']):
                    service_probs[label] = float(score)
                
                return service_probs
            else:
                # Fallback keyword-based classification
                return self._keyword_based_service_classification(text)
                
        except Exception as e:
            logger.warning(f"Service classification failed: {e}")
            return {"General Consultation": 0.8}
    
    def _keyword_based_service_classification(self, text: str) -> Dict[str, float]:
        """Fallback keyword-based service classification"""
        text_lower = text.lower()
        
        service_keywords = {
            "PKI Implementation": ['pki', 'certificate', 'ca', 'certificate authority', 'digital signature'],
            "Compliance Consulting": ['compliance', 'audit', 'gdpr', 'hipaa', 'sox', 'pci'],
            "Security Assessment": ['assessment', 'review', 'evaluation', 'security posture'],
            "Penetration Testing": ['pentest', 'penetration test', 'vulnerability test', 'security test'],
            "Incident Response": ['incident', 'breach', 'attack', 'response', 'forensic'],
            "Security Architecture": ['architecture', 'design', 'framework', 'infrastructure'],
            "Risk Management": ['risk', 'risk management', 'risk assessment', 'threat'],
            "Security Training": ['training', 'education', 'awareness', 'workshop']
        }
        
        scores = {}
        total_matches = 0
        
        for service, keywords in service_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            scores[service] = matches
            total_matches += matches
        
        # Normalize scores
        if total_matches > 0:
            for service in scores:
                scores[service] = scores[service] / total_matches
        else:
            scores["General Consultation"] = 1.0
        
        return scores
    
    def calculate_technical_complexity(self, text: str) -> float:
        """Calculate technical complexity score"""
        technical_terms = [
            'encryption', 'decryption', 'algorithm', 'protocol', 'api', 'database',
            'infrastructure', 'architecture', 'implementation', 'integration',
            'cryptographic', 'authentication', 'authorization', 'firewall',
            'network', 'security', 'vulnerability', 'threat', 'malware',
            'certificate', 'ssl', 'tls', 'vpn', 'ids', 'ips', 'siem'
        ]
        
        text_lower = text.lower()
        words = text_lower.split()
        total_words = len(words)
        
        if total_words == 0:
            return 0.0
        
        technical_word_count = sum(1 for word in words if word in technical_terms)
        complexity_ratio = technical_word_count / total_words
        
        # Normalize to 0-1 scale
        return min(complexity_ratio * 3, 1.0)
    
    def calculate_urgency_score(self, text: str) -> float:
        """Calculate urgency score based on text content"""
        urgent_keywords = [
            'urgent', 'asap', 'immediately', 'emergency', 'critical',
            'breach', 'attack', 'compromised', 'hacked', 'incident',
            'deadline', 'time-sensitive', 'quickly', 'fast', 'soon'
        ]
        
        moderate_keywords = [
            'need', 'require', 'important', 'priority', 'planning',
            'project', 'implementation', 'upgrade', 'improvement'
        ]
        
        text_lower = text.lower()
        urgent_matches = sum(1 for keyword in urgent_keywords if keyword in text_lower)
        moderate_matches = sum(1 for keyword in moderate_keywords if keyword in text_lower)
        
        urgency_score = (urgent_matches * 0.8 + moderate_matches * 0.4) / len(text_lower.split())
        return min(urgency_score * 10, 1.0)
    
    def analyze_business_impact(self, text: str) -> float:
        """Analyze potential business impact"""
        high_impact_terms = [
            'revenue', 'financial', 'business critical', 'operations',
            'customers', 'reputation', 'compliance', 'regulatory',
            'data breach', 'downtime', 'productivity', 'competitive'
        ]
        
        impact_indicators = [
            'million', 'billion', 'enterprise', 'large-scale',
            'organization', 'company', 'business', 'corporate'
        ]
        
        text_lower = text.lower()
        impact_matches = sum(1 for term in high_impact_terms if term in text_lower)
        indicator_matches = sum(1 for term in impact_indicators if term in text_lower)
        
        impact_score = (impact_matches * 0.6 + indicator_matches * 0.3) / len(text_lower.split())
        return min(impact_score * 15, 1.0)
    
    def analyze_content(self, content: str, content_type: str = "general") -> ContentMetrics:
        """Comprehensive content analysis"""
        start_time = time.time()
        
        try:
            # Sentiment analysis
            sentiment_label, sentiment_score = self.analyze_sentiment(content)
            
            # Technical complexity
            technical_complexity = self.calculate_technical_complexity(content)
            
            # Business impact
            business_impact = self.analyze_business_impact(content)
            
            # Urgency score
            urgency_score = self.calculate_urgency_score(content)
            
            # Compliance detection
            compliance_detection = self.detect_compliance_frameworks(content)
            compliance_confidence = (
                sum(compliance_detection.confidence_scores.values()) / 
                max(len(compliance_detection.confidence_scores), 1)
            )
            
            # Security risk level
            risk_keywords = ['breach', 'attack', 'vulnerability', 'threat', 'risk', 'security issue']
            risk_count = sum(1 for keyword in risk_keywords if keyword in content.lower())
            
            if risk_count >= 3:
                security_risk_level = "HIGH"
            elif risk_count >= 1:
                security_risk_level = "MEDIUM"
            else:
                security_risk_level = "LOW"
            
            processing_time = time.time() - start_time
            
            return ContentMetrics(
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                technical_complexity=technical_complexity,
                business_impact=business_impact,
                urgency_score=urgency_score,
                compliance_confidence=compliance_confidence,
                security_risk_level=security_risk_level,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return ContentMetrics(
                sentiment_score=0.5,
                sentiment_label="NEUTRAL",
                technical_complexity=0.3,
                business_impact=0.5,
                urgency_score=0.3,
                compliance_confidence=0.0,
                security_risk_level="MEDIUM",
                processing_time=time.time() - start_time
            )
    
    def qualify_lead_content(self, lead_text: str, company_info: str = "") -> Dict[str, Any]:
        """Qualify lead based on content analysis"""
        # Analyze main content
        content_metrics = self.analyze_content(lead_text)
        
        # Service classification
        service_classification = self.classify_service_type(lead_text)
        top_service = max(service_classification, key=service_classification.get)
        
        # Compliance detection
        compliance_info = self.detect_compliance_frameworks(lead_text + " " + company_info)
        
        # Calculate overall qualification score
        qualification_factors = {
            'technical_complexity': content_metrics.technical_complexity * 0.2,
            'business_impact': content_metrics.business_impact * 0.3,
            'urgency': content_metrics.urgency_score * 0.2,
            'compliance_need': content_metrics.compliance_confidence * 0.15,
            'message_quality': (1.0 if len(lead_text.split()) > 20 else 0.5) * 0.15
        }
        
        qualification_score = sum(qualification_factors.values()) * 100
        
        # Determine priority level
        if qualification_score >= 80:
            priority_level = "HIGH"
        elif qualification_score >= 60:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"
        
        return {
            "qualification_score": round(qualification_score, 1),
            "priority_level": priority_level,
            "top_service": top_service,
            "service_confidence": service_classification.get(top_service, 0.0),
            "content_metrics": asdict(content_metrics),
            "compliance_frameworks": compliance_info.frameworks,
            "technical_complexity": content_metrics.technical_complexity,
            "business_impact_score": content_metrics.business_impact,
            "urgency_level": content_metrics.urgency_score,
            "sentiment": {
                "label": content_metrics.sentiment_label,
                "score": content_metrics.sentiment_score
            },
            "processing_time": content_metrics.processing_time
        }
    
    def batch_analyze(self, contents: List[str]) -> List[ContentMetrics]:
        """Batch analysis for multiple contents"""
        results = []
        
        for content in contents:
            try:
                result = self.analyze_content(content)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to analyze content: {e}")
                # Add default metrics for failed analysis
                results.append(ContentMetrics(
                    sentiment_score=0.5,
                    sentiment_label="NEUTRAL",
                    technical_complexity=0.3,
                    business_impact=0.3,
                    urgency_score=0.3,
                    compliance_confidence=0.0,
                    security_risk_level="MEDIUM",
                    processing_time=0.0
                ))
        
        return results

def test_content_analyzer():
    """Test function for content analyzer"""
    try:
        logger.info("Testing Content Analyzer...")
        
        analyzer = ContentAnalyzer()
        
        # Test content
        test_content = """
        We are a financial services company looking to implement a comprehensive PKI 
        infrastructure to meet PCI-DSS compliance requirements. Our current certificate 
        management is manual and we've had some security incidents recently. We need 
        this implemented urgently as our audit is in 3 months. Budget is around $200K.
        """
        
        # Basic content analysis
        metrics = analyzer.analyze_content(test_content)
        print(f"✅ Content Analysis:")
        print(f"   Sentiment: {metrics.sentiment_label} ({metrics.sentiment_score:.2f})")
        print(f"   Technical Complexity: {metrics.technical_complexity:.2f}")
        print(f"   Business Impact: {metrics.business_impact:.2f}")
        print(f"   Urgency Score: {metrics.urgency_score:.2f}")
        print(f"   Security Risk: {metrics.security_risk_level}")
        
        # Lead qualification
        qualification = analyzer.qualify_lead_content(test_content, "SecureBank Corp")
        print(f"\n✅ Lead Qualification:")
        print(f"   Score: {qualification['qualification_score']}")
        print(f"   Priority: {qualification['priority_level']}")
        print(f"   Top Service: {qualification['top_service']}")
        print(f"   Compliance Frameworks: {qualification['compliance_frameworks']}")
        
        # Service classification
        services = analyzer.classify_service_type(test_content)
        print(f"\n✅ Service Classification:")
        for service, score in sorted(services.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"   {service}: {score:.2f}")
        
        # Compliance detection
        compliance = analyzer.detect_compliance_frameworks(test_content)
        print(f"\n✅ Compliance Detection:")
        print(f"   Frameworks: {compliance.frameworks}")
        print(f"   Confidence Scores: {compliance.confidence_scores}")
        
        print(f"\n🎉 Content analyzer tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_content_analyzer()
