package services

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"
)

// LinkedInProfile represents a LinkedIn profile structure
type LinkedInProfile struct {
	ID            string    `json:"id"`
	FirstName     string    `json:"first_name"`
	LastName      string    `json:"last_name"`
	Email         string    `json:"email"`
	ProfileURL    string    `json:"profile_url"`
	Headline      string    `json:"headline"`
	Summary       string    `json:"summary"`
	Industry      string    `json:"industry"`
	Location      string    `json:"location"`
	Connections   int       `json:"connections"`
	Skills        []string  `json:"skills"`
	Experience    []Experience `json:"experience"`
	Education     []Education  `json:"education"`
	LastUpdated   time.Time `json:"last_updated"`
}

// Experience represents work experience
type Experience struct {
	Company     string `json:"company"`
	Title       string `json:"title"`
	Description string `json:"description"`
	StartDate   string `json:"start_date"`
	EndDate     string `json:"end_date"`
	Current     bool   `json:"current"`
}

// Education represents educational background
type Education struct {
	Institution string `json:"institution"`
	Degree      string `json:"degree"`
	FieldOfStudy string `json:"field_of_study"`
	StartDate   string `json:"start_date"`
	EndDate     string `json:"end_date"`
}

// LinkedInPost represents a LinkedIn post
type LinkedInPost struct {
	ID          string    `json:"id"`
	Text        string    `json:"text"`
	MediaURL    string    `json:"media_url,omitempty"`
	PostType    string    `json:"post_type"` // article, image, video, text
	Visibility  string    `json:"visibility"` // public, connections, private
	Tags        []string  `json:"tags"`
	Engagement  PostEngagement `json:"engagement"`
	CreatedAt   time.Time `json:"created_at"`
	ScheduledAt *time.Time `json:"scheduled_at,omitempty"`
}

// PostEngagement tracks post performance
type PostEngagement struct {
	Likes     int `json:"likes"`
	Comments  int `json:"comments"`
	Shares    int `json:"shares"`
	Views     int `json:"views"`
	ClickRate float64 `json:"click_rate"`
}

// ContentSuggestion represents AI-generated content suggestions
type ContentSuggestion struct {
	Type        string   `json:"type"` // educational, thought_leadership, case_study, industry_news
	Title       string   `json:"title"`
	Content     string   `json:"content"`
	Tags        []string `json:"tags"`
	BestTimes   []string `json:"best_times"`
	Rationale   string   `json:"rationale"`
	Confidence  float64  `json:"confidence"`
}

// OllamaRequest represents request to local Ollama instance
type OllamaRequest struct {
	Model  string `json:"model"`
	Prompt string `json:"prompt"`
	Stream bool   `json:"stream"`
}

// OllamaResponse represents response from Ollama
type OllamaResponse struct {
	Response string `json:"response"`
	Done     bool   `json:"done"`
}

// LinkedInIntegrationService handles LinkedIn optimization and content generation
type LinkedInIntegrationService struct {
	ollamaURL    string
	httpClient   *http.Client
	apiKey       string
	userProfiles map[string]*LinkedInProfile // In-memory cache
}

// NewLinkedInIntegrationService creates a new service instance
func NewLinkedInIntegrationService(ollamaURL, apiKey string) *LinkedInIntegrationService {
	return &LinkedInIntegrationService{
		ollamaURL: ollamaURL,
		apiKey:    apiKey,
		httpClient: &http.Client{
			Timeout: time.Second * 30,
		},
		userProfiles: make(map[string]*LinkedInProfile),
	}
}

// OptimizeProfile suggests improvements to a LinkedIn profile for cybersecurity professionals
func (s *LinkedInIntegrationService) OptimizeProfile(ctx context.Context, profile *LinkedInProfile) (*LinkedInProfile, error) {
	log.Printf("Optimizing LinkedIn profile for: %s %s", profile.FirstName, profile.LastName)

	// Generate optimized headline
	optimizedHeadline, err := s.generateOptimizedHeadline(ctx, profile)
	if err != nil {
		log.Printf("Error generating headline: %v", err)
	} else {
		profile.Headline = optimizedHeadline
	}

	// Generate optimized summary
	optimizedSummary, err := s.generateOptimizedSummary(ctx, profile)
	if err != nil {
		log.Printf("Error generating summary: %v", err)
	} else {
		profile.Summary = optimizedSummary
	}

	// Suggest cybersecurity skills
	suggestedSkills, err := s.suggestCybersecuritySkills(ctx, profile)
	if err != nil {
		log.Printf("Error suggesting skills: %v", err)
	} else {
		profile.Skills = s.mergeSkills(profile.Skills, suggestedSkills)
	}

	profile.LastUpdated = time.Now()
	s.userProfiles[profile.ID] = profile

	return profile, nil
}

