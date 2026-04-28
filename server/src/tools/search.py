from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")
load_dotenv()
search_tool = TavilySearchResults(max_results=4)