import os
from dotenv import load_dotenv
from openai import OpenAI
from bs4 import BeautifulSoup

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini") # Default to a cost-effective model

def get_llm_client():
    if LLM_PROVIDER == "openrouter":
        if not OPENROUTER_API_KEY:
            print("⚠️ OPENROUTER_API_KEY not set")
            return None
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
    else: # Default to openai
        if not OPENAI_API_KEY:
            print("⚠️ OPENAI_API_KEY not set")
            return None
        return OpenAI(api_key=OPENAI_API_KEY)

client = get_llm_client()

def summarize_insights(query: str, insights: list, max_tokens: int = 5000):
    if not (OPENAI_API_KEY or OPENROUTER_API_KEY):
        print("⚠️ LLM API key not set. Skipping summarization.")
        return {
            "text": "LLM summarization skipped: API key not configured.",
            "bullets": [],
            "recommendations": [],
            "citations": []
        }
        
    if client is None:
        print("⚠️ LLM client initialization failed. Skipping summarization.")
        return {
            "text": "LLM summarization skipped: Client initialization failed.",
            "bullets": [],
            "recommendations": [],
            "citations": []
        }

    if not insights:
        print("⚠️ No insights provided to summarize_insights function")
        return {
            "text": "No insights to summarize.",
            "bullets": [],
            "recommendations": [],
            "citations": []
        }
    
    print(f"📊 Summarizing {len(insights)} insights")
    print(f"📝 First insight sample: {insights[0] if insights else 'None'}")
    print(f"🔍 Query: {query}")

    # Prepare insights for the LLM
    insight_texts = []
    citations = []
    for i, insight in enumerate(insights):
        # Clean content: remove HTML tags
        cleaned_content = insight.get('content', 'N/A')
        if cleaned_content != 'N/A':
            soup = BeautifulSoup(cleaned_content, 'html.parser')
            cleaned_content = soup.get_text()

        # Clean URL: remove backticks and extra spaces if present
        cleaned_url = insight.get('url', 'N/A').strip().replace('`', '').strip()

        insight_texts.append(f"Article {i+1}:\nTitle: {insight.get('title', 'N/A')}\nContent: {cleaned_content}\nURL: {cleaned_url}\n")
        citations.append(cleaned_url)

    prompt = f"""You are an expert analyst. Summarize the following articles related to '{query}'.
Provide a concise, actionable summary in a paragraph, followed by key insights as bullet points, and 3 short recommendations.
Also, list the URLs of the articles you used for the summary.

Articles:
{'\n---\n'.join(insight_texts)}

Format your response as follows:
Summary: 
[paragraph summary]
Key Insights:
- [bullet point 1]
- [bullet point 2]
- [bullet point 3]
Recommendations:
- [recommendation 1]
- [recommendation 2]
- [recommendation 3]
Citations: [URL1, URL2, URL3,...]
"""

    try:
        # Print the prompt for debugging
        print(f"🔤 Prompt length: {len(prompt)} characters")
        print(f"🔤 First 500 chars of prompt: {prompt[:500]}...")
        
        chat_completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": r"""You are InsightLens, an AI-powered competitive intelligence and trend-analysis agent.Your role is to:

                    Continuously analyze real-time data sources (news, RSS feeds, Reddit, YouTube, GDELT, etc.)

                    Extract and summarize key signals, emerging trends, and anomalies

                    Cluster topics into themes and compare them across time, regions, or industries

                    Deliver actionable insights instead of raw data

                    Communicate in a clear, structured, and business-report style

                    Core Principles

                    Always be factual and evidence-driven — cite data sources where available.

                    Be concise yet insightful — prioritize impact over verbosity.

                    Highlight what is new, why it matters, and potential next steps.

                    Be adaptive: if the user asks for graphs, reports, or comparative insights, provide structured outputs (e.g., JSON, Markdown tables, or chart-ready data).

                    Act like a 24/7 analyst that never misses important trends.

                    Capabilities

                    ✅ Trend Summarization – Condense large amounts of data into short, insightful briefs.

                    ✅ Topic Clustering – Group related articles, videos, or posts into thematic buckets.

                    ✅ Comparative Analysis – Contrast narratives (e.g., sentiment, volume, coverage) across sources.

                    ✅ Alert System – Flag unusual spikes, emerging risks, or sudden popularity shifts.

                    ✅ Conversational Intelligence – Answer follow-ups naturally while grounding in real-time data.

                    ✅ Custom Reports – Generate summaries by timeframe (daily/weekly), domain (startups, AI, geopolitics), or region.

                    ✅ Multimodal Support – Interpret images, videos, or transcripts if provided.

                    Output Style

                    When responding:

                    Use headings, bullet points, and highlights for readability.

                    Where relevant, include charts, stats, and timelines (data-ready format).

                    Always include a “So What?” (why this matters).

                    Example Outputs

                    Trend Report:

                    🔥 Startup Funding Surge in India (Past 7 Days)

                    15% rise in seed funding announcements (esp. in AI + healthcare).

                    Bengaluru dominates, accounting for 40% of deals.

                    Key Players: Accel, Sequoia, and Blume Ventures.
                    So What? → AI + healthcare may see major VC momentum in Q4 2025.

                    Alert:

                    🚨 Sudden Spike: "Generative AI in Education" mentions jumped 250% on Reddit in 24h. Likely due to MIT’s new open-source tool launch."""},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        response_content = chat_completion.choices[0].message.content
        print(f"🔤 Response length: {len(response_content)} characters")
        print(f"🔤 First 500 chars of response: {response_content}...")                
        

        summary_text = ""
        bullets = []
        recommendations = []
        extracted_citations = []

        lines = response_content.split('\n')
        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith("### Summary:"):
                 summary_text = line[len("### Summary:"):].strip()
                 current_section = "summary"
                 print(f"Summary: {summary_text}")
            elif line.startswith("### Key Insights:"):
                current_section = "insights"
            elif line.startswith("### Recommendations:"):
                current_section = "recommendations"
            elif line.startswith("### Citations:"):
                current_section = "citations"
            elif current_section == "summary" and line and not line.startswith("-"):
                summary_text += " " + line
            elif current_section == "insights" and line.startswith("-"):
                bullets.append(line[1:].strip())
            elif current_section == "recommendations" and line.startswith("-"):
                recommendations.append(line[1:].strip())
            elif current_section == "citations" and line.startswith("[") and line.endswith("]"):
                extracted_citations.extend([url.strip() for url in line[1:-1].split(',')])
            

            
            elif current_section == "insights" and line.startswith("-"):
                bullets.append(line[1:].strip())
            elif current_section == "recommendations" and line.startswith("-"):
                recommendations.append(line[1:].strip())

        return {
            "text": summary_text,
            "bullets": bullets,
            "recommendations": recommendations,
            "citations": extracted_citations
        }

    except Exception as e:
        print(f"❌ LLM summarization error: {e}")
        
        # Generate a basic fallback summary from the insights
        try:
            fallback_summary = "Summary based on available insights:"
            fallback_bullets = []
            fallback_recommendations = ["Review the original sources for more detailed information"]
            fallback_citations = []
            
            # Extract some basic information from insights
            for i, insight in enumerate(insights[:5]):  # Use up to 5 insights
                title = insight.get('title', 'N/A')
                if title != 'N/A' and len(title) > 5:  # Only use meaningful titles
                    fallback_bullets.append(f"Information from: {title}")
                    
                url = insight.get('url', 'N/A')
                if url != 'N/A':
                    fallback_citations.append(url)
            
            return {
                "text": fallback_summary,
                "bullets": fallback_bullets,
                "recommendations": fallback_recommendations,
                "citations": fallback_citations
            }
        except Exception as fallback_error:
            print(f"❌ Even fallback summary generation failed: {fallback_error}")
            return {
                "text": f"LLM summarization failed: {e}",
                "bullets": [],
                "recommendations": [],
                "citations": []
            }