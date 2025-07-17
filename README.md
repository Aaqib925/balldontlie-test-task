# MLB Team Performance API

A simple Flask REST API to fetch MLB team performance data via the balldontlie API.

## Setup

1. **Clone repository**

2. **Install dependencies**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

3. **Configure API key**

   * Copy `.env.example` to `.env`
   * Set your API key:

     ```bash
     BALLDONTLIE_API_KEY=<your_api_key_here>
     ```

## Running the Server

Start the API server:

```bash
python app.py
```

By default, it runs at `http://localhost:5001`.

## API Endpoint

**GET** `/team/<team_id>/performance?season=<year>`

* `team_id` (integer): MLB team ID
* `season` (integer): Four-digit year (e.g., 2023)

### Example

```bash
curl "http://localhost:5001/team/26/performance?season=2023"
```

**Sample Response**

```json
{
  "team_id": 26,
  "team_name": "St. Louis Cardinals",
  "wins": 71,
  "losses": 91,
  "win_percentage": 0.4382716
}
```
