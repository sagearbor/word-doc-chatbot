# Development Environment Configuration

## Development Machine Specifications
- **Hardware**: ThinkPad with 13th Gen Intel Core i7-1355U, 32GB RAM
- **Operating System**: Windows 11 Enterprise (64-bit, x64-based processor)
- **Primary IDE**: VS Code with Git Bash terminal
- **Terminal**: Git Bash (use Unix-style commands within Windows environment)

## Environment Setup

### Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows with Git Bash)
source venv/Scripts/activate

# Deactivate when done
deactivate
```

### Package Management
```bash
# Install dependencies
pip install -r requirements.txt

# Update requirements file
pip freeze > requirements.txt

# Install specific packages
pip install package_name
```

## Deployment Architecture

### Primary Deployment: Azure Cloud
- **Platform**: Microsoft Azure
- **AI Models**: Primarily OpenAI models (GPT-4, GPT-3.5, etc.)
- **Configuration**: Use Azure OpenAI Service endpoints
- **Environment Variables**: 
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_API_VERSION`

### Alternative Deployments
- **Render.com**: Secondary deployment option
- **Other cloud providers**: AWS, GCP, Railway, Vercel, etc.
- **Local development**: Test locally before cloud deployment

### Multi-Model Support
Design applications to support multiple AI providers:
- **OpenAI**: GPT models, DALL-E, Whisper
- **Azure OpenAI**: Same models via Azure endpoints
- **Anthropic**: Claude models
- **Google**: Gemini models
- **Local models**: Ollama, HuggingFace Transformers

## Configuration Best Practices

### Environment Variables Pattern
```bash
# AI Provider Configuration
AI_PROVIDER=openai  # or azure_openai, anthropic, google, etc.
OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
ANTHROPIC_API_KEY=your_key_here

# Deployment Configuration
DEPLOYMENT_TARGET=azure  # or render, aws, local, etc.
ENVIRONMENT=development  # or staging, production
```

### Directory Structure
```
project-root/
├── .env                    # Local environment variables
├── .env.example           # Template for environment setup
├── requirements.txt       # Python dependencies
├── venv/                  # Virtual environment (Scripts/ on Windows)
├── src/                   # Source code
├── tests/                 # Test files
├── config/                # Configuration files
│   ├── azure.py          # Azure-specific config
│   ├── render.py         # Render.com config
│   └── local.py          # Local development config
├── deploy/                # Deployment scripts
│   ├── azure/            # Azure deployment files
│   ├── render/           # Render.com deployment files
│   └── docker/           # Docker configurations
└── docs/                 # Documentation
```

## Development Workflow

### Testing Commands
```bash
# Run tests
python -m pytest

# Run with coverage
python -m pytest --cov=src

# Lint code
python -m flake8 src/
python -m black src/

# Type checking
python -m mypy src/
```

### Git Workflow
```bash
# Standard Git operations in Git Bash
git add .
git commit -m "descriptive message"
git push origin main

# Create feature branch
git checkout -b feature/new-feature
```

### Local Development Server
```bash
# For Flask applications
python app.py

# For FastAPI applications
uvicorn main:app --reload

# For Streamlit applications
streamlit run app.py
```

## AI Model Integration Guidelines

### Flexible Provider Configuration
When generating code for AI integrations:
- Use factory patterns for different AI providers
- Implement fallback mechanisms between providers
- Create unified interfaces for different model APIs
- Include proper error handling and retry logic

### Example Configuration Pattern
```python
# Preferred pattern for AI provider switching
class AIProviderFactory:
    @staticmethod
    def get_provider(provider_name: str):
        if provider_name == "openai":
            return OpenAIProvider()
        elif provider_name == "azure_openai":
            return AzureOpenAIProvider()
        elif provider_name == "anthropic":
            return AnthropicProvider()
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
```

## Deployment Considerations

### Azure-Specific Requirements
- Use Azure Key Vault for sensitive configuration
- Implement Azure App Service deployment
- Configure Azure Application Insights for monitoring
- Use Azure Container Registry for Docker images

### Multi-Cloud Compatibility
- Use environment-agnostic configuration
- Implement health check endpoints
- Create Docker containers for consistent deployment
- Use Infrastructure as Code (Terraform/ARM templates)

## Notes for AI Agents

### Code Generation Preferences
- **Terminal**: Always generate Git Bash compatible commands
- **Paths**: Use forward slashes `/` in Git Bash, but remember Windows paths use backslashes in some contexts
- **Environment**: Assume Windows development with Linux-style deployment
- **Dependencies**: Include both development and production requirements
- **Documentation**: Generate clear setup instructions for both local development and cloud deployment

### Common Patterns to Follow
- Environment variable configuration over hardcoded values
- Graceful degradation when services are unavailable
- Comprehensive logging for debugging
- Security best practices (no secrets in code)
- Cross-platform compatibility where possible
### File Restrictions
- Do not commit binary files (images, videos, .docx, .doc, .pdf, .exe).