// generateOptimizedHeadline creates an optimized LinkedIn headline for cybersecurity professionals
func (s *LinkedInIntegrationService) generateOptimizedHeadline(ctx context.Context, profile *LinkedInProfile) (string, error) {
	prompt := fmt.Sprintf(`
Generate an optimized LinkedIn headline for a cybersecurity professional based on their profile:

Name: %s %s
Current Headline: %s
Industry: %s
Experience: %s
Skills: %s

Requirements:
- Maximum 120 characters
- Include key cybersecurity specializations
- Use action words and quantifiable achievements
- Make it searchable with relevant keywords
- Professional and authoritative tone

Generate only the headline, no explanations:
`, profile.FirstName, profile.LastName, profile.Headline, profile.Industry,
		s.formatExperience(profile.Experience), strings.Join(profile.Skills, ", "))

	response, err := s.callOllama(ctx, prompt, "llama3.2")
	if err != nil {
		return profile.Headline, err
	}

	// Clean and validate the response
	headline := strings.TrimSpace(response)
	if len(headline) > 120 {
		headline = headline[:117] + "..."
	}

	return headline, nil
}

// generateOptimizedSummary creates an optimized LinkedIn summary
func (s *LinkedInIntegrationService) generateOptimizedSummary(ctx context.Context, profile *LinkedInProfile) (string, error) {
	prompt := fmt.Sprintf(`
Generate an optimized LinkedIn summary for a cybersecurity consultant based on their profile:

Name: %s %s
Current Summary: %s
Industry: %s
Location: %s
Experience: %s
Skills: %s
Education: %s

Requirements:
- 2000 character limit
- Professional first-person narrative
- Highlight cybersecurity expertise and achievements
- Include specific technologies and methodologies
- Add a call-to-action for potential clients
- Use industry keywords for LinkedIn search optimization
- Structure: Opening hook, expertise overview, key achievements, services offered, call-to-action

Generate only the summary text:
`, profile.FirstName, profile.LastName, profile.Summary, profile.Industry, profile.Location,
		s.formatExperience(profile.Experience), strings.Join(profile.Skills, ", "),
		s.formatEducation(profile.Education))

	response, err := s.callOllama(ctx, prompt, "llama3.2")
	if err != nil {
		return profile.Summary, err
	}

	summary := strings.TrimSpace(response)
	if len(summary) > 2000 {
		summary = summary[:1997] + "..."
	}

	return summary, nil
}

// suggestCybersecuritySkills suggests relevant cybersecurity skills
func (s *LinkedInIntegrationService) suggestCybersecuritySkills(ctx context.Context, profile *LinkedInProfile) ([]string, error) {
	prompt := fmt.Sprintf(`
Suggest 15-20 relevant cybersecurity skills for a LinkedIn profile based on their background:

Current Skills: %s
Experience: %s
Industry: %s
Role Focus: Cybersecurity Consulting

Categories to consider:
- Technical Security Tools (SIEM, IDS/IPS, Firewalls)
- Compliance Frameworks (NIST, ISO 27001, SOC 2, GDPR)
- Security Specializations (PKI, Penetration Testing, Incident Response)
- Programming/Scripting (Python, PowerShell, Bash)
- Cloud Security (AWS, Azure, GCP)
- Risk Management
- Governance and Strategy

Return only a comma-separated list of skills, no explanations:
`, strings.Join(profile.Skills, ", "), s.formatExperience(profile.Experience), profile.Industry)

	response, err := s.callOllama(ctx, prompt, "llama3.2")
	if err != nil {
		return []string{}, err
	}

	// Parse skills from response
	skillsStr := strings.TrimSpace(response)
	skills := strings.Split(skillsStr, ",")
	
	var cleanSkills []string
	for _, skill := range skills {
		skill = strings.TrimSpace(skill)
		if skill != "" && len(skill) < 50 { // LinkedIn skill character limit
			cleanSkills = append(cleanSkills, skill)
		}
	}

	return cleanSkills, nil
}

// GenerateContentSuggestions creates content suggestions for LinkedIn posts
func (s *LinkedInIntegrationService) GenerateContentSuggestions(ctx context.Context, profile *LinkedInProfile, count int) ([]ContentSuggestion, error) {
	log.Printf("Generating %d content suggestions for profile: %s", count, profile.ID)

	var suggestions []ContentSuggestion

	contentTypes := []string{"educational", "thought_leadership", "case_study", "industry_news"}
	
	for i := 0; i < count; i++ {
		contentType := contentTypes[i%len(contentTypes)]
		
		suggestion, err := s.generateContentSuggestion(ctx, profile, contentType)
		if err != nil {
			log.Printf("Error generating content suggestion: %v", err)
			continue
		}
		
		suggestions = append(suggestions, *suggestion)
	}

	return suggestions, nil
}

