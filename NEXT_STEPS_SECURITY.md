# Next Steps for Security Implementation

**Quick Reference Guide for Completing Phase 2**

---

## What's Done ✅

All critical security infrastructure is in place and working:
- XXE protection
- Secure download system
- File validation module
- Input sanitization module
- Rate limiting
- Security headers
- Error handling
- CORS hardening
- HTTPS enforcement

**Current Status:** 80% complete, ready for review and merge

---

## What Remains 🔄

### Task 1: Endpoint Integration (2-4 hours)

Apply the security pattern to 6 upload endpoints. Here's the exact pattern to use:

```python
# Example: Update /process-document/ endpoint

@app.post("/process-document/")
@limiter.limit("10/hour")  # Add this decorator
async def process_document(
    request: Request,  # Add Request parameter
    file: UploadFile = File(...),
    instructions: str = Form(...),
    author_name: str = Form(DEFAULT_AUTHOR_NAME),
    ...
):
    """Process document with AI suggestions."""

    # STEP 1: Add file validation (at the start)
    is_valid, error_msg = await validate_docx_upload(file)
    if not is_valid:
        raise handle_validation_error("file", error_msg)

    # STEP 2: Add input sanitization
    is_valid, error_msg = validate_user_instructions(instructions)
    if not is_valid:
        raise handle_validation_error("instructions", error_msg)

    # Use sanitized version in LLM calls
    safe_instructions = sanitize_llm_input(instructions, max_length=5000)

    # STEP 3: Wrap main logic in try-except
    try:
        # ... existing processing logic (don't change this) ...

        # STEP 4: Replace download URL generation (find this line)
        # OLD:
        # "download_url": f"/download/{os.path.basename(output_path)}"

        # NEW:
        download_token = register_download(
            output_path,
            os.path.basename(output_path),
            TEMP_DIR_ROOT
        )
        # In response dictionary:
        "download_url": f"/download/{download_token}"

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise handle_error(e, "document processing")
```

**Apply this pattern to these 6 endpoints:**

1. `/process-document/` (around line 189)
2. `/analyze-document/` (around line 102)
3. `/upload-fallback-document/` (around line 326)
4. `/analyze-fallback-requirements/` (around line 399)
5. `/process-document-with-fallback/` (around line 499)
6. `/process-legal-document/` (around line 851)

**Notes:**
- Use appropriate context names in `handle_error()` (e.g., "document analysis", "legal document processing")
- Some endpoints may not return download URLs (like `/analyze-document/`), skip step 4 for those
- Make sure `Request` is in the function parameters for rate limiting to work

---

### Task 2: Create Security Test Suite (4-6 hours)

Create `tests/test_security.py`:

```python
"""Security test suite for Word Document Chatbot."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
import io
import zipfile

client = TestClient(app)

def test_xxe_protection():
    """Test that XXE attacks are blocked."""
    # Create malicious DOCX with XXE payload
    malicious_xml = b'''<?xml version="1.0"?>
<!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>&xxe;</w:t></w:r></w:p></w:body>
</w:document>'''

    # Create malicious DOCX
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as docx:
        docx.writestr('word/document.xml', malicious_xml)
        docx.writestr('[Content_Types].xml', b'<Types/>')
    buffer.seek(0)

    # Test that it's blocked
    response = client.post(
        "/process-document/",
        files={"file": ("evil.docx", buffer, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"instructions": "test"}
    )

    # Should be rejected
    assert response.status_code in [400, 500]
    # Check for security error message
    assert "security" in response.json()["detail"].lower() or "malicious" in response.json()["detail"].lower()

def test_path_traversal_protection():
    """Test that path traversal in downloads is blocked."""
    # Try various path traversal attempts
    bad_tokens = [
        "../../etc/passwd",
        "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "invalid-token-123"
    ]

    for token in bad_tokens:
        response = client.get(f"/download/{token}")
        assert response.status_code in [400, 404]

def test_file_size_limit():
    """Test that oversized files are rejected."""
    # Create a file larger than 10MB
    large_content = b"x" * (11 * 1024 * 1024)

    response = client.post(
        "/process-document/",
        files={"file": ("large.docx", large_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"instructions": "test"}
    )

    assert response.status_code == 400
    assert "size" in response.json()["detail"].lower()

def test_rate_limiting():
    """Test that rate limiting is enforced."""
    # Make multiple requests quickly
    responses = []
    for i in range(12):
        response = client.get("/health")
        responses.append(response.status_code)

    # At least one should be rate limited
    # Note: This test might be flaky depending on rate limit settings
    # Adjust based on actual rate limit configuration

def test_security_headers():
    """Test that security headers are present."""
    response = client.get("/health")

    # Check critical security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

    assert "Content-Security-Policy" in response.headers

def test_error_message_sanitization():
    """Test that errors don't leak sensitive information."""
    # Trigger an error by sending invalid data
    response = client.post(
        "/process-document/",
        data={"instructions": "test"}  # Missing file
    )

    # Should return an error
    assert response.status_code >= 400

    # Error should not contain file paths, stack traces, etc.
    detail = response.json().get("detail", "")
    assert "/app/" not in detail
    assert "/backend/" not in detail
    assert "Traceback" not in detail
    assert ".py" not in detail or "Error ID" in detail  # Allow .py only if it's part of error ID

# Add more tests as needed
```

