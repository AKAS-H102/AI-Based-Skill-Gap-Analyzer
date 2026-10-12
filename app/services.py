
import json

from .database import get_db
from ml.skill_gap import analyze
from ml.recommender import career_recommendations


def required_for_role(role_id):
    """Return the skills and proficiency requirements for a target role."""
    db = get_db()

    rows = db.execute(
        """
        SELECT
            s.id AS skill_id,
            s.name,
            s.category,
            j.required_level,
            j.weight
        FROM job_role_skills j
        JOIN skills s ON s.id = j.skill_id
        WHERE j.job_role_id = ?
        """,
        (role_id,),
    ).fetchall()

    return [dict(row) for row in rows]


def user_skill_map(user_id):
    """Return the user's current proficiency level for each selected skill."""
    db = get_db()

    rows = db.execute(
        """
        SELECT skill_id, level
        FROM user_skills
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchall()

    return {row["skill_id"]: row["level"] for row in rows}


def role_analysis(user_id, role_id):
    """Calculate skill matches and gaps for the selected role."""
    requirements = required_for_role(role_id)
    current_skills = user_skill_map(user_id)

    return analyze(requirements, current_skills)


def parse_topics(raw_topics):
    """
    Safely parse learning-resource topics.

    Supports JSON arrays, JSON strings, plain text, empty values,
    and values that have already been decoded.
    """
    if raw_topics is None:
        return []

    if isinstance(raw_topics, list):
        return raw_topics

    if isinstance(raw_topics, dict):
        return raw_topics

    if not isinstance(raw_topics, str):
        return []

    raw_topics = raw_topics.strip()

    if not raw_topics:
        return []

    try:
        parsed = json.loads(raw_topics)
    except (json.JSONDecodeError, TypeError, ValueError):
        # Preserve plain-text topics instead of crashing the analysis.
        return [raw_topics]

    if parsed is None:
        return []

    if isinstance(parsed, (list, dict)):
        return parsed

    if isinstance(parsed, str):
        return [parsed] if parsed.strip() else []

    return [parsed]


def learning_path(user_id, role_id):
    """
    Build a dependency-aware learning path.

    Avoid repeated profile lookups and safely handle invalid topic data.
    """
    analysis = role_analysis(user_id, role_id)

    db = get_db()
    path = []
    seen = set()

    # Fetch the user's current skill levels once.
    current_map = user_skill_map(user_id)

    for skill in analysis.get("skills", []):
        skill_id = skill.get("skill_id")
        required_level = skill.get("required_level", 0)
        gap = skill.get("gap", 0)

        if skill_id is None or gap <= 0:
            continue

        # Find prerequisite skills, ordered by dependency strength.
        dependencies = db.execute(
            """
            SELECT
                sd.depends_on_skill_id,
                s.name
            FROM skill_dependencies sd
            JOIN skills s
                ON s.id = sd.depends_on_skill_id
            WHERE sd.skill_id = ?
            ORDER BY sd.strength DESC
            """,
            (skill_id,),
        ).fetchall()

        ordered_skills = [dict(dep) for dep in dependencies]

        # Add the target skill after its prerequisites.
        ordered_skills.append(
            {
                "depends_on_skill_id": skill_id,
                "name": skill.get("name", "Unknown skill"),
            }
        )

        for dependency in ordered_skills:
            dependency_id = dependency["depends_on_skill_id"]

            if dependency_id in seen:
                continue

            current_level = current_map.get(dependency_id, 0)

            # Only skip a prerequisite if the user already meets
            # the target skill's required proficiency.
            if current_level >= required_level:
                continue

            # Find the shortest available learning resource.
            resource = db.execute(
                """
                SELECT *
                FROM learning_resources
                WHERE skill_id = ?
                ORDER BY hours ASC
                LIMIT 1
                """,
                (dependency_id,),
            ).fetchone()

            # A missing resource should not crash the analysis.
            if not resource:
                continue

            item = dict(resource)

            item["skill_name"] = dependency["name"]
            item["current_level"] = current_level
            item["required_level"] = required_level
            item["gap"] = max(required_level - current_level, 0)

            # FIX: Invalid or empty topics no longer crash analysis.
            item["topics"] = parse_topics(item.get("topics"))

            # Restore the user's progress for this resource.
            progress = db.execute(
                """
                SELECT completed, progress
                FROM learning_progress
                WHERE user_id = ? AND resource_id = ?
                """,
                (user_id, resource["id"]),
            ).fetchone()

            item["done"] = bool(progress["completed"]) if progress else False
            item["progress"] = progress["progress"] if progress else 0

            path.append(item)
            seen.add(dependency_id)

    return path


def career_matches(user_id):
    """Generate career recommendations from the user's skill profile."""
    db = get_db()

    rows = db.execute(
        """
        SELECT skill_id, level
        FROM user_skills
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchall()

    user_skills = {
        row["skill_id"]: row["level"]
        for row in rows
    }

    roles = []

    for role in db.execute("SELECT * FROM job_roles").fetchall():
        role_skills = db.execute(
            """
            SELECT s.name, j.required_level
            FROM job_role_skills j
            JOIN skills s ON s.id = j.skill_id
            WHERE j.job_role_id = ?
            """,
            (role["id"],),
        ).fetchall()

        skill_text = " ".join(
            f'{skill["name"]} {skill["required_level"]}'
            for skill in role_skills
        )

        roles.append(
            {
                "id": role["id"],
                "name": role["name"],
                "description": role["description"],
                "skill_text": skill_text,
            }
        )

    user_profile = []

    for skill_id, level in user_skills.items():
        row = db.execute(
            "SELECT name FROM skills WHERE id = ?",
            (skill_id,),
        ).fetchone()

        # Ignore orphaned skill references safely.
        if not row:
            continue

        user_profile.append(
            {
                "skill_id": skill_id,
                "name": row["name"],
                "level": level,
            }
        )

    return career_recommendations(user_profile, roles)