// generateContentSuggestion generates a single content suggestion
func (s *LinkedInIntegrationService) generateContentSuggestion(ctx context.Context, profile *LinkedInProfile, contentType string) (*ContentSuggestion, error) {
	prompt := fmt.Sprintf(`
Generate a LinkedIn post suggestion for a cybersecurity consultant:

Profile Context:
- Name: %s %s
- Expertise: %s
- Industry Focus: %s
- Skills: %s

Content Type: %s

Requirements based on content type:
- educational: Share cybersecurity best practices, tips, or tutorials
- thought_leadership: Industry insights, trends, or professional opinions
- case_study: Success story or project outcome (anonymized)
- industry_news: Commentary on recent cybersecurity events or trends

Format Requirements:
- 1300 characters maximum (LinkedIn limit)
- Professional but engaging tone
- Include 3-5 relevant hashtags
- Add a call-to-action or question for engagement
- Make it valuable to the cybersecurity community

Return in this exact JSON format:
{
  "title": "Brief title for the post",
  "content": "Full post content with hashtags",
  "tags": ["tag1", "tag2", "tag3"],
  "rationale": "Why this content would be effective"
}
`, profile.FirstName, profile.LastName, profile.Headline, profile.Industry, 
   strings.Join(profile.Skills[:5], ", "), contentType) // Limit skills for prompt brevity

	response, err := s.callOllama(ctx, prompt, "llama3.2")
	if err != nil {
		return nil, err
	}

	// Parse JSON response
	var suggestion ContentSuggestion
	err = json.Unmarshal([]byte(response), &suggestion)
	if err != nil {
		// Fallback if JSON parsing fails
		suggestion = ContentSuggestion{
			Type:       contentType,
			Title:      fmt.Sprintf("Cybersecurity %s Content", strings.Title(contentType)),
			Content:    strings.TrimSpace(response),
			Tags:       []string{"cybersecurity", "infosec", "security"},
			BestTimes:  []string{"Tuesday 9AM", "Wednesday 2PM", "Thursday 11AM"},
			Rationale:  "AI-generated content suggestion",
			Confidence: 0.7,
		}
	}

	suggestion.Type = contentType
	suggestion.BestTimes = []string{"Tuesday 9AM", "Wednesday 2PM", "Thursday 11AM"}
	suggestion.Confidence = 0.85

	return &suggestion, nil
}

// AnalyzePostPerformance analyzes the performance of LinkedIn posts
func (s *LinkedInIntegrationService) AnalyzePostPerformance(ctx context.Context, posts []LinkedInPost) (map[string]interface{}, error) {
	log.Printf("Analyzing performance of %d posts", len(posts))

	analysis := make(map[string]interface{})
	
	if len(posts) == 0 {
		return analysis, fmt.Errorf("no posts to analyze")
	}

	// Calculate engagement metrics
	var totalLikes, totalComments, totalShares, totalViews int
	var totalEngagementRate float64
	contentTypePerformance := make(map[string]PostEngagement)
	
	for _, post := range posts {
		totalLikes += post.Engagement.Likes
		totalComments += post.Engagement.Comments
		totalShares += post.Engagement.Shares
		totalViews += post.Engagement.Views
		
		engagementRate := float64(post.Engagement.Likes+post.Engagement.Comments+post.Engagement.Shares) / float64(post.Engagement.Views) * 100
		totalEngagementRate += engagementRate
		
		// Track by content type
		if existing, exists := contentTypePerformance[post.PostType]; exists {
			existing.Likes += post.Engagement.Likes
			existing.Comments += post.Engagement.Comments
			existing.Shares += post.Engagement.Shares
			existing.Views += post.Engagement.Views
			contentTypePerformance[post.PostType] = existing
		} else {
			contentTypePerformance[post.PostType] = post.Engagement
		}
	}

	avgEngagementRate := totalEngagementRate / float64(len(posts))
	
	analysis["total_posts"] = len(posts)
	analysis["avg_engagement_rate"] = avgEngagementRate
	analysis["total_engagement"] = map[string]int{
		"likes":    totalLikes,
		"comments": totalComments,
		"shares":   totalShares,
		"views":    totalViews,
	}
	analysis["content_type_performance"] = contentTypePerformance

	// Generate AI insights
	insights, err := s.generatePerformanceInsights(ctx, posts, analysis)
	if err == nil {
		analysis["ai_insights"] = insights
	}

	return analysis, nil
}

