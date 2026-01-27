# Backend Integration Plan

## Overview
The Alpha Bot backend consists of two primary components working in tandem to provide real-time financial insights and natural language interaction.

## Components

### 1. 🐍 Python Data Engine
**Role:** Data Aggregation & Analysis
**Responsibilities:**
- Scraping financial data (prices, metrics, news)
- Performing stock analysis
- Providing raw data for charts and visualizations
- Likely source of truth for "My Positions" and "Market Feed" data

### 2. 🤖 Kimi LLM Agent
**Role:** User Interaction & Synthesis
**Responsibilities:**
- Processing natural language queries from the text chat
- Synthesizing "up-to-date information" (News + Data)
- Delivering "informed insights" based on the Python engine's data
- Maintaining conversation context

## Integration Questions (To Be Determined)
- **API Interface:** How does the React frontend communicate with these services? (FastAPI, Flask, etc?)
- **Data Flow:** Does Kimi invoke the Python script? Or does the frontend query both separately?
- **Authentication:** How are API keys managed?
- **Real-time:** Will we use WebSockets for live ticker updates?
