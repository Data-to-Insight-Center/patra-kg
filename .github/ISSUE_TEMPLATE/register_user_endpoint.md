# Add `/register_user` endpoint

## Problem
Users need to register themselves with the Patra Knowledge Base to participate in experiments and track their model submissions, but there's no public API endpoint for user registration.

## Solution
Add a POST `/register_user` endpoint that allows users to register and returns a unique `user_id` for future experiment and model submissions.

## Current State
- ✅ User constraint exists in Neo4j (`user_id_unique`)
- ✅ User relationships exist (`SUBMITTED_BY` relationship with experiments)
- ✅ User references in deployment queries
- ❌ No public API endpoint for user registration
- ❌ No user existence check method

## API Specification

### Request
```http
POST /register_user
Content-Type: application/json
```

```json
{
  "user_id": "string (required)",
  "email": "string (optional)",
  "full_name": "string (optional)",
  "organization": "string (optional)",
  "department": "string (optional)",
  "location": "string (optional)",
  "orcid": "string (optional)"
}
```

### Response
**Success (201)**
```json
{
  "message": "User registered successfully"
}
```

**Error (400)**
```json
{
  "error": "user_id is required"
}
```

**Error (409)**
```json
{
  "error": "User with this ID already exists"
}
```

## Execution Plan

### Phase 1: Database Layer
1. **Add user existence check** in `ingester/database.py`
   ```python
   def check_user_exists(self, user_id):
       # Query Neo4j to check if User with user_id exists
   ```

2. **Add user insertion method** in `ingester/database.py`
   ```python
   def insert_user(self, user):
       # Insert user information into the graph
   ```

3. **Add methods to neo4j_ingester.py**
   ```python
   def check_user_exists(self, user_id):
       return self.db.check_user_exists(user_id)
   
   def add_user(self, user):
       self.db.insert_user(user)
   ```

### Phase 2: API Endpoint
4. **Add endpoint to server.py**
   ```python
   @api.route('/register_user')
   class RegisterUser(Resource):
       def post(self):
           # Validate user_id is required
           # Check for duplicate user_id
           # Register user
           # Return success response
   ```

### Phase 3: Validation & Error Handling
5. **Input validation**
   - Required fields: `user_id`
   - Email validation: `email` format if provided
   - ORCID validation: `orcid` format if provided (XXXX-XXXX-XXXX-XXXX)

6. **Error handling**
   - 400: Missing `user_id` or invalid data
   - 409: User already exists
   - 500: Database errors

### Phase 4: Documentation
7. **Update API docs**
   - Add to `docs/patra_openapi.json`
   - Update README.md endpoint table

### Phase 5: Testing
8. **Unit tests**
   - Test validation logic
   - Test database operations
   - Test error scenarios

9. **Integration tests**
   - Test full endpoint flow
   - Test with existing experiment data

## Acceptance Criteria
- [ ] POST `/register_user` accepts valid user data
- [ ] Returns success message on successful registration (201)
- [ ] Validates `user_id` is required (400)
- [ ] Returns 409 for duplicate `user_id`
- [ ] Integrates with existing experiment tracking
- [ ] Includes comprehensive tests
- [ ] Documentation updated

## Labels
- `enhancement`
- `api`
- `user-management`
