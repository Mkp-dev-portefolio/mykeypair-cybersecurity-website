# MyKeyPair AI Integration Setup

This document describes the AI integration capabilities implemented for the MyKeyPair cybersecurity website.

## Overview

The AI integration provides local and privacy-focused AI processing using:
- **Ollama** for local LLM processing
- **HuggingFace Transformers** for content analysis
- **Integrated services** for lead qualification and content processing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Services   │
│                 │    │                 │    │                 │
│ - Forms         │◄───┤ - Lead Capture  │◄───┤ - Ollama        │
│ - Content       │    │ - Content API   │    │ - HuggingFace   │
│ - Resources     │    │ - Analytics     │    │ - Content       │
│                 │    │                 │    │   Analyzer      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components

### 1. Ollama Integration (`src/scripts/ollama_integration.py`)

**Purpose**: Local AI processing for content generation, analysis, and lead qualification

**Features**:
- Content analysis and summarization
- Lead qualification scoring
- Security recommendation generation  
- Blog content creation
- Cybersecurity expertise simulation

**Configuration**: Uses local Ollama instance at `http://localhost:11434`

### 2. Content Analyzer (`src/backend/services/content_analyzer.py`)

**Purpose**: Fast, lightweight content analysis using HuggingFace transformers

**Features**:
- Sentiment analysis
- Compliance framework detection
- Service type classification
- Technical complexity assessment
- Business impact analysis
- Urgency scoring

**Models Used**:
- `cardiffnlp/twitter-roberta-base-sentiment-latest` - Sentiment analysis
- `facebook/bart-large-mnli` - Zero-shot classification
- `all-MiniLM-L6-v2` - Sentence embeddings

### 3. Lead Capture Service (`src/backend/services/lead_capture.py`)

**Purpose**: Enhanced lead management with AI-powered qualification

**AI Features**:
- Automatic lead scoring
- AI-generated summaries
- Sentiment analysis
- Intent classification
- Priority assignment

### 4. Configuration (`config/ai_models.json`)

**Purpose**: Centralized configuration for all AI models and parameters

**Includes**:
- Model selection and parameters
- Compliance framework patterns
- Scoring weights and thresholds
- Performance and security settings

## Installation

### Prerequisites

1. **Python 3.8+** with pip
2. **Ollama** installed locally (optional but recommended)

### Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install and setup Ollama** (optional):
   ```bash
   # Install Ollama (see https://ollama.ai/)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull recommended models
   ollama pull llama3.2
   ollama pull phi3
   ```

3. **Download HuggingFace models** (automatic on first run):
   ```bash
   python -c "from transformers import pipeline; pipeline('sentiment-analysis')"
   ```

## Usage

### Basic Testing

Run the integration test to verify setup:
```bash
python src/scripts/test_ai_integration.py
```

### Content Analysis

```python
from src.backend.services.content_analyzer import ContentAnalyzer

analyzer = ContentAnalyzer()

# Analyze content
content = "We need PKI implementation for PCI-DSS compliance..."
metrics = analyzer.analyze_content(content)

print(f"Sentiment: {metrics.sentiment_label}")
print(f"Technical Complexity: {metrics.technical_complexity}")
print(f"Business Impact: {metrics.business_impact}")
```

### Lead Qualification

```python
from src.backend.services.lead_capture import LeadCaptureService

service = LeadCaptureService()

# Create and qualify lead
lead_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "company": "TechCorp",
    "message": "Need urgent PKI implementation...",
    "service_interest": "PKI Implementation"
}

lead_id = service.create_lead(lead_data)
```

### Ollama Integration

```python
from src.scripts.ollama_integration import OllamaIntegration

ollama = OllamaIntegration()

# Generate security recommendations
recommendation = ollama.generate_security_recommendation(
    "How to implement zero-trust architecture?"
)

# Analyze content for compliance
analysis = ollama.analyze_cybersecurity_content(content)
```

## Configuration

### AI Models Configuration

Edit `config/ai_models.json` to customize:

- **Model selection** and parameters
- **Compliance frameworks** to detect
- **Scoring weights** for lead qualification
- **Performance** and security settings

### Environment Variables

Create `.env` file for sensitive configuration:
```env
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
HUGGINGFACE_CACHE_DIR=./model_cache
AI_DEBUG_MODE=false
```

## Compliance Frameworks Supported

The system can detect and analyze content for:

- **GDPR** - General Data Protection Regulation
- **SOX** - Sarbanes-Oxley Act
- **HIPAA** - Health Insurance Portability and Accountability Act
- **PCI-DSS** - Payment Card Industry Data Security Standard
- **ISO27001** - Information Security Management
- **NIST** - National Institute of Standards and Technology
- **CCPA** - California Consumer Privacy Act
- **SOC2** - System and Organization Controls 2

## Privacy & Security

### Local Processing
- **Ollama** runs entirely locally - no data sent to external services
- **HuggingFace models** run locally after initial download
- **No API keys** required for core functionality

### Data Handling
- Content is processed locally and not stored permanently
- Lead data follows standard data protection practices
- AI model outputs are logged for quality assurance only

### Security Features
- Input validation and sanitization
- Output filtering for sensitive information
- Audit logging of AI model usage
- Configurable data retention policies

## Performance

### Resource Requirements

- **CPU**: 4+ cores recommended for transformers
- **RAM**: 8GB+ recommended (4GB minimum)
- **Disk**: 5GB for model storage
- **GPU**: Optional but recommended for faster processing

### Optimization

- Models are cached locally after first download
- Batch processing for multiple requests
- Configurable timeout and retry settings
- Lightweight fallback models for resource-constrained environments

## Monitoring

### Health Checks

The system provides health check endpoints:
```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Test content analyzer
python -c "from src.backend.services.content_analyzer import ContentAnalyzer; ContentAnalyzer()"
```

### Logging

All AI operations are logged with:
- Processing time metrics
- Model performance data
- Error rates and failures
- Usage statistics

## Troubleshooting

### Common Issues

1. **Ollama Connection Failed**:
   - Verify Ollama is running: `ollama list`
   - Check port configuration in config file
   - Try restarting Ollama service

2. **HuggingFace Model Download Issues**:
   - Check internet connection
   - Verify disk space (5GB+ needed)
   - Clear cache directory if corrupted

3. **Memory Issues**:
   - Reduce batch size in configuration
   - Use lighter fallback models
   - Enable model offloading

4. **Slow Performance**:
   - Enable GPU processing if available
   - Increase timeout settings
   - Use smaller, faster models

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Development

### Adding New AI Features

1. **Extend content analyzer** for new analysis types
2. **Add Ollama prompts** for new use cases
3. **Update configuration** with new parameters
4. **Add tests** for new functionality

### Model Updates

Update models by:
1. Modifying `config/ai_models.json`
2. Testing with new models
3. Updating fallback configurations

## Support

For issues and questions:
- Check logs for error details
- Run integration tests for diagnostics
- Review configuration settings
- Consult HuggingFace and Ollama documentation

## Changelog

### Version 1.0.0 (Current)
- Initial AI integration setup
- Ollama local processing integration
- HuggingFace transformers content analysis
- Lead qualification with AI scoring
- Compliance framework detection
- Comprehensive configuration system
