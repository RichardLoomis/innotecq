"""Four separate agents, each its own self-contained class (own prompt, tools,
mocked backend, gateway, and LangChain loop). No shared runner."""

from agents.ap_agent import APAgent
from agents.helpdesk_agent import HelpdeskAgent
from agents.reporting_agent import ReportingAgent
from agents.support_agent import SupportAgent

AGENTS = {a.key: a for a in (APAgent(), HelpdeskAgent(), SupportAgent(), ReportingAgent())}
