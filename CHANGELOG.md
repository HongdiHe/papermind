# Changelog

All notable changes to PaperMind are documented here.

## [1.0.0] - 2025-09-01
### Added
- Initial release of PaperMind
- MinerU OCR SDK integration for document processing
- Support for academic papers, textbooks, and exam sheets
- Automatic LaTeX output for mathematical formulas
- Table recognition and conversion to structured Markdown
- Large Language Model integration for intelligent analysis
- Gradio-based web interface for drag-and-drop usage
- Support for processing password-protected PDFs
- Progress indicator during OCR processing
- Batch processing capabilities for multiple documents
- Configuration system with YAML-based settings
- Comprehensive logging system with file rotation

### Features
- **OCR Processing**: Convert PDFs to Markdown with high accuracy
- **Formula Recognition**: Automatic extraction and rendering of LaTeX formulas
- **Table Parsing**: Intelligent table structure recognition
- **LLM Integration**: AI-powered analysis and enhancement of extracted content
- **Error Handling**: Robust error recovery and detailed error messages
- **Timeout Management**: Configurable timeout settings for API calls
- **Retry Logic**: Automatic retry with exponential backoff (max 3 attempts)
- **Unicode Support**: Proper handling of CJK characters and international text

### Technical Details
- MinerU API Client with batch processing support
- Exponential backoff retry mechanism for API resilience
- Zip-based result handling with security path validation
- Thread-based API calls for responsive UI
- JSON export format with structured output
- Markdown rendering with MathJax support for formulas

---

For more information, visit the [PaperMind GitHub Repository](https://github.com/papermind/papermind)
