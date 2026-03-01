import os
import requests
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER")

if not all([GEMINI_API_KEY, GITHUB_TOKEN, REPO, ISSUE_NUMBER]):
    print("Missing environment variables.")
    exit()

# 1. Get the Issue Question
headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
issue_url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}"
issue_data = requests.get(issue_url, headers=headers).json()
question = issue_data.get('body', issue_data.get('title', ''))

# 2. Build FAISS Vector Store on-the-fly
loader = TextLoader(".github/data/madhavgit_brain.md")
docs = loader.load()
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = FAISS.from_documents(docs, embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 2})
context_docs = retriever.invoke(question)
context = "\n".join([d.page_content for d in context_docs])

# 3. Query Gemini AI Studio via LangChain
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=GEMINI_API_KEY, 
    temperature=0.3
)

prompt = PromptTemplate.from_template("""
You are Madhav Kapila's GitHub Personal Assistant (PA). Answer the visitor's question based strictly on the context provided.
Madhav is an applied GenAI developer, a heavy backend engineer, and a consistent problem solver in DSA and CP.

Rules:
1. Always speak in the third person (e.g., "Madhav built...", "He is currently...").
2. Maintain a professional, highly technical, yet slightly swagger-filled aesthetic.
3. If the answer isn't in the context, confidently state that you don't have that information but they can email Madhav directly.

Context:
{context}

Visitor Question: {question}

Response:
""")
chain = prompt | llm
response = chain.invoke({"context": context, "question": question})

# 4. Post the Comment back to GitHub
comment_url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
comment_payload = {
    "body": f"🤖 **Madhav's AI PA:**\n\n{response.content}"
}
requests.post(comment_url, headers=headers, json=comment_payload)
print("Active Agent replied successfully.")