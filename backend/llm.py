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
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
    else: # Default to openai
        return OpenAI(api_key=OPENAI_API_KEY)

client = get_llm_client()

def summarize_insights(query: str, insights: list, max_tokens: int = 500):
    if not (OPENAI_API_KEY or OPENROUTER_API_KEY):
        print("⚠️ LLM API key not set. Skipping summarization.")
        return {
            "text": "LLM summarization skipped: API key not configured.",
            "bullets": [],
            "recommendations": [],
            "citations": []
        }

    if not insights:
        return {
            "text": "No insights to summarize.",
            "bullets": [],
            "recommendations": [],
            "citations": []
        }

    # Prepare insights for the LLM
    insight_texts = []
    citations = []
    for i, insight in enumerate(insights):
        # Clean content: remove HTML tags
        cleaned_content = insight.get('content', 'N/A')
        if cleaned_content != 'N/A':
            soup = BeautifulSoup(cleaned_content, 'html.parser')
            cleaned_content = soup.get_text()

        # Clean URL: remove backticks if present
        cleaned_url = insight.get('url', 'N/A').replace('`', '')

        insight_texts.append(f"Article {i+1}:\nTitle: {insight.get('title', 'N/A')}\nContent: {cleaned_content}\nURL: {cleaned_url}\n")
        citations.append(cleaned_url)

    prompt = f"""You are an expert analyst. Summarize the following articles related to '{query}'.
Provide a concise, actionable summary in a paragraph, followed by key insights as bullet points, and 3 short recommendations.
Also, list the URLs of the articles you used for the summary.

Articles:
{'\n---\n'.join(insight_texts)}

Format your response as follows:
Summary: [paragraph summary]
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
        chat_completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        response_content = chat_completion.choices[0].message.content

        summary_text = ""
        bullets = []
        recommendations = []
        extracted_citations = []

        lines = response_content.split('\n')
        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith("Summary:"):
                summary_text = line[len("Summary:"):].strip()
                current_section = "summary"
            elif line.startswith("Key Insights:"):
                current_section = "insights"
            elif line.startswith("Recommendations:"):
                current_section = "recommendations"
            elif line.startswith("Citations:"):
                citations_str = line[len("Citations:"):].strip()
                extracted_citations = [url.strip() for url in citations_str.strip('[]').split(',') if url.strip()]
                current_section = "citations"
            elif current_section == "summary":
                summary_text += " " + line
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
        return {
            "text": f"LLM summarization failed: {e}",
            "bullets": [],
            "recommendations": [],
            "citations": []
        }