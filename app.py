import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from balldontlie import BalldontlieAPI
from balldontlie.exceptions import (
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError,
    BallDontLieException
)


def create_app():
    """Application factory function"""
    load_dotenv()
    app = Flask(__name__)

    @app.route('/test-sports', methods=['GET'])
    def test_sports():
        api_key = os.environ.get('BALLDONTLIE_API_KEY')
        if not api_key:
            return jsonify({"error": "No API key"}), 500

        api = BalldontlieAPI(api_key=api_key)
        results = {}

        for league in ('nba', 'mlb', 'nfl'):
            try:
                teams = getattr(getattr(api, league), 'teams').list()
                results[league] = "Working"
            except Exception as e:
                results[league] = f"Failed: {str(e)}"

        return jsonify(results), 200

    @app.route('/test-config', methods=['GET'])
    def test_config():
        api_key = os.environ.get('BALLDONTLIE_API_KEY')
        if api_key:
            return jsonify({
                "api_key_loaded": True,
                "api_key_length": len(api_key),
                "api_key_first_6": api_key[:6],
                "api_key_last_4": api_key[-4:]
            }), 200
        else:
            return jsonify({"api_key_loaded": False}), 200

    @app.route('/team/<int:team_id>/performance', methods=['GET'])
    def get_team_performance(team_id):
        season = request.args.get('season')
        if not season:
            return jsonify({"error": "Season parameter is required"}), 400

        api_key = os.environ.get('BALLDONTLIE_API_KEY')
        if not api_key:
            return jsonify({"error": "API key not configured"}), 502

        try:
            api = BalldontlieAPI(api_key=api_key)

            # Use .get(...) to fetch standings for a season
            standings_response = api.mlb.standings.get(season=int(season))

            # Extract the list of MLBStandings model objects
            standings_data = (
                standings_response.data
                if hasattr(standings_response, 'data')
                else standings_response
            )

            # Find the matching team
            for standing in standings_data:
                # standing is an MLBStandings model; access attributes directly
                if standing.team.id == team_id:
                    return jsonify({
                        "team_id": standing.team.id,
                        "team_name": standing.team.display_name,
                        "wins": standing.wins or 0,
                        "losses": standing.losses or 0,
                        "win_percentage": standing.win_percent or 0.0
                    }), 200

            return jsonify({"error": "Team not found for season"}), 404

        except AuthenticationError:
            return jsonify({"error": "Invalid API key"}), 502
        except RateLimitError:
            return jsonify({"error": "Rate limit exceeded"}), 502
        except ValidationError:
            return jsonify({"error": "Invalid request parameters"}), 400
        except NotFoundError:
            return jsonify({"error": "Resource not found"}), 404
        except ServerError:
            return jsonify({"error": "External API server error"}), 502
        except BallDontLieException:
            return jsonify({"error": "External API request failed"}), 502
        except Exception as e:
            # Log the exception internally if you like, then:
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='localhost', port=5001, debug=True)
