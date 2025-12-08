Here is a professional, English-language README.md file tailored for your GitHub repository. It incorporates the architecture, specific constraints (like the "visualization is mandatory" rule), and the switch to DuckDB as discussed.🏦 Banking Analytics AI AssistantA Stateful Multi-Agent System for Text-to-SQL & Data Visualization📖 OverviewThis project is an AI-powered banking assistant that converts natural language questions into executable SQL queries and automatically generates data visualizations. It is built using LangGraph for stateful multi-agent orchestration and uses DuckDB as a high-performance, embedded OLAP engine .The system is designed with a "Self-Healing" architecture: if a generated SQL query fails, the system analyzes the error and retries automatically (up to 3 attempts) before falling back .🏗️ ArchitectureThe system enforces a strict pipeline: "If there is SQL, there must be a visualization." .Kod snippet'iflowchart TD
    Start([👤 User Question]) --> Planner
    
    subgraph "Core Backend (LangGraph)"
        Planner[🧠 Planner Agent\n(Role & Schema Selection)]
        SQLGen[⚙️ SQL Generator\n(DuckDB Syntax)]
        DBExec[🗄️ DB Executor\n(DuckDB Read-Only)]
        Fixer[🔧 SQL Error Fixer\n(Retry Loop < 3)]
    end
    
    subgraph "UI & Presentation"
        VisAgent[📊 Visualization Agent\n(Matplotlib/Plotly)]
        Streamlit[🖥️ Streamlit UI]
    end

    Planner --> SQLGen
    SQLGen --> DBExec
    DBExec -- "Error" --> Fixer
    Fixer -- "Revised SQL" --> SQLGen
    DBExec -- "Success" --> VisAgent
    VisAgent --> Streamlit
✨ Key FeaturesRole-Based Access Control (RBAC):The Planner Node filters data access based on user roles (e.g., A Branch Manager sees only their branch, while C-Level sees aggregated KPIs) .Resilient Text-to-SQL:Generates DuckDB-compatible SQL (using LIMIT instead of ROWNUM, standard ANSI joins) .Includes a Router Agent loop that fixes syntax errors (e.g., correcting non-existent column names) automatically .Mandatory Visualization:Every successful query triggers the Visualization Agent, which deterministically selects the best chart type (Line, Bar, etc.) based on the data shape .Secure & Auditable:Database connections are strictly Read-Only .Full logging of "Question -> SQL -> Table Access" for governance .🛠️ Tech StackComponentTechnologyDescriptionOrchestrationLangGraphManages agent state, routing, and error loops .DatabaseDuckDBFast, embedded analytical database (replacing Oracle for this phase) .LLMWatsonx.ai / OpenAIPowers the planner, SQL generation, and error fixing .FrontendStreamlitChat interface, SQL preview, and interactive charts .VisualizationMatplotlibPython code generation for rendering static charts .🚀 Installation & SetupPrerequisitesPython 3.9+GitStepsClone the RepositoryBashgit clone https://github.com/your-org/banking-analytics-agent.git
cd banking-analytics-agent
Create Virtual EnvironmentBashpython -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
Install DependenciesBashpip install -r requirements.txt
Run the ApplicationBashstreamlit run app.py
📂 Project StructureBash├── data/
│   └── bank_data.duckdb       # Local DuckDB instance
├── src/
│   ├── agents/
│   │   ├── planner.py         # Role-based planning logic 
│   │   ├── sql_generator.py   # Text-to-SQL logic 
│   │   ├── executor.py        # DuckDB connection handler 
│   │   └── visualizer.py      # Matplotlib code generator 
│   ├── graph/
│   │   ├── state.py           # TypedDict state definition
│   │   └── workflow.py        # LangGraph node/edge setup
│   └── utils/
│       └── security.py        # Masking & Role definitions 
├── app.py                     # Streamlit entry point
└── README.md
🧪 Usage Scenarios1. Business Analyst (Campaign Analysis)Prompt: "What is the difference in credit volume between the campaign period and the pre-campaign period? Show monthly."Process: Planner identifies the campaign tables -> SQL Generator creates a time-based comparison -> Visualizer draws a Line Chart showing the lift .2. Branch Manager (Regional Performance)Prompt: "Show me the credit volume for branches in the Marmara region for the last 3 months."Process: Planner applies a "Marmara" filter -> DB Executor runs the query -> Visualizer draws a Bar Chart ranking branches .👥 Contributors & ResponsibilitiesOrchestration Lead: Responsible for LangGraph architecture, state management, and the retry logic .Text2SQL Architect: Responsible for LLM prompts, DuckDB syntax compliance, and the semantic layer .Frontend & Vis Lead: Responsible for the Streamlit UI and ensuring chart generation safety .🗺️ Roadmap[x] Phase 1: Open Source MVP with DuckDB and Local LLMs .[ ] Phase 2: Integration of "Impact Analysis Agent" and RAG architecture.[ ] Phase 3: Advanced Governance & Audit Logging .
