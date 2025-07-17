import os
import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from balldontlie import BalldontlieAPI
from balldontlie.exceptions import (
    AuthenticationError,
    RateLimitError,
    ValidationError as BoValidationError,
    NotFoundError,
    ServerError,
    BallDontLieException
)
from pydantic import ValidationError as PydanticValidationError


def create_app():
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

            # Attempt SDK call, fallback to raw HTTP if it fails
            try:
                standings_response = api.mlb.standings.get(season=int(season))
                standings_data = (
                    standings_response.data
                    if hasattr(standings_response, 'data')
                    else standings_response
                )
            except (AttributeError, PydanticValidationError):
                url = "https://api.balldontlie.io/mlb/v1/standings"
                resp = requests.get(
                    url,
                    params={"season": int(season)},
                    headers={"Authorization": api_key}
                )
                if resp.status_code != 200:
                    return jsonify({"error": f"Raw API request failed ({resp.status_code})"}), 502
                raw = resp.json()
                standings_data = raw.get("data", raw)

            # Normalize each entry to (tid, name, wins, losses, win_pct)
            for entry in standings_data:
                if isinstance(entry, dict):
                    team_info = entry.get('team', {})
                    tid = team_info.get('id')
                    name = team_info.get('display_name') or team_info.get('full_name', '')
                    wins = entry.get('wins', 0)
                    losses = entry.get('losses', 0)
                    win_pct = (
                        entry.get('win_percent')
                        or entry.get('win_percentage')
                        or 0.0
                    )
                else:
                    # entry is a model object
                    team_info = entry.team
                    tid = team_info.id
                    name = team_info.display_name or getattr(team_info, 'full_name', '')
                    wins = entry.wins or 0
                    losses = entry.losses or 0
                    win_pct = entry.win_percent or 0.0

                if tid == team_id:
                    return jsonify({
                        "team_id": tid,
                        "team_name": name,
                        "wins": wins,
                        "losses": losses,
                        "win_percentage": win_pct
                    }), 200

            return jsonify({"error": "Team not found for season"}), 404

        except AuthenticationError:
            return jsonify({"error": "Invalid API key"}), 502
        except RateLimitError:
            return jsonify({"error": "Rate limit exceeded"}), 502
        except BoValidationError:
            return jsonify({"error": "Invalid request parameters"}), 400
        except NotFoundError:
            return jsonify({"error": "Resource not found"}), 404
        except ServerError:
            return jsonify({"error": "External API server error"}), 502
        except BallDontLieException:
            return jsonify({"error": "External API request failed"}), 502
        except Exception as e:
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='localhost', port=5001, debug=True)