// generatePerformanceInsights generates AI insights from post performance data
func (s *LinkedInIntegrationService) generatePerformanceInsights(ctx context.Context, posts []LinkedInPost, analysis map[string]interface{}) (string, error) {
	prompt := fmt.Sprintf(`
Analyze LinkedIn post performance data and provide actionable insights:

Total Posts: %d
Average Engagement Rate: %.2f%%
Content Performance: %+v

Top Performing Posts:
%s

Provide 3-5 actionable insights for improving LinkedIn content performance:
1. What content types work best
2. Optimal posting strategies
3. Engagement optimization tips
4. Content format recommendations
5. Timing suggestions

Keep insights specific to cybersecurity consulting and professional services:
`, len(posts), analysis["avg_engagement_rate"], analysis["content_type_performance"],
		s.formatTopPosts(posts))

	response, err := s.callOllama(ctx, prompt, "llama3.2")
	if err != nil {
		return "", err
	}

	return strings.TrimSpace(response), nil
}

// callOllama makes a request to the local Ollama instance
func (s *LinkedInIntegrationService) callOllama(ctx context.Context, prompt, model string) (string, error) {
	request := OllamaRequest{
		Model:  model,
		Prompt: prompt,
		Stream: false,
	}

	jsonData, err := json.Marshal(request)
	if err != nil {
		return "", fmt.Errorf("error marshaling request: %v", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", s.ollamaURL+"/api/generate", bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("error creating request: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("error making request to Ollama: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("Ollama request failed with status: %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("error reading response body: %v", err)
	}

	var ollamaResp OllamaResponse
	err = json.Unmarshal(body, &ollamaResp)
	if err != nil {
		return "", fmt.Errorf("error unmarshaling response: %v", err)
	}

	return ollamaResp.Response, nil
}

// Helper functions

func (s *LinkedInIntegrationService) formatExperience(experiences []Experience) string {
	if len(experiences) == 0 {
		return "No experience listed"
	}
	
	var formatted []string
	for _, exp := range experiences {
		formatted = append(formatted, fmt.Sprintf("%s at %s", exp.Title, exp.Company))
	}
	
	return strings.Join(formatted, "; ")
}

func (s *LinkedInIntegrationService) formatEducation(education []Education) string {
	if len(education) == 0 {
		return "No education listed"
	}
	
	var formatted []string
	for _, edu := range education {
		formatted = append(formatted, fmt.Sprintf("%s in %s from %s", edu.Degree, edu.FieldOfStudy, edu.Institution))
	}
	
	return strings.Join(formatted, "; ")
}

func (s *LinkedInIntegrationService) mergeSkills(existing, suggested []string) []string {
	skillMap := make(map[string]bool)
	var merged []string
	
	// Add existing skills
	for _, skill := range existing {
		if !skillMap[strings.ToLower(skill)] {
			merged = append(merged, skill)
			skillMap[strings.ToLower(skill)] = true
		}
	}
	
	// Add suggested skills if not already present
	for _, skill := range suggested {
		if !skillMap[strings.ToLower(skill)] && len(merged) < 50 { // LinkedIn limit
			merged = append(merged, skill)
			skillMap[strings.ToLower(skill)] = true
		}
	}
	
	return merged
}

func (s *LinkedInIntegrationService) formatTopPosts(posts []LinkedInPost) string {
	if len(posts) == 0 {
		return "No posts available"
	}
	
	// Sort by engagement (simple metric: likes + comments + shares)
	sortedPosts := make([]LinkedInPost, len(posts))
	copy(sortedPosts, posts)
	
	// Simple bubble sort for top 3
	for i := 0; i < len(sortedPosts) && i < 3; i++ {
		for j := i + 1; j < len(sortedPosts); j++ {
			engagementI := sortedPosts[i].Engagement.Likes + sortedPosts[i].Engagement.Comments + sortedPosts[i].Engagement.Shares
			engagementJ := sortedPosts[j].Engagement.Likes + sortedPosts[j].Engagement.Comments + sortedPosts[j].Engagement.Shares
			
			if engagementJ > engagementI {
				sortedPosts[i], sortedPosts[j] = sortedPosts[j], sortedPosts[i]
			}
		}
	}
	
	var formatted []string
	limit := 3
	if len(sortedPosts) < 3 {
		limit = len(sortedPosts)
	}
	
	for i := 0; i < limit; i++ {
		post := sortedPosts[i]
		engagement := post.Engagement.Likes + post.Engagement.Comments + post.Engagement.Shares
		formatted = append(formatted, fmt.Sprintf("'%s' (%d total engagement)", 
			s.truncateText(post.Text, 50), engagement))
	}
	
	return strings.Join(formatted, "; ")
}

func (s *LinkedInIntegrationService) truncateText(text string, maxLen int) string {
	if len(text) <= maxLen {
		return text
	}
	return text[:maxLen-3] + "..."
}
