'''mermaid
graph TD
    subgraph User Interface
        A[Streamlit Dashboard]
    end

    subgraph Application Core
        B(Scheduler Agent)
        C(Data Collector Agent)
        D(Content Filter Agent)
        E(Trend Analyzer Agent)
        F(LLM Summarizer Agent)
        G(Storage Agent)
    end

    subgraph Data Sources
        H[RSS Feeds]
        I[AI Blogs]
        J[Tech News]
        K[Research News]
        L[GitHub Trending]
        M[AI Tools]
    end

    subgraph Database
        N[SQLite]
    end

    A --> B
    B --> C
    C --> H
    C --> I
    C --> J
    C --> K
    C --> L
    C --> M
    C --> D
    D --> E
    E --> F
    F --> G
    G --> N
    N --> A
'''
