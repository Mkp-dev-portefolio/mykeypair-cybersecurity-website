import React, { useState, useEffect } from 'react';
import './ResourceDownload.css';

// ResourceDownload Component
// Gated content download component for lead generation
// Captures user information before allowing access to premium resources
const ResourceDownload = ({ 
  resource,
  variant = 'modal', // 'modal', 'inline', 'sidebar'
  onDownload,
  onLeadCapture 
}) => {
  const [isFormVisible, setIsFormVisible] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    jobTitle: '',
    useCase: '',
    marketingConsent: false
  });
  const [status, setStatus] = useState('idle'); // idle, submitting, success, error
  const [errors, setErrors] = useState({});
  const [downloadUrl, setDownloadUrl] = useState(null);

  // Default resource structure if none provided
  const defaultResource = {
    title: 'Cybersecurity Resource',
    description: 'Download our comprehensive guide',
    type: 'whitepaper',
    fileSize: '2.5MB',
    format: 'PDF',
    downloadCount: 1250,
    preview: null,
    thumbnail: '/assets/resource-thumbnail.png'
  };

  const resourceData = { ...defaultResource, ...resource };

  // Validation rules
  const validateField = (name, value) => {
    switch (name) {
      case 'name':
        return value.length < 2 ? 'Name must be at least 2 characters' : null;
      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return !emailRegex.test(value) ? 'Please enter a valid email address' : null;
      case 'company':
        return value.length < 2 ? 'Company name is required' : null;
      default:
        return null;
    }
  };

  const handleInputChange = (event) => {
    const { name, value, type, checked } = event.target;
    const inputValue = type === 'checkbox' ? checked : value;
    
    setFormData(prev => ({ ...prev, [name]: inputValue }));
    
    // Validate field
    if (type !== 'checkbox') {
      const error = validateField(name, value);
      setErrors(prev => ({ ...prev, [name]: error }));
    }
  };

  const handleDownloadRequest = () => {
    setIsFormVisible(true);
    
    // Analytics tracking
    if (window.gtag) {
      window.gtag('event', 'resource_download_initiated', {
        event_category: 'engagement',
        event_label: resourceData.title,
        resource_type: resourceData.type
      });
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    // Validate required fields
    const requiredFields = ['name', 'email', 'company'];
    const newErrors = {};
    let isValid = true;
    
    requiredFields.forEach(field => {
      const error = validateField(field, formData[field]);
      if (error || !formData[field]) {
        newErrors[field] = error || 'This field is required';
        isValid = false;
      }
    });
    
    setErrors(newErrors);
    
    if (!isValid) return;
    
    setStatus('submitting');
    
    const submissionData = {
      ...formData,
      lead_source: 'resource_download',
      resource_title: resourceData.title,
      resource_type: resourceData.type,
      service_interest: 'Content Download',
      message: `Downloaded: ${resourceData.title} (${resourceData.type})`,
      timestamp: new Date().toISOString()
    };
    
    try {
      // Submit lead information
      const leadResponse = await fetch('/api/leads/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submissionData),
      });
      
      const leadResult = await leadResponse.json();
      
      if (leadResponse.ok && leadResult.success) {
        // Generate download URL
        const downloadResponse = await fetch(`/api/resources/download/${resource?.id || 'default'}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: formData.email,
            lead_id: leadResult.lead_id
          }),
        });
        
        const downloadResult = await downloadResponse.json();
        
        if (downloadResponse.ok && downloadResult.success) {
          setDownloadUrl(downloadResult.download_url);
          setStatus('success');
          
          // Call callbacks
          if (onLeadCapture) {
            onLeadCapture(leadResult);
          }
          
          if (onDownload) {
            onDownload(downloadResult);
          }
          
          // Analytics tracking
          if (window.gtag) {
            window.gtag('event', 'resource_download_completed', {
              event_category: 'conversion',
              event_label: resourceData.title,
              resource_type: resourceData.type,
              lead_id: leadResult.lead_id
            });
          }
          
          // Auto-trigger download after short delay
          setTimeout(() => {
            if (downloadResult.download_url) {
              window.open(downloadResult.download_url, '_blank');
            }
          }, 1000);
          
        } else {
          setStatus('error');
          console.error('Download generation failed:', downloadResult.message);
        }
      } else {
        setStatus('error');
        console.error('Lead capture failed:', leadResult.message);
      }
    } catch (error) {
      setStatus('error');
      console.error('Network error:', error);
    }
  };

  const handleClose = () => {
    setIsFormVisible(false);
    setStatus('idle');
    setErrors({});
  };

  // Resource preview component
  const ResourcePreview = () => (
    <div className="resource-preview">
      <div className="resource-thumbnail">
        {resourceData.thumbnail ? (
          <img src={resourceData.thumbnail} alt={resourceData.title} />
        ) : (
          <div className="thumbnail-placeholder">
            <span className="file-icon">📄</span>
          </div>
        )}
      </div>
      
      <div className="resource-info">
        <h3 className="resource-title">{resourceData.title}</h3>
        <p className="resource-description">{resourceData.description}</p>
        
        <div className="resource-meta">
          <span className="resource-type">{resourceData.type}</span>
          <span className="resource-format">{resourceData.format}</span>
          <span className="resource-size">{resourceData.fileSize}</span>
          {resourceData.downloadCount && (
            <span className="download-count">
              {resourceData.downloadCount.toLocaleString()} downloads
            </span>
          )}
        </div>
        
        {resourceData.preview && (
          <div className="resource-preview-content">
            <h4>Preview:</h4>
            <p>{resourceData.preview}</p>
          </div>
        )}
      </div>
    </div>
  );

  // Download form component
  const DownloadForm = () => (
    <form onSubmit={handleSubmit} className="download-form">
      <div className="form-header">
        <h3>Download {resourceData.title}</h3>
        <p>Get instant access by providing your information below</p>
      </div>
      
      {status === 'error' && (
        <div className="error-message">
          Unable to process your request. Please try again or contact support.
        </div>
      )}
      
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="name">
            Full Name <span className="required">*</span>
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleInputChange}
            className={errors.name ? 'error' : ''}
            placeholder="Enter your full name"
            required
          />
          {errors.name && <span className="field-error">{errors.name}</span>}
        </div>
        
        <div className="form-group">
          <label htmlFor="email">
            Business Email <span className="required">*</span>
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            className={errors.email ? 'error' : ''}
            placeholder="your.email@company.com"
            required
          />
          {errors.email && <span className="field-error">{errors.email}</span>}
        </div>
      </div>
      
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="company">
            Company <span className="required">*</span>
          </label>
          <input
            type="text"
            id="company"
            name="company"
            value={formData.company}
            onChange={handleInputChange}
            className={errors.company ? 'error' : ''}
            placeholder="Your company name"
            required
          />
          {errors.company && <span className="field-error">{errors.company}</span>}
        </div>
        
        <div className="form-group">
          <label htmlFor="jobTitle">Job Title</label>
          <input
            type="text"
            id="jobTitle"
            name="jobTitle"
            value={formData.jobTitle}
            onChange={handleInputChange}
            placeholder="e.g., CISO, IT Manager"
          />
        </div>
      </div>
      
      <div className="form-group">
        <label htmlFor="useCase">How will you use this resource? (Optional)</label>
        <select
          id="useCase"
          name="useCase"
          value={formData.useCase}
          onChange={handleInputChange}
        >
          <option value="">Select a use case</option>
          <option value="research">Research and learning</option>
          <option value="implementation">Implementation planning</option>
          <option value="compliance">Compliance requirements</option>
          <option value="proposal">Proposal development</option>
          <option value="training">Team training</option>
          <option value="audit">Security audit</option>
          <option value="other">Other</option>
        </select>
      </div>
      
      <div className="form-group checkbox-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            name="marketingConsent"
            checked={formData.marketingConsent}
            onChange={handleInputChange}
          />
          <span className="checkmark"></span>
          I'd like to receive updates about cybersecurity best practices and MyKeyPair services
        </label>
      </div>
      
      <div className="form-footer">
        <button 
          type="submit" 
          className={`btn-primary ${status === 'submitting' ? 'loading' : ''}`}
          disabled={status === 'submitting'}
        >
          {status === 'submitting' ? (
            <>
              <span className="spinner"></span>
              Processing...
            </>
          ) : (
            `Download ${resourceData.format}`
          )}
        </button>
        
        <p className="privacy-notice">
          <small>
            By downloading this resource, you agree to our{' '}
            <a href="/privacy-policy" target="_blank">Privacy Policy</a>.
            Your information is secure and will only be used for the purposes stated.
          </small>
        </p>
      </div>
    </form>
  );

  // Success state component
  const SuccessState = () => (
    <div className="download-success">
      <div className="success-icon">✓</div>
      <h3>Download Ready!</h3>
      <p>
        Your download should start automatically. If it doesn't, use the link below.
      </p>
      
      {downloadUrl && (
        <div className="download-links">
          <a 
            href={downloadUrl} 
            className="btn-primary"
            target="_blank"
            rel="noopener noreferrer"
          >
            Download {resourceData.title}
          </a>
        </div>
      )}
      
      <div className="next-steps">
        <h4>What's next?</h4>
        <ul>
          <li>Check your email for additional resources</li>
          <li>Follow us for more cybersecurity insights</li>
          <li>Consider scheduling a consultation for personalized advice</li>
        </ul>
      </div>
      
      <div className="related-actions">
        <button 
          onClick={() => window.location.href = '/consultation'}
          className="btn-secondary"
        >
          Schedule a Consultation
        </button>
        <button 
          onClick={handleClose}
          className="btn-tertiary"
        >
          Continue Browsing
        </button>
      </div>
    </div>
  );

  // Render different variants
  if (variant === 'inline') {
    return (
      <div className="resource-download-inline">
        <ResourcePreview />
        
        {!isFormVisible && (
          <button 
            onClick={handleDownloadRequest}
            className="btn-primary download-trigger"
          >
            Download Now
          </button>
        )}
        
        {isFormVisible && status === 'success' && <SuccessState />}
        {isFormVisible && status !== 'success' && <DownloadForm />}
      </div>
    );
  }
  
  if (variant === 'sidebar') {
    return (
      <div className="resource-download-sidebar">
        <ResourcePreview />
        <button 
          onClick={handleDownloadRequest}
          className="btn-primary download-trigger"
        >
          Get Free Access
        </button>
        
        {isFormVisible && (
          <div className="sidebar-modal">
            <div className="modal-overlay" onClick={handleClose}></div>
            <div className="modal-content">
              <button className="close-button" onClick={handleClose}>×</button>
              {status === 'success' ? <SuccessState /> : <DownloadForm />}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Default modal variant
  return (
    <div className="resource-download-modal">
      <div className="resource-card" onClick={handleDownloadRequest}>
        <ResourcePreview />
        <button className="btn-primary download-trigger">
          Download Free Resource
        </button>
      </div>
      
      {isFormVisible && (
        <div className="modal-overlay" onClick={handleClose}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="close-button" onClick={handleClose}>×</button>
            {status === 'success' ? <SuccessState /> : <DownloadForm />}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResourceDownload;
