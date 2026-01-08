"""
AI-Powered Job Description Generator Service
Uses OpenAI GPT-4o via Emergent LLM Key to generate professional job descriptions.
"""
import os
import logging
from typing import Optional, Dict, Any, List
from uuid import uuid4
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Import emergent integrations
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    EMERGENT_AVAILABLE = True
except ImportError:
    EMERGENT_AVAILABLE = False
    logger.warning("emergentintegrations not available. JD generation will use fallback.")

class JDGeneratorService:
    """
    AI-powered Job Description Generator using OpenAI GPT-4o.
    """
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        self.model_provider = "openai"
        self.model_name = "gpt-4o"
        
        if not self.api_key:
            logger.warning("EMERGENT_LLM_KEY not found. JD generation will use fallback templates.")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for JD generation."""
        return """You are an expert HR professional and technical recruiter with 15+ years of experience writing compelling job descriptions. Your job descriptions are:

1. Clear and concise yet comprehensive
2. Inclusive and free from bias
3. SEO-optimized for job boards
4. Structured with clear sections
5. Engaging and attract top talent

When generating a job description, always include:
- A compelling job summary (2-3 sentences)
- Key responsibilities (5-8 bullet points)
- Required qualifications (5-7 bullet points)
- Preferred qualifications (3-5 bullet points)
- What we offer / Benefits (4-6 bullet points)
- About the company section placeholder

Use professional language but keep it engaging. Avoid jargon unless industry-specific.
Format the output in clean markdown."""
    
    async def generate_jd(
        self,
        job_title: str,
        company_name: str,
        department: Optional[str] = None,
        location: Optional[str] = None,
        employment_type: str = "Full-time",
        experience_level: str = "Mid-level",
        required_skills: Optional[List[str]] = None,
        salary_range: Optional[str] = None,
        additional_requirements: Optional[str] = None,
        company_description: Optional[str] = None,
        tone: str = "professional"  # professional, casual, startup
    ) -> Dict[str, Any]:
        """
        Generate a professional job description using AI.
        
        Args:
            job_title: The job title (e.g., "Senior Software Engineer")
            company_name: Name of the company
            department: Department name (optional)
            location: Job location
            employment_type: Full-time, Part-time, Contract, etc.
            experience_level: Entry-level, Mid-level, Senior, Lead, etc.
            required_skills: List of required skills
            salary_range: Salary range (optional)
            additional_requirements: Any additional requirements
            company_description: Brief company description
            tone: Tone of the JD (professional, casual, startup)
        
        Returns:
            Dict with generated JD and metadata
        """
        generation_id = str(uuid4())
        
        # Build the prompt
        prompt = self._build_prompt(
            job_title=job_title,
            company_name=company_name,
            department=department,
            location=location,
            employment_type=employment_type,
            experience_level=experience_level,
            required_skills=required_skills,
            salary_range=salary_range,
            additional_requirements=additional_requirements,
            company_description=company_description,
            tone=tone
        )
        
        # Try AI generation
        if EMERGENT_AVAILABLE and self.api_key:
            try:
                jd_content = await self._generate_with_ai(prompt)
                return {
                    "id": generation_id,
                    "success": True,
                    "job_title": job_title,
                    "company_name": company_name,
                    "content": jd_content,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "model": f"{self.model_provider}/{self.model_name}",
                    "is_ai_generated": True
                }
            except Exception as e:
                logger.error(f"AI generation failed: {e}")
                # Fall through to fallback
        
        # Fallback to template
        jd_content = self._generate_fallback(
            job_title=job_title,
            company_name=company_name,
            department=department,
            location=location,
            employment_type=employment_type,
            experience_level=experience_level,
            required_skills=required_skills,
            salary_range=salary_range
        )
        
        return {
            "id": generation_id,
            "success": True,
            "job_title": job_title,
            "company_name": company_name,
            "content": jd_content,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": "fallback_template",
            "is_ai_generated": False,
            "note": "Generated using template (AI unavailable)"
        }
    
    def _build_prompt(self, **kwargs) -> str:
        """Build the prompt for JD generation."""
        parts = [f"Generate a professional job description for the following position:\n"]
        
        parts.append(f"**Job Title:** {kwargs['job_title']}")
        parts.append(f"**Company:** {kwargs['company_name']}")
        
        if kwargs.get('department'):
            parts.append(f"**Department:** {kwargs['department']}")
        if kwargs.get('location'):
            parts.append(f"**Location:** {kwargs['location']}")
        
        parts.append(f"**Employment Type:** {kwargs['employment_type']}")
        parts.append(f"**Experience Level:** {kwargs['experience_level']}")
        
        if kwargs.get('required_skills'):
            skills_str = ", ".join(kwargs['required_skills'])
            parts.append(f"**Required Skills:** {skills_str}")
        
        if kwargs.get('salary_range'):
            parts.append(f"**Salary Range:** {kwargs['salary_range']}")
        
        if kwargs.get('additional_requirements'):
            parts.append(f"**Additional Requirements:** {kwargs['additional_requirements']}")
        
        if kwargs.get('company_description'):
            parts.append(f"**About the Company:** {kwargs['company_description']}")
        
        parts.append(f"\n**Tone:** {kwargs.get('tone', 'professional')}")
        
        parts.append("\nPlease generate a complete, well-structured job description in markdown format.")
        
        return "\n".join(parts)
    
    async def _generate_with_ai(self, prompt: str) -> str:
        """Generate JD using AI."""
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"jd_gen_{uuid4()}",
            system_message=self._get_system_prompt()
        ).with_model(self.model_provider, self.model_name)
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        return response
    
    def _generate_fallback(self, **kwargs) -> str:
        """Generate JD using fallback template."""
        skills_list = ""
        if kwargs.get('required_skills'):
            skills_list = "\n".join([f"- {skill}" for skill in kwargs['required_skills']])
        
        template = f"""# {kwargs['job_title']}

