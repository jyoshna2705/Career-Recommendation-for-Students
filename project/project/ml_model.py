from __future__ import annotations

from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


CAREER_DETAILS = {
    "Data Scientist": {
        "description": "Works with structured data, predictive models, and analytics to solve business and research problems.",
        "required_skills": ["Python", "Machine Learning", "Statistics", "Data Visualization"],
        "recommended_courses": [
            "Machine Learning Basics",
            "Data Analysis with Python",
            "Statistics for Data Science",
        ],
        "internships": [
            {
                "title": "Data Analyst Intern",
                "description": "Assist with dashboards, reports, and data cleaning for business insights.",
                "required_skills": "Python, SQL, Excel, Data Visualization",
            },
            {
                "title": "Machine Learning Intern",
                "description": "Support model training, evaluation, and experimentation on prediction tasks.",
                "required_skills": "Python, Machine Learning, Statistics",
            },
            {
                "title": "AI Research Intern",
                "description": "Explore data experiments and support prototype intelligence features.",
                "required_skills": "Python, Analytics, Research Mindset",
            },
        ],
    },
    "Full Stack Developer": {
        "description": "Builds complete web applications across frontend interfaces, backend logic, and database integration.",
        "required_skills": ["HTML", "CSS", "JavaScript", "Flask", "SQL"],
        "recommended_courses": [
            "Responsive Web Design",
            "JavaScript Essentials",
            "Backend Development with Flask",
        ],
        "internships": [
            {
                "title": "Frontend Developer Intern",
                "description": "Create responsive pages and improve component-level user experience.",
                "required_skills": "HTML, CSS, JavaScript, UI Design",
            },
            {
                "title": "Backend Developer Intern",
                "description": "Support APIs, database operations, and server-side features.",
                "required_skills": "Flask, SQL, REST APIs, Python",
            },
            {
                "title": "Web Developer Intern",
                "description": "Build and maintain UI components and support backend integration tasks.",
                "required_skills": "HTML, CSS, JavaScript, API Basics",
            },
        ],
    },
    "AI Engineer": {
        "description": "Designs and deploys AI-powered systems using models, data pipelines, and intelligent automation.",
        "required_skills": ["Python", "AI", "Machine Learning", "Deep Learning"],
        "recommended_courses": [
            "Introduction to AI",
            "Deep Learning Foundations",
            "Applied Neural Networks",
        ],
        "internships": [
            {
                "title": "AI Engineering Intern",
                "description": "Prototype intelligent features and assist with model deployment workflows.",
                "required_skills": "Python, AI Concepts, Model Training",
            },
            {
                "title": "Computer Vision Intern",
                "description": "Work on image-based ML models and data preparation pipelines.",
                "required_skills": "Python, Deep Learning, Computer Vision",
            },
            {
                "title": "ML Platform Intern",
                "description": "Support training pipelines, evaluation tooling, and AI automation workflows.",
                "required_skills": "Python, Machine Learning, Deployment Basics",
            },
        ],
    },
    "Cybersecurity Analyst": {
        "description": "Protects systems, networks, and data by identifying threats and strengthening security controls.",
        "required_skills": ["Networking", "Security", "Risk Assessment", "Linux"],
        "recommended_courses": [
            "Network Security",
            "Ethical Hacking Basics",
            "Cyber Defense Operations",
        ],
        "internships": [
            {
                "title": "Security Analyst Intern",
                "description": "Monitor alerts, review vulnerabilities, and support secure operations.",
                "required_skills": "Networking, Security, Linux",
            },
            {
                "title": "Cybersecurity Intern",
                "description": "Assist with threat analysis, compliance checks, and incident documentation.",
                "required_skills": "Security Fundamentals, Risk Awareness, Networking",
            },
            {
                "title": "SOC Intern",
                "description": "Learn incident response workflows and help track suspicious activity.",
                "required_skills": "Networking, Security Monitoring, Linux",
            },
        ],
    },
    "Cloud Engineer": {
        "description": "Builds and manages scalable cloud infrastructure, deployment workflows, and platform services.",
        "required_skills": ["Cloud", "DevOps", "Linux", "Containers"],
        "recommended_courses": [
            "AWS Cloud Practitioner",
            "Azure Fundamentals",
            "DevOps and CI/CD",
        ],
        "internships": [
            {
                "title": "Cloud Operations Intern",
                "description": "Support cloud deployments, monitoring, and platform maintenance tasks.",
                "required_skills": "Cloud Basics, Linux, Monitoring",
            },
            {
                "title": "DevOps Intern",
                "description": "Assist with CI/CD pipelines, deployments, and automation workflows.",
                "required_skills": "DevOps, CI/CD, Linux, Containers",
            },
            {
                "title": "Infrastructure Intern",
                "description": "Help maintain services, deployment scripts, and cloud resource hygiene.",
                "required_skills": "Cloud Platforms, Scripting, Linux",
            },
        ],
    },
}


RULE_SIGNALS = {
    "Data Scientist": ["python", "data", "analytics", "statistics", "machine learning", "sql"],
    "Full Stack Developer": ["html", "css", "javascript", "web", "frontend", "backend", "flask"],
    "AI Engineer": ["ai", "ml", "machine learning", "deep learning", "neural", "python"],
    "Cybersecurity Analyst": ["networking", "security", "cyber", "linux", "risk", "firewall"],
    "Cloud Engineer": ["cloud", "devops", "aws", "azure", "linux", "containers", "docker"],
}


