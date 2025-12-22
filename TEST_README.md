# Test Instructions - Phase 1

This phase verifies the connection to the InRiver API.

## Prequisites
- Ensure `.env` file exists with `IN_RIVER_BASE_URL` and `ECOM_INRIVER_API_KEY`.
- Install dependencies (if not already installed):
  ```bash
  pip install -r requirements.txt
  ```

## Running the Test
Run the test script from the root directory:

```bash
python test_inriver.py
```

## Expected Output
You should see:
1. "Loading configuration..."
2. "Initializing InRiverClient..."
3. "Fetching total product count..." -> Total Products found: [NUMBER]
4. "Fetching first 5 products..." -> Retrieved 5 products
5. List of 5 products with IDs and Image URLs.