**Company:** {kwargs['company_name']}
**Location:** {kwargs.get('location', 'Remote/On-site')}
**Employment Type:** {kwargs['employment_type']}
**Experience Level:** {kwargs['experience_level']}
{f"**Salary Range:** {kwargs['salary_range']}" if kwargs.get('salary_range') else ''}

## About the Role

We are looking for a talented {kwargs['job_title']} to join our team at {kwargs['company_name']}. This is an exciting opportunity to work on challenging projects and grow your career.

## Key Responsibilities

- Design, develop, and maintain high-quality solutions
- Collaborate with cross-functional teams to define and implement new features
- Write clean, maintainable, and efficient code
- Participate in code reviews and provide constructive feedback
- Stay up-to-date with industry trends and best practices
- Mentor junior team members and contribute to team growth

## Required Qualifications

- {kwargs['experience_level']} experience in a similar role
- Strong problem-solving and analytical skills
- Excellent communication and collaboration abilities
- Bachelor's degree in a related field or equivalent experience
{skills_list if skills_list else '- Relevant technical skills for the position'}

## Preferred Qualifications

- Experience with agile development methodologies
- Track record of delivering projects on time
- Leadership experience or mentoring background
- Contributions to open-source projects

## What We Offer

- Competitive salary and benefits package
- Flexible work arrangements
- Professional development opportunities
- Collaborative and inclusive work environment
- Health insurance and wellness programs

## About {kwargs['company_name']}

[Company description placeholder - Add your company's mission, values, and culture here]

---

*{kwargs['company_name']} is an equal opportunity employer. We celebrate diversity and are committed to creating an inclusive environment for all employees.*
"""
        return template
    
    async def improve_jd(
        self,
        existing_jd: str,
        improvement_focus: str = "general"
    ) -> Dict[str, Any]:
        """
        Improve an existing job description.
        
        Args:
            existing_jd: The existing job description text
            improvement_focus: What to focus on (general, inclusivity, clarity, engagement)
        """
        if not EMERGENT_AVAILABLE or not self.api_key:
            return {
                "success": False,
                "error": "AI not available for JD improvement",
                "original": existing_jd
            }
        
        focus_prompts = {
            "general": "Improve this job description to make it more compelling and professional.",
            "inclusivity": "Review and improve this job description to make it more inclusive and free from bias.",
            "clarity": "Improve the clarity and structure of this job description.",
            "engagement": "Make this job description more engaging to attract top talent."
        }
        
        prompt = f"""{focus_prompts.get(improvement_focus, focus_prompts['general'])}

Existing Job Description:
```
{existing_jd}
```

Provide the improved version in markdown format."""
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"jd_improve_{uuid4()}",
                system_message="You are an expert HR professional specializing in writing inclusive, engaging job descriptions."
            ).with_model(self.model_provider, self.model_name)
            
            user_message = UserMessage(text=prompt)
            improved = await chat.send_message(user_message)
            
            return {
                "success": True,
                "original": existing_jd,
                "improved": improved,
                "improvement_focus": improvement_focus,
                "model": f"{self.model_provider}/{self.model_name}"
            }
        except Exception as e:
            logger.error(f"JD improvement failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "original": existing_jd
            }

# Singleton instance
jd_generator = JDGeneratorService()
