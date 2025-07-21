import React, { useState, useEffect } from 'react';
import './ConsultationForm.css';

// ConsultationForm Component
// Enhanced React component for cybersecurity consultation requests
// Integrates with lead capture service and provides AI-powered qualification
const ConsultationForm = ({ onSubmit, initialData = {} }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    serviceInterest: 'pki-implementation',
    urgencyLevel: 'medium',
    budgetRange: '',
    preferredContactMethod: 'email',
    message: '',
    ...initialData
  });
  
  const [status, setStatus] = useState('idle'); // idle, submitting, success, error
  const [errors, setErrors] = useState({});
  const [isValid, setIsValid] = useState(false);

  // Validation rules
  const validateField = (name, value) => {
    switch (name) {
      case 'name':
        return value.length < 2 ? 'Name must be at least 2 characters' : null;
      case 'email':
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return !emailRegex.test(value) ? 'Please enter a valid email address' : null;
      case 'phone':
        const phoneRegex = /^[\+]?[1-9][\d]{0,2}[-\s]?\(?[0-9]{3}\)?[-\s]?[0-9]{3}[-\s]?[0-9]{4}$/;
        return value && !phoneRegex.test(value.replace(/\s/g, '')) ? 'Please enter a valid phone number' : null;
      case 'message':
        return value.length < 10 ? 'Message must be at least 10 characters' : null;
      default:
        return null;
    }
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    const newFormData = { ...formData, [name]: value };
    setFormData(newFormData);
    
    // Validate field
    const error = validateField(name, value);
    setErrors(prev => ({ ...prev, [name]: error }));
  };

  // Check form validity
  useEffect(() => {
    const requiredFields = ['name', 'email', 'message'];
    const hasRequiredFields = requiredFields.every(field => formData[field]);
    const hasNoErrors = Object.values(errors).every(error => !error);
    setIsValid(hasRequiredFields && hasNoErrors);
  }, [formData, errors]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!isValid) return;
    
    setStatus('submitting');
    
    const submissionData = {
      ...formData,
      lead_source: 'consultation_form',
      service_interest: formData.serviceInterest,
      timestamp: new Date().toISOString()
    };

    try {
      const response = await fetch('/api/leads/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submissionData),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        setStatus('success');
        
        // Call parent callback if provided
        if (onSubmit) {
          onSubmit(result);
        }
        
        // Track successful submission (analytics)
        if (window.gtag) {
          window.gtag('event', 'consultation_request', {
            event_category: 'engagement',
            event_label: formData.serviceInterest,
            value: 1
          });
        }
        
      } else {
        setStatus('error');
        console.error('Submission failed:', result.message);
      }
    } catch (error) {
      setStatus('error');
      console.error('Network error:', error);
    }
  };

  // Success state
  if (status === 'success') {
    return (
      <div className="consultation-form-success">
        <div className="success-icon">✓</div>
        <h3>Thank You!</h3>
        <p>
          Your consultation request has been submitted successfully. 
          Our cybersecurity experts will review your inquiry and contact you within 24 hours.
        </p>
        <div className="next-steps">
          <h4>What happens next?</h4>
          <ul>
            <li>We'll review your specific requirements</li>
            <li>A senior consultant will contact you for a preliminary discussion</li>
            <li>We'll schedule a detailed consultation call</li>
            <li>Receive a customized proposal for your cybersecurity needs</li>
          </ul>
        </div>
        <button 
          onClick={() => {
            setStatus('idle');
            setFormData({
              name: '', email: '', phone: '', company: '',
              serviceInterest: 'pki-implementation', urgencyLevel: 'medium',
              budgetRange: '', preferredContactMethod: 'email', message: ''
            });
          }}
          className="btn-secondary"
        >
          Submit Another Request
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="consultation-form">
      <div className="form-header">
        <h2>Request a Cybersecurity Consultation</h2>
        <p>Get expert advice on your security challenges from certified professionals</p>
      </div>

      {status === 'error' && (
        <div className="error-message">
          <strong>Error:</strong> Unable to submit your request. Please try again or contact us directly.
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
            onChange={handleChange}
            className={errors.name ? 'error' : ''}
            placeholder="Enter your full name"
            required
          />
          {errors.name && <span className="field-error">{errors.name}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="email">
            Email Address <span className="required">*</span>
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className={errors.email ? 'error' : ''}
            placeholder="your.email@company.com"
            required
          />
          {errors.email && <span className="field-error">{errors.email}</span>}
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="phone">Phone Number</label>
          <input
            type="tel"
            id="phone"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            className={errors.phone ? 'error' : ''}
            placeholder="+1 (555) 123-4567"
          />
          {errors.phone && <span className="field-error">{errors.phone}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="company">Company/Organization</label>
          <input
            type="text"
            id="company"
            name="company"
            value={formData.company}
            onChange={handleChange}
            placeholder="Your company name"
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="serviceInterest">Primary Service Interest</label>
          <select
            id="serviceInterest"
            name="serviceInterest"
            value={formData.serviceInterest}
            onChange={handleChange}
          >
            <option value="pki-implementation">PKI Implementation & Certificate Management</option>
            <option value="security-assessment">Security Assessment & Vulnerability Testing</option>
            <option value="compliance-audit">Compliance Audit (SOC 2, ISO 27001, GDPR)</option>
            <option value="penetration-testing">Penetration Testing & Red Team Exercises</option>
            <option value="incident-response">Incident Response & Forensics</option>
            <option value="security-architecture">Security Architecture Design</option>
            <option value="risk-management">Risk Management & Governance</option>
            <option value="cloud-security">Cloud Security Assessment</option>
            <option value="training">Security Awareness Training</option>
            <option value="other">Other (Please specify in message)</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="urgencyLevel">Urgency Level</label>
          <select
            id="urgencyLevel"
            name="urgencyLevel"
            value={formData.urgencyLevel}
            onChange={handleChange}
          >
            <option value="low">Low - Planning phase (3+ months)</option>
            <option value="medium">Medium - Implementation needed (1-3 months)</option>
            <option value="high">High - Urgent requirement (within 1 month)</option>
            <option value="urgent">Critical - Immediate assistance needed</option>
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="budgetRange">Estimated Budget Range (Optional)</label>
          <select
            id="budgetRange"
            name="budgetRange"
            value={formData.budgetRange}
            onChange={handleChange}
          >
            <option value="">Prefer not to specify</option>
            <option value="under-25k">Under $25,000</option>
            <option value="25k-50k">$25,000 - $50,000</option>
            <option value="50k-100k">$50,000 - $100,000</option>
            <option value="100k-250k">$100,000 - $250,000</option>
            <option value="over-250k">Over $250,000</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="preferredContactMethod">Preferred Contact Method</label>
          <select
            id="preferredContactMethod"
            name="preferredContactMethod"
            value={formData.preferredContactMethod}
            onChange={handleChange}
          >
            <option value="email">Email</option>
            <option value="phone">Phone</option>
            <option value="video-call">Video Call (Teams/Zoom)</option>
            <option value="in-person">In-Person Meeting</option>
          </select>
        </div>
      </div>

      <div className="form-group full-width">
        <label htmlFor="message">
          Project Details & Requirements <span className="required">*</span>
        </label>
        <textarea
          id="message"
          name="message"
          value={formData.message}
          onChange={handleChange}
          className={errors.message ? 'error' : ''}
          rows="6"
          placeholder="Please describe your cybersecurity challenges, specific requirements, current security posture, compliance needs, or any other relevant information..."
          required
        />
        {errors.message && <span className="field-error">{errors.message}</span>}
        <small className="character-count">
          {formData.message.length} characters (minimum 10 required)
        </small>
      </div>

      <div className="form-footer">
        <button 
          type="submit" 
          className={`btn-primary ${!isValid || status === 'submitting' ? 'disabled' : ''}`}
          disabled={!isValid || status === 'submitting'}
        >
          {status === 'submitting' ? (
            <>
              <span className="spinner"></span>
              Submitting Request...
            </>
          ) : (
            'Submit Consultation Request'
          )}
        </button>
        
        <p className="privacy-notice">
          <small>
            By submitting this form, you agree to our{' '}
            <a href="/privacy-policy" target="_blank">Privacy Policy</a>.
            Your information is secure and will only be used to contact you regarding your consultation request.
          </small>
        </p>
      </div>
    </form>
  );
};

export default ConsultationForm;

