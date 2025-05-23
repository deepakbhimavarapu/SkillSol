import json, os
import logging
from flask import Flask, jsonify, request

def create_app():
    app = Flask(__name__)

    # Production configuration
    app.config.update(
        DEBUG=False,
        ENV='production'
    )

    # Set up logging if not in debug mode
    if not app.debug:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)

    # Load synthetic data from JSON file
    try:
        with open('synthetic_data.json', 'r') as f:
            data = json.load(f)
    except Exception as e:
        app.logger.error("Error loading synthetic_data.json: %s", e)
        data = {
            "organizations": [],
            "teams": [],
            "roles": [],
            "individuals": [],
            "skills": [],
            "benchmarks": {}
        }

    # Extract entities
    organizations = data.get('organizations', [])
    teams = data.get('teams', [])
    roles = data.get('roles', [])
    individuals = data.get('individuals', [])
    skills = data.get('skills', [])
    benchmarks = data.get('benchmarks', {})

    # Endpoint for all organizations
    @app.route('/organizations', methods=['GET'])
    def get_organizations():
        return jsonify(organizations)

    # Endpoint for a specific organization by ID
    @app.route('/organizations/<org_id>', methods=['GET'])
    def get_organization(org_id):
        org = next((o for o in organizations if o['id'] == org_id), None)
        return jsonify(org) if org else ('Organization not found', 404)

    # Endpoint for all teams, with optional filtering by organization_id
    @app.route('/teams', methods=['GET'])
    def get_teams():
        org_id = request.args.get('organization_id')
        if org_id:
            filtered_teams = [t for t in teams if t['organization_id'] == org_id]
            return jsonify(filtered_teams)
        return jsonify(teams)

    # Endpoint for a specific team by ID
    @app.route('/teams/<team_id>', methods=['GET'])
    def get_team(team_id):
        team = next((t for t in teams if t['id'] == team_id), None)
        return jsonify(team) if team else ('Team not found', 404)

    # Endpoint for all roles, with optional filtering by team_id
    @app.route('/roles', methods=['GET'])
    def get_roles():
        team_id = request.args.get('team_id')
        if team_id:
            filtered_roles = [r for r in roles if r['team_id'] == team_id]
            return jsonify(filtered_roles)
        return jsonify(roles)

    # Endpoint for a specific role by ID
    @app.route('/roles/<role_id>', methods=['GET'])
    def get_role(role_id):
        role = next((r for r in roles if r['id'] == role_id), None)
        return jsonify(role) if role else ('Role not found', 404)

    # Endpoint for all individuals, with optional filtering by team_id or role_id
    @app.route('/individuals', methods=['GET'])
    def get_individuals():
        team_id = request.args.get('team_id')
        role_id = request.args.get('role_id')
        if team_id:
            filtered_individuals = [i for i in individuals if i['team_id'] == team_id]
        elif role_id:
            filtered_individuals = [i for i in individuals if i['role_id'] == role_id]
        else:
            filtered_individuals = individuals
        return jsonify(filtered_individuals)

    # Endpoint for a specific individual by ID
    @app.route('/individuals/<ind_id>', methods=['GET'])
    def get_individual(ind_id):
        ind = next((i for i in individuals if i['id'] == ind_id), None)
        return jsonify(ind) if ind else ('Individual not found', 404)

    # Endpoint for all skills
    @app.route('/skills', methods=['GET'])
    def get_skills():
        return jsonify(skills)

    # Endpoint for benchmarks by industry
    @app.route('/benchmarks', methods=['GET'])
    def get_benchmarks():
        industry = request.args.get('industry')
        if industry:
            return jsonify(benchmarks.get(industry, []))
        return jsonify(benchmarks)
    
    @app.route('/skillgap', methods=['GET'])
    def get_skill_gap():
        org_id = request.args.get('org_id')
        if not org_id:
            return jsonify({"error": "org_id parameter is required"}), 400

        # Find the organization with the given ID
        org = next((o for o in organizations if o['id'] == org_id), None)
        if not org:
            return jsonify({"error": "Organization not found"}), 404

        # Ensure the organization has an industry field
        if 'industry' not in org:
            return jsonify({"error": "Organization does not have an industry field"}), 400

        org_industry = org['industry']

        # Get all teams for the organization
        org_teams = [t for t in teams if t['organization_id'] == org_id]
        expected_skills_set = set()

        # For each team, accumulate expected skills from all roles
        for team in org_teams:
            team_roles = [r for r in roles if r['team_id'] == team['id']]
            for role in team_roles:
                # Expecting each role to have an "expected_skills" field (list of skill IDs)
                role_skills = role.get('expected_skills', [])
                expected_skills_set.update(role_skills)

        # Get benchmark skills for the organization's industry
        benchmark_skills = benchmarks.get(org_industry, [])
        benchmark_skills_set = set(benchmark_skills)

        # Calculate the gap: skills expected but missing from the benchmark
        gap_skill_ids = benchmark_skills_set - expected_skills_set

        # Retrieve the skill objects for each missing skill
        gap_skills = [s for s in skills if s['id'] in gap_skill_ids]

        return jsonify(gap_skills)

    return app

# Create the app using the factory
app = create_app()

# This block is only used for debugging or local testing.
# In production, run the app with a WSGI server like Gunicorn or uWSGI.
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
