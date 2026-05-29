# Tools, Integrations & Resources

> Source: https://docs.crewai.com/llms.txt

## Built-in Tools (40+)

### Search & Research
- `SerperDevTool` - Google search via Serper.dev
- `TavilySearchTool` / `TavilyResearchTool` - Comprehensive web search
- `ExaSearchTool` - Fast web search API
- `BraveSearchTool` - Brave Search API suite
- `You.com Search & Research` - Web search + AI research
- `ArxivPaperTool` - Academic paper search
- `GitHubSearchTool` - Code repository search
- `LinkupSearchTool` - Contextual information API

### Web Scraping
- `FirecrawlCrawlWebsiteTool` / `FirecrawlScrapeWebsiteTool`
- `ScrapeWebsiteTool` / `ScrapeElementFromWebsiteTool`
- `SeleniumScrapingTool` - Browser-based scraping
- `BrowserbaseLoadTool` - Headless browser management
- `SpiderTool`, `ScrapflyScrapeTool`, `StagehandTool`
- `Bright Data Tools` - SERP, Web Unlocker, Dataset API
- `OxylabsScrapers` - Amazon, Google search scrapers

### File & Document Processing
- `FileReadTool` / `FileWriteTool` / `DirectoryReadTool`
- RAG tools: `PDFSearchTool`, `CSVSearchTool`, `DOCXSearchTool`, `JSONSearchTool`, `TXTSearchTool`, `XMLSearchTool`, `MDXSearchTool`
- `OCRTool` - Text extraction from images
- `PDFTextWritingTool` - Write text to PDFs

### AI & Machine Learning
- `VisionTool` - Extract text from images
- `DallETool` - Image generation
- `RagTool` - Retrieval-Augmented Generation
- `CodeInterpreterTool` - Secure Python execution
- `AIMindTool` - Natural language data querying
- E2B Sandbox Tools - Isolated code execution
- Daytona Sandbox Tools - Shell/Python in sandboxes

### Database & Data
- `PGSearchTool` (PostgreSQL), `MySQLSearchTool`
- `MongoDBVectorSearchTool`, `QdrantVectorSearchTool`, `WeaviateVectorSearchTool`
- `SingleStoreSearchTool`, `SnowflakeSearchTool`
- `NL2SQLTool` - Natural language to SQL
- `DatabricksQueryTool`

### Cloud Storage
- `S3ReaderTool`, `S3WriterTool`
- `BedrockKnowledgeBaseRetriever`

### Automation & Integration
- `ComposioTool` - 250+ integrations with auth management
- `ApifyActorsTool` - Web scraping/crawling platform
- `ZapierActionsAdapter` - Zapier actions
- `MultiOnTool` - Web navigation via natural language

### Enterprise Integrations
- Slack, Gmail, Google Calendar, Google Drive, Google Docs, Google Sheets
- Microsoft Teams, Outlook, OneDrive, SharePoint, Excel, Word
- Salesforce, HubSpot, Zendesk, Jira, Linear, Notion, Asana
- GitHub, Shopify, Stripe, Box, ClickUp
- Bedrock Invoke Agent, CrewAI Run Automation, Merge Agent Handler

## MCP (Model Context Protocol) Support
- Connect MCP servers as tools
- Multiple transport options: Stdio, SSE, Streamable HTTP
- DSL syntax for simple integration
- Multi-server aggregation

## Observability Integrations (15+)
- Datadog, Langfuse, MLflow, Weave (W&B)
- Arize Phoenix, Braintrust, Galileo
- LangDB, Langtrace, Maxim, Neatlogs
- OpenLIT, Opik, Patronus AI, Portkey
- TrueFoundry

## Official Resources
- **Docs**: https://docs.crewai.com/
- **GitHub**: https://github.com/crewAIInc/crewAI
- **Community**: https://community.crewai.com
- **Examples**: https://github.com/crewAIInc/crewAI-examples
- **Cookbooks**: Feature-focused quickstarts and notebooks
- **Skills**: `npx skills add crewaiinc/skills` for IDE agents

## Key Example Flows
1. **Email Auto Responder** - Infinite loop background automation
2. **Lead Score Flow** - HITL feedback + conditional routing
3. **Write a Book Flow** - Chaining multiple crews
4. **Meeting Assistant Flow** - Broadcast event → multiple actions
