"""
Intelligent Candidate Matching Algorithm
HiringReferrals Platform

Multi-factor matching with weighted scoring:
- Skills Match: 40% weight
- Experience Level: 25% weight  
- Education Match: 15% weight
- Location Preference: 10% weight
- Salary Expectation: 10% weight
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of skill matches"""
    EXACT = "exact"           # 100% match
    RELATED = "related"       # 80% match
    TRANSFERABLE = "transferable"  # 60% match


# Weight configuration for matching factors
MATCHING_WEIGHTS = {
    "skills": 0.40,       # 40%
    "experience": 0.25,   # 25%
    "education": 0.15,    # 15%
    "location": 0.10,     # 10%
    "salary": 0.10        # 10%
}

# Auto-shortlist threshold
AUTO_SHORTLIST_THRESHOLD = 70  # 70% match score

# Related skills mapping (skill -> related skills)
RELATED_SKILLS_MAP = {
    "python": ["django", "flask", "fastapi", "pandas", "numpy"],
    "javascript": ["typescript", "react", "vue", "angular", "nodejs"],
    "react": ["redux", "nextjs", "javascript", "typescript"],
    "nodejs": ["express", "javascript", "typescript", "nestjs"],
    "java": ["spring", "springboot", "hibernate", "maven"],
    "sql": ["mysql", "postgresql", "mongodb", "database"],
    "aws": ["cloud", "azure", "gcp", "devops"],
    "docker": ["kubernetes", "containerization", "devops"],
    "machine learning": ["ai", "deep learning", "tensorflow", "pytorch"],
    "data science": ["python", "statistics", "machine learning", "analytics"],
}

# Education level hierarchy
EDUCATION_HIERARCHY = {
    "phd": 5,
    "masters": 4,
    "bachelors": 3,
    "diploma": 2,
    "high_school": 1
}


