Model nodes in the Patra Knowledge Graph contain location URLs that may become invalid over time (broken links, moved resources, etc.). Create a script that iterates through all Model nodes, extracts their location URLs, validates them, and updates the model card status field based on URL validity.

## Script Specification

### Input
- Neo4j database connection
- Optional: Specific model IDs to validate
- Optional: Timeout settings for URL checks

### Output
- Console summary of findings
- Update model card boolean field: `is_orphan` (true for invalid URLs, false for valid URLs)

### Model Card Boolean Field
The script will update an `is_orphan` boolean field on ModelCard nodes:
- **`false`**: URL is valid and accessible
- **`true`**: URL is invalid, broken, or inaccessible

Example console output:
```
Validating model URLs...
✅ model-001: VALID (https://example.com/model)
❌ model-002: ORPHAN (https://broken-url.com/model) - 404 Not Found
❌ model-003: ORPHAN (invalid-url) - Invalid URL format
Summary: 1 valid, 2 orphan models
```

## Implementation

### Database Layer
1. **Add method to get all models with locations** in `ingester/database.py`
   ```python
   def get_all_models_with_locations(self):
       # Query all Model nodes with location field
   ```

2. **Add method to update model card orphan status** in `ingester/database.py`
   ```python
   def update_model_card_orphan_status(self, model_id, is_orphan):
       # Update ModelCard is_orphan boolean field
   ```

### URL Validation Script
3. **Create validation script** in `scripts/validate_urls.py`
   - Simple URL validation with timeout
   - Console output with progress
   - Update model card is_orphan field

## Features
- URL format and connectivity validation
- Console output with progress
- Update model card is_orphan boolean field
- Simple timeout handling

## Acceptance Criteria
- [ ] Script retrieves all Model nodes with location URLs
- [ ] Validates URL format and accessibility
- [ ] Updates model card is_orphan boolean field
- [ ] Provides console output with progress
- [ ] Handles basic error cases
