"""Four standalone agents, one self-contained package per folder
(agents/ap, agents/helpdesk, agents/support, agents/reporting). Each is built
from scratch with LangChain create_agent and shares no code with the others;
this module only collects them into a registry for the server."""

from agents.ap.agent import APAgent
from agents.helpdesk.agent import HelpdeskAgent
from agents.reporting.agent import ReportingAgent
from agents.support.agent import SupportAgent

AGENTS = {a.key: a for a in (APAgent(), HelpdeskAgent(), SupportAgent(), ReportingAgent())}
