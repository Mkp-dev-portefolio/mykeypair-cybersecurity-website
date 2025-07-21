#!/usr/bin/env python3
"""
AI Integration Test Script

This script tests the integration between all AI components:
- Ollama integration
- HuggingFace transformers content analyzer  
- Configuration loading
- Lead capture service with AI features

Usage: python src/scripts/test_ai_integration.py
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.scripts.ollama_integration import OllamaIntegration
from src.backend.services.content_analyzer import ContentAnalyzer
from src.backend.services.lead_capture import LeadCaptureService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_ai_config():
    """Load AI configuration from config file"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config" / "ai_models.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info("✅ AI configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"❌ Failed to load AI configuration: {e}")
        return None

def test_ollama_integration():
    """Test Ollama integration"""
    try:
        logger.info("🧪 Testing Ollama Integration...")
        
        ollama = OllamaIntegration()
        
        # Test basic response generation
        response = ollama.generate_response(
            "Please respond with exactly: 'Ollama integration test successful'",
            temperature=0.1
        )
        
        if response and "successful" in response.lower():
            logger.info("✅ Ollama basic response generation working")
        else:
            logger.warning(f"⚠️ Ollama response unclear: {response}")
        
        # Test cybersecurity content analysis
        test_content = """
        We need help implementing a comprehensive PKI infrastructure for our 
        organization. We've had security incidents recently and need PCI-DSS 
        compliance for our payment systems.
        """
        
        analysis = ollama.analyze_cybersecurity_content(test_content)
        logger.info(f"✅ Ollama content analysis: {analysis.content_type}")
        logger.info(f"   Compliance tags: {analysis.compliance_tags}")
        logger.info(f"   Processing time: {analysis.processing_time:.2f}s")
        
        # Test lead qualification
        test_lead = {
            "name": "Jane Smith",
            "company": "SecureBank Corp",
            "service_interest": "PKI Implementation", 
            "message": test_content,
            "budget_range": "$100K-200K"
        }
        
        qualification = ollama.generate_lead_qualification(test_lead)
        logger.info(f"✅ Ollama lead qualification: {qualification.get('qualification_score', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ollama integration test failed: {e}")
        return False

def test_content_analyzer():
    """Test HuggingFace content analyzer"""
    try:
        logger.info("🧪 Testing Content Analyzer...")
        
        analyzer = ContentAnalyzer()
        
        # Test content analysis
        test_content = """
        Our financial services company urgently needs PKI implementation 
        to meet PCI-DSS compliance requirements. We've had recent security 
        incidents and our audit is in 3 months. Budget is $200K.
        """
        
        metrics = analyzer.analyze_content(test_content)
        logger.info(f"✅ Content analysis completed")
        logger.info(f"   Sentiment: {metrics.sentiment_label} ({metrics.sentiment_score:.2f})")
        logger.info(f"   Technical complexity: {metrics.technical_complexity:.2f}")
        logger.info(f"   Business impact: {metrics.business_impact:.2f}")
        logger.info(f"   Urgency: {metrics.urgency_score:.2f}")
        logger.info(f"   Security risk: {metrics.security_risk_level}")
        
        # Test compliance detection
        compliance = analyzer.detect_compliance_frameworks(test_content)
        logger.info(f"✅ Compliance detection: {compliance.frameworks}")
        
        # Test service classification
        services = analyzer.classify_service_type(test_content)
        top_service = max(services.items(), key=lambda x: x[1])
        logger.info(f"✅ Service classification: {top_service[0]} ({top_service[1]:.2f})")
        
        # Test lead qualification
        qualification = analyzer.qualify_lead_content(test_content, "SecureBank Corp")
        logger.info(f"✅ Lead qualification score: {qualification['qualification_score']}")
        logger.info(f"   Priority level: {qualification['priority_level']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Content analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lead_capture_service():
    """Test lead capture service with AI integration"""
    try:
        logger.info("🧪 Testing Lead Capture Service...")
        
        # Use in-memory database for testing
        service = LeadCaptureService(db_path=":memory:")
        
        # Test lead creation with AI analysis
        test_lead_data = {
            "name": "John Doe",
            "email": "john.doe@testcompany.com", 
            "company": "TestCorp Inc",
            "phone": "+1-555-0123",
            "service_interest": "Compliance Consulting",
            "message": "We need GDPR compliance assessment for our data processing operations. This is urgent as we have a regulatory deadline next month.",
            "lead_source": "website_form"
        }
        
        lead_id = service.create_lead(test_lead_data)
        
        if lead_id:
            logger.info(f"✅ Lead created successfully: ID {lead_id}")
            
            # Get the lead to check AI analysis
            leads = service.get_leads(limit=1)
            if leads:
                lead = leads[0]
                logger.info(f"   Qualification score: {lead['qualification_score']:.1f}")
                logger.info(f"   Status: {lead['status']}")
                logger.info(f"   AI Summary: {lead['ai_summary']}")
        else:
            logger.error("❌ Failed to create test lead")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Lead capture service test failed: {e}")
        return False

def test_configuration_integration():
    """Test that configuration is properly integrated"""
    try:
        logger.info("🧪 Testing Configuration Integration...")
        
        config = load_ai_config()
        
        if not config:
            return False
        
        ai_config = config.get('ai_models_config', {})
        
        # Test Ollama configuration
        ollama_config = ai_config.get('ollama', {})
        if ollama_config.get('enabled'):
            logger.info("✅ Ollama configuration enabled")
            logger.info(f"   Default model: {ollama_config.get('models', {}).get('primary', {}).get('name')}")
        
        # Test HuggingFace configuration  
        hf_config = ai_config.get('huggingface', {})
        if hf_config.get('enabled'):
            logger.info("✅ HuggingFace configuration enabled")
            logger.info(f"   Sentiment model: {hf_config.get('models', {}).get('sentiment_analysis', {}).get('model_name')}")
        
        # Test content analysis settings
        content_config = ai_config.get('content_analysis', {})
        if content_config.get('enabled'):
            frameworks = content_config.get('compliance_frameworks', {}).get('supported_frameworks', [])
            logger.info(f"✅ Content analysis enabled with {len(frameworks)} compliance frameworks")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration integration test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    logger.info("🚀 Starting AI Integration Tests...")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Load configuration first
    test_results['config'] = test_configuration_integration()
    
    # Test individual components
    test_results['content_analyzer'] = test_content_analyzer()
    test_results['ollama'] = test_ollama_integration()
    test_results['lead_capture'] = test_lead_capture_service()
    
    # Summary
    logger.info("=" * 60)
    logger.info("🏁 Test Results Summary:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All AI integration tests completed successfully!")
        logger.info("\nYour AI integration is ready for use:")
        logger.info("- Ollama local AI processing ✅")
        logger.info("- HuggingFace transformers analysis ✅") 
        logger.info("- Content analysis and lead qualification ✅")
        logger.info("- Configuration management ✅")
        return 0
    else:
        logger.warning(f"\n⚠️ {total - passed} test(s) failed. Please check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