TRAINING_DATA = [
    ("python machine learning statistics pandas data visualization analytics data science", "Data Scientist"),
    ("sql python analytics dashboards statistics data science machine learning", "Data Scientist"),
    ("html css javascript web frontend backend flask sql ui", "Full Stack Developer"),
    ("web development html css javascript full stack backend database", "Full Stack Developer"),
    ("ai machine learning deep learning python neural networks intelligent systems", "AI Engineer"),
    ("artificial intelligence python ml deployment deep learning nlp", "AI Engineer"),
    ("networking security linux firewall threats incident response risk", "Cybersecurity Analyst"),
    ("cyber security network defense penetration testing linux", "Cybersecurity Analyst"),
    ("cloud devops aws azure docker kubernetes linux ci cd", "Cloud Engineer"),
    ("cloud infrastructure devops containers deployment automation aws", "Cloud Engineer"),
]


def _build_pipeline() -> Pipeline:
    texts = [text for text, _label in TRAINING_DATA]
    labels = [label for _text, label in TRAINING_DATA]
    pipeline = Pipeline(
        [
            ("vectorizer", TfidfVectorizer(ngram_range=(1, 2))),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )
    pipeline.fit(texts, labels)
    return pipeline


@lru_cache(maxsize=1)
def get_career_model() -> Pipeline:
    return _build_pipeline()


def _normalize_items(text: str) -> list[str]:
    raw = text.replace("/", ",").replace(";", ",")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _match_required_skills(student_text: str, required_skills: list[str]) -> tuple[list[str], list[str]]:
    matched: list[str] = []
    missing: list[str] = []
    lowered_text = student_text.lower()

    for skill in required_skills:
        if skill.lower() in lowered_text:
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing


def predict_careers(
    skills: str,
    interested_course: str,
    programming_languages: str,
    branch_interested: str,
    limit: int = 4,
) -> dict[str, object]:
    profile_text = " ".join(
        [skills.strip(), interested_course.strip(), programming_languages.strip(), branch_interested.strip()]
    ).lower()
    student_skill_items = _normalize_items(", ".join([skills, programming_languages]))
    model = get_career_model()
    probabilities = dict(zip(model.classes_, model.predict_proba([profile_text])[0]))

    recommendations: list[dict[str, object]] = []

    for career_name, details in CAREER_DETAILS.items():
        matched_skills, missing_skills = _match_required_skills(profile_text, details["required_skills"])
        rule_hits = sum(1 for signal in RULE_SIGNALS[career_name] if signal in profile_text)
        confidence_value = round((len(matched_skills) / len(details["required_skills"])) * 100)
        total_score = min(100, confidence_value + rule_hits * 8 + round(probabilities.get(career_name, 0) * 20))

        if total_score <= 0:
            continue

        recommendations.append(
            {
                "title": career_name,
                "description": details["description"],
                "required_skills": ", ".join(details["required_skills"]),
                "recommended_courses": ", ".join(details["recommended_courses"]),
                "courses": details["recommended_courses"],
                "confidence_score": f"{confidence_value}%",
                "confidence_value": confidence_value,
                "match_score": f"{total_score}%",
                "matched_skills": ", ".join(matched_skills) if matched_skills else "No direct match yet",
                "student_skills": ", ".join(student_skill_items) if student_skill_items else "Not provided",
                "skill_gaps": ", ".join(missing_skills) if missing_skills else "No major skill gaps",
                "skill_gap_list": missing_skills,
                "reason": f"Matched {len(matched_skills)} of {len(details['required_skills'])} required skills, with additional alignment from your course and branch interests.",
                "internships": details["internships"],
                "_sort_score": total_score,
            }
        )

    recommendations.sort(key=lambda item: (item["_sort_score"], item["confidence_value"]), reverse=True)
    recommendations = recommendations[:limit]

    if not recommendations:
        fallback = CAREER_DETAILS["Full Stack Developer"]
        recommendations = [
            {
                "title": "Full Stack Developer",
                "description": fallback["description"],
                "required_skills": ", ".join(fallback["required_skills"]),
                "recommended_courses": ", ".join(fallback["recommended_courses"]),
                "courses": fallback["recommended_courses"],
                "confidence_score": "20%",
                "confidence_value": 20,
                "match_score": "25%",
                "matched_skills": "No direct match yet",
                "student_skills": ", ".join(student_skill_items) if student_skill_items else "Not provided",
                "skill_gaps": ", ".join(fallback["required_skills"]),
                "skill_gap_list": fallback["required_skills"],
                "reason": "Your profile is still broad, so full stack development is suggested as a practical starting point.",
                "internships": fallback["internships"],
            }
        ]

    roadmap: list[dict[str, str]] = []
    seen_skills: set[str] = set()
    for recommendation in recommendations:
        for missing_skill in recommendation["skill_gap_list"]:
            if missing_skill in seen_skills:
                continue
            seen_skills.add(missing_skill)
            roadmap.append(
                {
                    "skill": missing_skill,
                    "course": next(
                        (
                            course
                            for course in recommendation["courses"]
                            if missing_skill.lower().split()[0] in course.lower()
                        ),
                        recommendation["courses"][0],
                    ),
                }
            )
        recommendation.pop("_sort_score", None)

    analytics = {
        "career_labels": [item["title"] for item in recommendations],
        "confidence_values": [item["confidence_value"] for item in recommendations],
        "matched_counts": [
            0 if item["matched_skills"] == "No direct match yet" else len(item["matched_skills"].split(", "))
            for item in recommendations
        ],
        "missing_counts": [
            0 if item["skill_gaps"] == "No major skill gaps" else len(item["skill_gaps"].split(", "))
            for item in recommendations
        ],
    }

    internship_groups = [
        {
            "career_name": item["title"],
            "internships": item["internships"],
        }
        for item in recommendations
    ]

    return {
        "recommendations": recommendations,
        "roadmap": roadmap,
        "analytics": analytics,
        "internship_groups": internship_groups,
    }