class CandidateMatcher:
    """
    Intelligent candidate matching service with multi-factor
    weighted scoring algorithm.
    """
    
    def __init__(self, db):
        self.db = db
    
    def normalize_skill(self, skill: str) -> str:
        """Normalize skill name for comparison"""
        return skill.lower().strip().replace("-", " ").replace("_", " ")
    
    def calculate_skill_match(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
        preferred_skills: List[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate skill match score with exact, related, and transferable matches
        
        Returns:
            Skill match details with breakdown
        """
        if not required_skills:
            return {"score": 100, "matched": [], "missing": [], "type": "no_requirements"}
        
        candidate_skills_normalized = [self.normalize_skill(s) for s in candidate_skills]
        required_normalized = [self.normalize_skill(s) for s in required_skills]
        preferred_normalized = [self.normalize_skill(s) for s in (preferred_skills or [])]
        
        exact_matches = []
        related_matches = []
        transferable_matches = []
        missing_skills = []
        
        for req_skill in required_normalized:
            # Check exact match
            if req_skill in candidate_skills_normalized:
                exact_matches.append(req_skill)
                continue
            
            # Check related skills
            found_related = False
            for cand_skill in candidate_skills_normalized:
                related = RELATED_SKILLS_MAP.get(cand_skill, [])
                if req_skill in [self.normalize_skill(r) for r in related]:
                    related_matches.append({"required": req_skill, "matched_with": cand_skill})
                    found_related = True
                    break
                
                # Check reverse relationship
                related_of_req = RELATED_SKILLS_MAP.get(req_skill, [])
                if cand_skill in [self.normalize_skill(r) for r in related_of_req]:
                    related_matches.append({"required": req_skill, "matched_with": cand_skill})
                    found_related = True
                    break
            
            if not found_related:
                # Check for transferable (partial string match)
                for cand_skill in candidate_skills_normalized:
                    if req_skill in cand_skill or cand_skill in req_skill:
                        transferable_matches.append({"required": req_skill, "matched_with": cand_skill})
                        found_related = True
                        break
            
            if not found_related:
                missing_skills.append(req_skill)
        
        # Calculate weighted score
        total_required = len(required_normalized)
        exact_score = (len(exact_matches) / total_required) * 100
        related_score = (len(related_matches) / total_required) * 80
        transferable_score = (len(transferable_matches) / total_required) * 60
        
        skill_score = exact_score + related_score + transferable_score
        skill_score = min(100, skill_score)  # Cap at 100
        
        # Bonus for preferred skills
        if preferred_normalized:
            preferred_matched = sum(1 for p in preferred_normalized if p in candidate_skills_normalized)
            bonus = (preferred_matched / len(preferred_normalized)) * 10  # Up to 10% bonus
            skill_score = min(100, skill_score + bonus)
        
        return {
            "score": round(skill_score, 1),
            "exact_matches": exact_matches,
            "related_matches": related_matches,
            "transferable_matches": transferable_matches,
            "missing_skills": missing_skills,
            "total_required": total_required,
            "coverage": f"{len(exact_matches) + len(related_matches) + len(transferable_matches)}/{total_required}"
        }
    
    def calculate_experience_match(
        self,
        candidate_years: int,
        required_min: int,
        required_max: int = None,
        domain_match: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate experience match score
        """
        if required_max is None:
            required_max = required_min + 5
        
        # Perfect match within range
        if required_min <= candidate_years <= required_max:
            base_score = 100
        # Slightly under-experienced
        elif candidate_years < required_min:
            gap = required_min - candidate_years
            if gap <= 1:
                base_score = 85
            elif gap <= 2:
                base_score = 70
            else:
                base_score = max(40, 100 - (gap * 15))
        # Over-experienced
        else:
            over = candidate_years - required_max
            if over <= 2:
                base_score = 90  # Slightly over is okay
            elif over <= 5:
                base_score = 75
            else:
                base_score = 60  # May be overqualified
        
        # Domain relevance adjustment
        if not domain_match:
            base_score *= 0.8
        
        return {
            "score": round(base_score, 1),
            "candidate_years": candidate_years,
            "required_range": f"{required_min}-{required_max} years",
            "status": "match" if required_min <= candidate_years <= required_max else 
                     "under" if candidate_years < required_min else "over",
            "domain_relevant": domain_match
        }
    
    def calculate_education_match(
        self,
        candidate_education: List[str],
        required_level: str,
        preferred_fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate education match score
        """
        required_level_normalized = required_level.lower().replace(" ", "_")
        required_value = EDUCATION_HIERARCHY.get(required_level_normalized, 2)
        
        # Find highest education level
        candidate_highest = 0
        candidate_fields = []
        
        for edu in candidate_education:
            edu_lower = edu.lower()
            for level, value in EDUCATION_HIERARCHY.items():
                if level in edu_lower:
                    if value > candidate_highest:
                        candidate_highest = value
                    break
            candidate_fields.append(edu)
        
        # Calculate score based on level match
        if candidate_highest >= required_value:
            base_score = 100
        elif candidate_highest == required_value - 1:
            base_score = 80
        else:
            base_score = max(50, 100 - ((required_value - candidate_highest) * 20))
        
        # Field relevance bonus
        field_match = False
        if preferred_fields:
            for field in preferred_fields:
                for edu in candidate_fields:
                    if field.lower() in edu.lower():
                        field_match = True
                        base_score = min(100, base_score + 10)
                        break
        
        return {
            "score": round(base_score, 1),
            "candidate_level": list(EDUCATION_HIERARCHY.keys())[candidate_highest - 1] if candidate_highest > 0 else "unknown",
            "required_level": required_level,
            "field_match": field_match,
            "education_list": candidate_education
        }
    
    def calculate_location_match(
        self,
        candidate_location: str,
        job_location: str,
        candidate_willing_to_relocate: bool = False,
        remote_available: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate location preference match
        """
        candidate_loc = candidate_location.lower().strip()
        job_loc = job_location.lower().strip()
        
        # Exact match
        if candidate_loc == job_loc or candidate_loc in job_loc or job_loc in candidate_loc:
            return {"score": 100, "match_type": "exact", "details": "Same location"}
        
        # Remote job
        if remote_available or "remote" in job_loc:
            return {"score": 95, "match_type": "remote", "details": "Remote position available"}
        
        # Willing to relocate
        if candidate_willing_to_relocate:
            return {"score": 80, "match_type": "relocate", "details": "Candidate willing to relocate"}
        
        # Same country/region check (simplified)
        common_metros = ["bangalore", "mumbai", "delhi", "hyderabad", "chennai", "pune", "kolkata"]
        candidate_in_metro = any(m in candidate_loc for m in common_metros)
        job_in_metro = any(m in job_loc for m in common_metros)
        
        if candidate_in_metro and job_in_metro:
            return {"score": 60, "match_type": "different_metro", "details": "Different metro city"}
        
        return {"score": 40, "match_type": "mismatch", "details": "Location mismatch"}
    
    def calculate_salary_match(
        self,
        candidate_expected: float,
        job_min: float,
        job_max: float
    ) -> Dict[str, Any]:
        """
        Calculate salary expectation match
        """
        # Within range
        if job_min <= candidate_expected <= job_max:
            # Closer to min is better for employer
            range_position = (candidate_expected - job_min) / (job_max - job_min) if job_max > job_min else 0.5
            score = 100 - (range_position * 10)  # 90-100 for within range
            return {
                "score": round(score, 1),
                "match_type": "within_range",
                "negotiation_room": round(job_max - candidate_expected, 0)
            }
        
        # Below range (good for employer)
        if candidate_expected < job_min:
            return {
                "score": 100,
                "match_type": "below_range",
                "savings": round(job_min - candidate_expected, 0)
            }
        
        # Above range
        excess = candidate_expected - job_max
        excess_percent = (excess / job_max) * 100 if job_max > 0 else 0
        
        if excess_percent <= 10:
            score = 75
        elif excess_percent <= 20:
            score = 60
        elif excess_percent <= 30:
            score = 45
        else:
            score = max(20, 100 - excess_percent)
        
        return {
            "score": round(score, 1),
            "match_type": "above_range",
            "excess_amount": round(excess, 0),
            "excess_percent": round(excess_percent, 1)
        }
    
    async def calculate_match_score(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive match score for candidate-job pair
        
        Args:
            candidate: Candidate profile with skills, experience, etc.
            job: Job posting with requirements
            
        Returns:
            Complete match analysis with weighted score
        """
        # Extract job requirements
        job_skills = job.get("requirements", [])
        job_preferred_skills = job.get("preferred_skills", [])
        job_exp_min = job.get("experience_min", 0)
        job_exp_max = job.get("experience_max", job_exp_min + 5)
        job_education = job.get("education_required", "bachelors")
        job_location = job.get("location", "")
        job_salary_min = job.get("salary_min", 0)
        job_salary_max = job.get("salary_max", 0)
        job_remote = job.get("remote_available", False)
        
        # Extract candidate data
        cand_skills = candidate.get("skills", [])
        cand_experience = candidate.get("experience_years", 0)
        cand_education = candidate.get("education", [])
        cand_location = candidate.get("location", "")
        cand_relocate = candidate.get("willing_to_relocate", False)
        cand_expected_salary = candidate.get("expected_salary", 0)
        
        # Calculate individual scores
        skills_result = self.calculate_skill_match(cand_skills, job_skills, job_preferred_skills)
        experience_result = self.calculate_experience_match(cand_experience, job_exp_min, job_exp_max)
        education_result = self.calculate_education_match(cand_education, job_education)
        location_result = self.calculate_location_match(cand_location, job_location, cand_relocate, job_remote)
        
        # Salary match (only if both values available)
        if cand_expected_salary > 0 and job_salary_max > 0:
            salary_result = self.calculate_salary_match(cand_expected_salary, job_salary_min, job_salary_max)
        else:
            salary_result = {"score": 75, "match_type": "not_specified"}  # Neutral if not specified
        
        # Calculate weighted total
        weighted_score = (
            skills_result["score"] * MATCHING_WEIGHTS["skills"] +
            experience_result["score"] * MATCHING_WEIGHTS["experience"] +
            education_result["score"] * MATCHING_WEIGHTS["education"] +
            location_result["score"] * MATCHING_WEIGHTS["location"] +
            salary_result["score"] * MATCHING_WEIGHTS["salary"]
        )
        
        # Determine recommendation
        if weighted_score >= AUTO_SHORTLIST_THRESHOLD:
            recommendation = "auto_shortlist"
        elif weighted_score >= 60:
            recommendation = "manual_review"
        elif weighted_score >= 40:
            recommendation = "consider"
        else:
            recommendation = "not_recommended"
        
        return {
            "candidate_id": candidate.get("id"),
            "job_id": job.get("id"),
            "overall_score": round(weighted_score, 1),
            "recommendation": recommendation,
            "auto_shortlist": weighted_score >= AUTO_SHORTLIST_THRESHOLD,
            "breakdown": {
                "skills": {
                    "weight": f"{MATCHING_WEIGHTS['skills'] * 100}%",
                    "score": skills_result["score"],
                    "weighted": round(skills_result["score"] * MATCHING_WEIGHTS["skills"], 1),
                    "details": skills_result
                },
                "experience": {
                    "weight": f"{MATCHING_WEIGHTS['experience'] * 100}%",
                    "score": experience_result["score"],
                    "weighted": round(experience_result["score"] * MATCHING_WEIGHTS["experience"], 1),
                    "details": experience_result
                },
                "education": {
                    "weight": f"{MATCHING_WEIGHTS['education'] * 100}%",
                    "score": education_result["score"],
                    "weighted": round(education_result["score"] * MATCHING_WEIGHTS["education"], 1),
                    "details": education_result
                },
                "location": {
                    "weight": f"{MATCHING_WEIGHTS['location'] * 100}%",
                    "score": location_result["score"],
                    "weighted": round(location_result["score"] * MATCHING_WEIGHTS["location"], 1),
                    "details": location_result
                },
                "salary": {
                    "weight": f"{MATCHING_WEIGHTS['salary'] * 100}%",
                    "score": salary_result["score"],
                    "weighted": round(salary_result["score"] * MATCHING_WEIGHTS["salary"], 1),
                    "details": salary_result
                }
            },
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def find_matching_candidates(
        self,
        job_id: str,
        limit: int = 50,
        min_score: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Find and rank matching candidates for a job
        """
        # Get job details
        job = await self.db.jobs.find_one({"id": job_id}, {"_id": 0})
        if not job:
            return []
        
        # Get all candidate resumes
        resumes = await self.db.resumes.find({}, {"_id": 0}).to_list(500)
        
        matches = []
        for resume in resumes:
            # Build candidate profile from resume
            candidate = {
                "id": resume.get("candidate_id"),
                "skills": resume.get("skills", []),
                "experience_years": resume.get("experience_years", 0),
                "education": resume.get("education", []),
                "location": resume.get("parsed_data", {}).get("location", ""),
                "expected_salary": resume.get("parsed_data", {}).get("expected_salary", 0),
                "willing_to_relocate": resume.get("parsed_data", {}).get("willing_to_relocate", False)
            }
            
            # Calculate match
            match_result = await self.calculate_match_score(candidate, job)
            
            if match_result["overall_score"] >= min_score:
                match_result["resume_id"] = resume.get("id")
                match_result["candidate_name"] = resume.get("parsed_data", {}).get("name", "Unknown")
                matches.append(match_result)
        
        # Sort by score descending
        matches.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return matches[:limit]


def create_candidate_matcher(db) -> CandidateMatcher:
    return CandidateMatcher(db)