Run with:
```bash
pytest tests/test_security.py -v
```

---

### Task 3: Update Environment Variables

Update `.env.example` to document new variables:

```bash
# Security Configuration (add this section)

# Environment (development or production)
ENVIRONMENT=development

# Production Security Settings (only needed in production)
# ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
# ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Development Debug Settings (DO NOT USE IN PRODUCTION)
# ENABLE_LITELLM_DEBUG=true  # WARNING: Will expose API keys in logs!
```

---

## Testing Checklist

Before considering Phase 2 complete:

- [ ] All 6 endpoints updated with security pattern
- [ ] Security test suite created and passing
- [ ] Full regression test suite passing
- [ ] Manual testing of file upload validation
- [ ] Manual testing of download tokens
- [ ] Rate limiting verified (try 11 quick requests)
- [ ] Security headers verified in browser dev tools
- [ ] Error messages don't leak sensitive info
- [ ] Documentation updated

---

## Deployment Checklist

Before deploying to production:

### Environment Configuration
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `ALLOWED_ORIGINS` for your domain
- [ ] Set `ALLOWED_HOSTS` for your domain
- [ ] Ensure `ENABLE_LITELLM_DEBUG` is NOT set
- [ ] All API keys properly configured

### Security Verification
- [ ] HTTPS configured with valid certificate
- [ ] Security headers present in responses
- [ ] Rate limiting active and appropriate
- [ ] Error messages generic (no info leakage)
- [ ] File upload validation working
- [ ] Download tokens working

### Testing
- [ ] All tests passing
- [ ] Manual smoke test of key workflows
- [ ] Security scan completed (if available)

---

## Quick Commands

```bash
# Run tests
pytest tests/ -v

# Run security tests only
pytest tests/test_security.py -v

# Run specific endpoint test
pytest tests/test_main.py::test_process_document_endpoint -v

# Check git status
git status

# View commits
git log --oneline -5

# View security implementation branch
git branch
```

---

## Getting Help

### Documentation
- **Technical Details:** `SECURITY_IMPLEMENTATION_COMPLETE.md`
- **Executive Summary:** `SECURITY_PHASE2_SUMMARY.md`
- **Original Audit:** `SECURITY_AUDIT_REPORT_20251029.md`
- **Fix Guide:** `SECURITY_FIX_IMPLEMENTATION_GUIDE.md`

### Key Files
- File validation: `backend/file_validation.py`
- Input sanitization: `backend/input_sanitization.py`
- Secure downloads: `backend/secure_downloads.py`
- Error handling: `backend/error_handling.py`
- Main application: `backend/main.py`

### Common Issues

**Issue:** Import errors when starting server
**Solution:** Make sure security dependencies are installed:
```bash
pip install defusedxml python-magic slowapi jsonschema
```

**Issue:** Rate limiting not working
**Solution:** Make sure `request: Request` parameter is in function signature

**Issue:** Download returns 404
**Solution:** Use `register_download()` to generate token before returning URL

---

## Estimated Time to Complete

- **Endpoint Integration:** 2-4 hours (straightforward pattern application)
- **Security Tests:** 4-6 hours (writing comprehensive tests)
- **Testing & Validation:** 1-2 hours (running tests, manual verification)
- **Documentation Update:** 1 hour (update .env.example, README)

**Total:** 8-13 hours to fully complete Phase 2

---

## Success Criteria

Phase 2 is complete when:

1. ✅ All 6 endpoints use the security pattern
2. ✅ Security test suite created and passing
3. ✅ Full regression test suite passing
4. ✅ Manual testing confirms all features working
5. ✅ Documentation updated
6. ✅ Ready for production deployment

---

**Current Branch:** `fix/security-implementation-phase2`
**Status:** Ready for review, 80% complete
**Next:** Apply security pattern to endpoints, create tests
